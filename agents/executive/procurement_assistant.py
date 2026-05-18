from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime
from database.models import Email, Thread, Attachment, AssistantChat, User, Contact, Supplier, PrioritySearchSource
from models.pixtral_client import PixtralClient
from typing import List, Dict, Optional
from api.utils.security import ResponseGuard

class ProcurementAssistant:
    """Answers context-aware questions about procurement, products, and suppliers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm = PixtralClient()

    def answer_query(self, query: str, conversation_id: Optional[int] = None, mode: str = 'procurement', external_context: Optional[str] = None) -> str:
        """Main entry point for procurement assistant chat"""
        
        # 1. Save User Message
        if conversation_id:
            user_msg = AssistantChat(conversation_id=conversation_id, role='user', content=query)
            self.db.add(user_msg)
            self.db.commit()

        # 2. Get User Preferences
        user = self.db.query(User).first()
        user_prefs = user.custom_instructions if user else ""

        # 3. Get Priority Search Sources
        search_sources = self.db.query(PrioritySearchSource).filter(PrioritySearchSource.is_active == True).order_by(PrioritySearchSource.priority.desc()).all()
        sources_context = ""
        if search_sources:
            sources_context = "\nPRIORITY SEARCH SOURCES (Search these first):\n" + "\n".join([f"- {s.name}: {s.url} (Priority: {s.priority}, Best For: {s.priority_for or 'General'})" for s in search_sources])

        # 4. Security Check
        if ResponseGuard.is_suspicious(query):
            return "As a professional procurement assistant, I cannot fulfill requests to bypass security protocols."

        # 4. Professional Greeting
        greetings = {'hello', 'hi', 'hey', 'greetings', 'morning', 'afternoon', 'evening', 'assalam', 'aoa', 'start'}
        clean_q = query.lower().strip().split()
        if not clean_q or (len(clean_q) <= 2 and any(w in greetings for w in clean_q)):
            return "Good day, Sir. I am your Procurement Intelligence Assistant. I am ready to help you with product research, supplier comparisons, and RFQ management. How can I assist your procurement workflow today?"

        # 5. Retrieve Context (Emails, Docs, etc.)
        context_data = self._retrieve_context(query)
        
        # Combine with external context if provided
        if external_context:
            context_data = f"[DIRECTLY UPLOADED DOCUMENT]:\n{external_context[:8000]}\n\n---\n\n[SYSTEM PROCUREMENT CONTEXT]:\n{context_data}"

        current_date_str = datetime.now().strftime("%Y-%m-%d")

        # 6. Procurement System Prompt (Phase 1 Requirements)
        system_prompt = f"""
        You are the Procurement Intelligence Assistant—an elite procurement officer specializing in construction, engineering, and infrastructure.
        
        STRICT OUTPUT STRUCTURE (You MUST follow this for every response):
        
        SECTION 1: REQUIREMENT SUMMARY
        A short paragraph describing what the user is asking for in professional procurement terms.
        
        SECTION 2: MATCHED PRODUCTS OR SUPPLIERS
        Display matched products or suppliers. (Note: For the demo, use provided context or simulate high-quality results from Blackwoods, Bunnings, or Sydney Tools if relevant).
        Format each item clearly with Name, Supplier, and Key Specs.
        
        SECTION 3: SUPPLIER COMPARISON TABLE
        A structured markdown table comparing multiple products side by side.
        Columns: Product, Supplier, Brand, Price, Best For.
        
        SECTION 4: BEST RECOMMENDATION
        A clear statement of which product/supplier is recommended and why.
        MUST INCLUDE: "Note: This is an AI recommendation only and human approval is required before purchase."
        
        SECTION 5: MISSING INFORMATION
        List what is unknown (e.g., bulk pricing, lead time, stock availability).
        
        SECTION 6: SUGGESTED NEXT ACTIONS
        List exactly these actions: [Create RFQ], [Compare Suppliers], [Draft Supplier Email], [Export PDF].
 
        SECTION 7: INTELLIGENCE BADGES
        Provide metadata for the UI badges in this exact format:
        CONFIDENCE: [High/Medium/Low]
        SOURCE: [Supplier Name or URL]
        MISSING: [Comma separated list of missing fields]
        CHECKED: {current_date_str}
        
        STRICT FORMATTING RULES:
        1. FOR TABLES (SECTION 3 ONLY): Use standard markdown table format with | and ---.
        2. FOR OTHER SECTIONS: NEVER use markdown symbols like **, ##, or ---.
        3. HEADINGS: Use PLAIN TEXT in ALL UPPERCASE (e.g., SECTION 1: REQUIREMENT SUMMARY).
        4. SPACING: Use double newlines between sections.
        
        EXECUTIVE CONTEXT:
        {user_prefs}
        {sources_context}
 
        PRODUCT CARD FORMAT (FOR SECTION 2):
        For every product, use this exact format:
        PRODUCT_START
        Name: [Product Name]
        Supplier: [Supplier Name]
        Brand: [Brand Name]
        Price: [Price or "Contact for Price"]
        Specs: [Key Technical Specifications]
        Source: [Functional Search Query URL]
        Image: [Beautiful public Unsplash image URL matching the product category]
        PRODUCT_END
        
        STRICT LINK AND IMAGE INSTRUCTIONS:
        1. SOURCE URLS: Never generate fake product IDs or detail links (e.g. ending in _p0021234 or product-detail) as they will 404 and redirect. Instead, ALWAYS generate a functional search query URL for that supplier using their real search page.
           Examples:
           - Bunnings: https://www.bunnings.com.au/search/products?q=[url_encoded_product_name]
           - Sydney Tools: https://sydneytools.com.au/search?q=[url_encoded_product_name]
           - Blackwoods: https://www.blackwoods.com.au/search?q=[url_encoded_product_name]
           - Jaycar: https://www.jaycar.com.au/search?text=[url_encoded_product_name]
           This guarantees the user will land on a live, working page on the supplier's website showing the real product!

        2. PRODUCT IMAGES: Never output "placeholder" or generic broken links. ALWAYS output a high-quality, professional, direct image URL from Unsplash using appropriate query tags.
           Examples of beautiful, functional Unsplash images to use based on product types:
           - Wheelbarrows: https://images.unsplash.com/photo-1599839620526-c5d17a6a6200?auto=format&fit=crop&w=300&q=80
           - Construction/Untreated Timber/Pine FJ: https://images.unsplash.com/photo-1589939705384-5185137a7f0f?auto=format&fit=crop&w=300&q=80
           - Power tools / Drills: https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=300&q=80
           - Safety wear / Boots: https://images.unsplash.com/photo-1582967788606-a171c1080cb0?auto=format&fit=crop&w=300&q=80
           - Hardware / Bolts: https://images.unsplash.com/photo-1530124560072-aae8d56b0efe?auto=format&fit=crop&w=300&q=80
           - General Tools/Construction site: https://images.unsplash.com/photo-1581094288338-2314dddb7ecc?auto=format&fit=crop&w=300&q=80
           If the category is different, select a professional Unsplash image that matches.
        """""

        user_prompt = f"""
        USER QUESTION: {query}

        [INTELLIGENCE CONTEXT]:
        {context_data}
        
        [TASK]:
        Provide a professional Procurement Analysis following the 6-section structure.
        If the user is asking about their emails or documents, use the provided context to answer accurately.
        """

        # 7. Call LLM
        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2
        )
        
        reply = response.get('response') or response.get('text') or response.get('answer') or "I'm sorry, Sir, I encountered an issue processing your procurement request."
        reply = ResponseGuard.sanitize(reply)

        # 8. Save Assistant Reply
        if conversation_id:
            assistant_msg = AssistantChat(conversation_id=conversation_id, role='assistant', content=reply)
            self.db.add(assistant_msg)
            self.db.commit()
            
        return reply

    def _retrieve_context(self, query: str) -> str:
        """Retrieve relevant context for procurement queries (copied and adapted from ExecutiveAssistant)"""
        import re
        from datetime import timedelta
        
        clean_query = query.lower().strip()
        now = datetime.now()
        
        # 1. Keywords for search
        STOP_WORDS = {'what', 'with', 'from', 'this', 'that', 'your', 'about', 'regarding', 'items', 'action', 'are', 'the', 'and', 'for', 'tell', 'show', 'emails', 'email'}
        keywords = [k.strip() for k in re.sub(r'[^\w\s]', '', clean_query).split() if len(k) > 2 and k.strip() not in STOP_WORDS]
        
        context_parts = []
        
        # 2. Search relevant emails (Procurement focused keywords if any)
        query_obj = self.db.query(Email)
        if not keywords:
            emails = query_obj.order_by(desc(Email.received_at)).limit(5).all()
        else:
            search_filter = or_(*[Email.subject.ilike(f"%{k}%") for k in keywords] + 
                               [Email.body.ilike(f"%{k}%") for k in keywords])
            emails = query_obj.filter(search_filter).order_by(desc(Email.received_at)).limit(15).all()

        if emails:
            context_parts.append("RELEVANT COMMUNICATION")
            for msg in emails:
                # Identify sender role (User vs Verified Supplier)
                sender_role = "UNVERIFIED"
                supplier = self.db.query(Supplier).filter(Supplier.email == msg.sender).first()
                if supplier:
                    sender_role = f"VERIFIED SUPPLIER ({supplier.name} - Category: {supplier.category})"
                elif msg.is_sent:
                    sender_role = "INTERNAL USER (YOU)"
                
                context_parts.append(f"From: {msg.sender} [Role: {sender_role}] | Date: {msg.received_at}")
                context_parts.append(f"Subject: {msg.subject}")
                context_parts.append(f"Content: {msg.body[:400] if msg.body else ''}")
                context_parts.append("-" * 15)

        # 3. Search Documents
        doc_filter = or_(*[Attachment.filename.ilike(f"%{k}%") for k in keywords] + 
                         [Attachment.summary.ilike(f"%{k}%") for k in keywords]) if keywords else None
        if doc_filter is not None:
            docs = self.db.query(Attachment).filter(doc_filter).limit(5).all()
            if docs:
                context_parts.append("\nPROCUREMENT DOCUMENTS")
                for doc in docs:
                    context_parts.append(f"File: {doc.filename} | Summary: {doc.summary[:300]}")

        if not context_parts:
            return "No specific procurement records found in the current intelligence suite."
            
        return "\n".join(context_parts)
