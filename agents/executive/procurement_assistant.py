from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime
from database.models import Email, Thread, Attachment, AssistantChat, User, Contact, Supplier, PrioritySearchSource
from models.pixtral_client import PixtralClient
from typing import List, Dict, Optional
from api.utils.security import ResponseGuard
from agents.executive.market_scraper import search_all_sources

class ProcurementAssistant:
    """Market Assistant for product research, supplier discovery, and market comparisons"""
    
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
            security_reply = "As a professional procurement assistant, I cannot fulfill requests to bypass security protocols."
            if conversation_id:
                assistant_msg = AssistantChat(conversation_id=conversation_id, role='assistant', content=security_reply)
                self.db.add(assistant_msg)
                self.db.commit()
            return security_reply

        # 4. Professional Greeting
        greetings = {'hello', 'hi', 'hey', 'greetings', 'morning', 'afternoon', 'evening', 'assalam', 'aoa', 'start'}
        clean_q = query.lower().strip().split()
        if not clean_q or (len(clean_q) <= 2 and any(w in greetings for w in clean_q)):
            greeting_reply = "Good day, Sir. I am your Market Assistant. I can help research products, supplier options, market comparisons, source links, missing data, and RFQ-ready market summaries."
            if conversation_id:
                assistant_msg = AssistantChat(conversation_id=conversation_id, role='assistant', content=greeting_reply)
                self.db.add(assistant_msg)
                self.db.commit()
            return greeting_reply

        conversation_context = self._get_conversation_context(conversation_id)

        # 5. Retrieve Context (Emails, Docs, etc.)
        context_data = self._retrieve_context(query)
        
        # Combine with external context if provided
        if external_context:
            context_data = f"[DIRECTLY UPLOADED DOCUMENT]:\n{external_context[:8000]}\n\n---\n\n[SYSTEM PROCUREMENT CONTEXT]:\n{context_data}"

        current_date_str = datetime.now().strftime("%Y-%m-%d")

        # 5b. Extract core search term from query for better scraping
        extraction_prompt = f"Extract the core product or material name to search for from this user query. If the query is just a single generic word (like 'road', 'pipe', 'cable', 'door', 'wood', 'steel'), return 'TOO_GENERIC'. Otherwise return ONLY the product name, nothing else. No punctuation. Query: '{query}'"
        try:
            extracted_query_resp = self.llm.generate(
                system_prompt="You are a search query extractor. Output only the exact noun phrase to search for, or 'TOO_GENERIC' if it's a single broad category word.",
                user_prompt=extraction_prompt,
                temperature=0.1
            )
            search_term = extracted_query_resp.get('response', query).strip()
            search_term = search_term.strip("'\"")
            if not search_term or len(search_term.split()) > 5:
                search_term = query
        except Exception as e:
            print(f"[ProcurementAssistant] Search extraction failed: {e}")
            search_term = query

        print(f"[ProcurementAssistant] Original Query: '{query}', Extracted Search Term: '{search_term}'")

        # 5c. LIVE MARKET SCRAPING — fetch real products from Blackwoods & Sydney Tools
        live_product_context = ""
        if search_term == "TOO_GENERIC":
            # Don't search at all — just ask user to clarify
            live_product_context = "\n[NOTE: User query was too generic. Do not show products or tables. Instead, politely ask the user to clarify exactly what type of product they need. Example: if 'road', ask: 'By road do you mean road construction materials, road marking paint, road safety barriers, or road building machinery?']\n"
        else:
            try:
                scrape_result = search_all_sources(search_term, max_per_source=3)
                products_found = scrape_result.get("products", [])
                # Only use results that have meaningful data (not generic fallback entries)
                real_products = [p for p in products_found if p.get("sku") or p.get("price", "") != "Contact for Price" or len(p.get("specs", "")) > 40]
                use_products = real_products if real_products else products_found

                if use_products:
                    src_type = scrape_result.get("source_type", "database")
                    live_product_context = "\n=== PRODUCT DATA (FROM CURATED DATABASE — USE THIS DATA EXACTLY) ===\n"
                    live_product_context += f"Search Query: {scrape_result['query']}\n"
                    live_product_context += f"Sources: {', '.join(scrape_result.get('sources', []))}\n"
                    live_product_context += f"Total Products Found: {len(use_products)}\n\n"

                    for i, p in enumerate(use_products, 1):
                        live_product_context += f"--- PRODUCT {i} ---\n"
                        live_product_context += f"Name: {p.get('name', 'N/A')}\n"
                        live_product_context += f"Supplier: {p.get('supplier', 'N/A')}\n"
                        live_product_context += f"Brand: {p.get('brand', 'N/A')}\n"
                        live_product_context += f"Price: {p.get('price', 'Contact for Price')}\n"
                        live_product_context += f"Specs: {p.get('specs', 'See website')}\n"
                        live_product_context += f"Source URL: {p.get('source', '#')}\n"
                        live_product_context += f"Image URL: {p.get('image', '')}\n"
                        live_product_context += f"SKU: {p.get('sku', '')}\n\n"

                    live_product_context += "=== END PRODUCT DATA ===\n"
                    print(f"[ProcurementAssistant] Fetched {len(use_products)} products [{src_type}] for: {query}")
                else:
                    live_product_context = "\n[NOTE: No products found in database for this query. Inform the user this product is not in our current database and suggest they contact Blackwoods directly at blackwoods.com.au]\n"
            except Exception as scrape_err:
                print(f"[ProcurementAssistant] Market search failed (non-fatal): {scrape_err}")
                live_product_context = "\n[NOTE: Product search encountered an error. Advise the user to search directly on blackwoods.com.au]\n"


        # 6. Market Assistant System Prompt
        system_prompt = f"""
        You are the Market Assistant for construction procurement research.

        ROLE BOUNDARY:
        You research product options, supplier options, market comparisons, source links, missing market data, and RFQ-ready market summaries.
        You are NOT the Procurement Assistant for internal database history. If the user asks about previous projects, last week updates, historical database prices, internal RFQs, or records stored in the system, tell them to use Procurement Assistant.

        CRITICAL INSTRUCTION — PRODUCT DATA:
        You have been provided with PRODUCT DATA from a curated database of Blackwoods (blackwoods.com.au).
        You MUST use this data in your response. Do NOT invent or hallucinate product names, prices, or URLs.
        Use the exact product names, prices, brands, specs, and source URLs provided in the PRODUCT DATA section.
        If the data has an actual price like 'AUD $XX.XX', show it prominently.
        If the data has an actual image URL, use THAT in the product card.
        Only use Unsplash fallback images if the Image URL field is empty or blank.
        
        CRITICAL RULES FOR RESPONDING (STRICTLY ENFORCED):
        1. QUERY VALIDATION: If the NOTE says the user query was too generic (like "road", "pipe", "motor"), DO NOT output the standard product format. Instead, politely ask the user to clarify what exact product they need (e.g., "By 'road', do you mean road construction materials, marking paint, or safety equipment?").
        2. SOURCE FILTERING: Only show results from Blackwoods. Ignore any other websites.
        3. IMAGE HANDLING: If images are missing from the data, explicitly say "Images not available in search results".
        
        STRICT OUTPUT STRUCTURE (You MUST follow this format if providing products. Do not use this if asking for clarification):
        
        SECTION 1: REQUIREMENT SUMMARY
        A short paragraph describing what the user is asking for in professional procurement terms.
        
        SECTION 2: MATCHED PRODUCTS OR SUPPLIERS
        Display matched products from the PRODUCT DATA.
        Use the PRODUCT_START/PRODUCT_END format below for EACH product.
        
        SECTION 3: SUPPLIER COMPARISON TABLE
        A structured markdown table comparing the products side by side.
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
        CONFIDENCE: [High/Medium/Low — High if real prices found, Medium if contact-for-price, Low if no data]
        SOURCE: [Comma-separated list of sources that returned data]
        CHECKED: {current_date_str}
        
        STRICT FORMATTING RULES:
        1. FOR TABLES (SECTION 3 ONLY): Use standard markdown table format with | and ---.
        2. FOR OTHER SECTIONS: NEVER use markdown symbols like **, ##, or ---.
        You MUST provide two main sections in your response:

        1. REQUIREMENT SUMMARY
        Briefly explain what the user is looking for and what you searched.

        2. MATCHED PRODUCTS OR SUPPLIERS
        CRITICAL: For every product from the live data, you MUST output this exact format line-by-line. 
        DO NOT use markdown tables for the products. DO NOT merge lines. You MUST include the exact tags "PRODUCT_START" and "PRODUCT_END".

        PRODUCT_START
        Name: [Exact product name from live data]
        Supplier: [Exact supplier name from live data]
        Brand: [Brand from live data]
        Price: [Exact price from live data]
        Specs: [Specs from live data]
        Source: [Exact source URL from live data]
        Image: [Exact image URL from live data]
        PRODUCT_END

        3. SUPPLIER COMPARISON TABLE
        (Optional) A markdown table summarizing the differences.

        4. BEST RECOMMENDATION
        Explain which product is best and why. SOURCE URLS: Use the exact Source URL from the PRODUCT DATA.
           If a source URL is missing, generate a search query URL:
           - Blackwoods: https://www.blackwoods.com.au/search?q=[url_encoded_product_name]
 
        2. PRODUCT IMAGES: Use the exact Image URL from the PRODUCT DATA.
        
        EXECUTIVE CONTEXT:
        {user_prefs}
        """

        user_prompt = f"""
        USER QUESTION: {query}

        [CURRENT CHAT CONTEXT]:
        {conversation_context}

        [LIVE PRODUCT DATA FROM SUPPLIER WEBSITES]:
        {live_product_context}

        [ADDITIONAL INTELLIGENCE CONTEXT]:
        {context_data}
        
        [TASK]:
        Provide a professional Market Assistant response following the 7-section structure.
        You MUST use the LIVE PRODUCT DATA above — do not invent products. Show real names, real prices, real URLs, and real images from the scraped data.
        If the user asks about internal emails, documents, previous projects, historical database prices, or saved RFQs, redirect them to Procurement Assistant.
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

    def _get_conversation_context(self, conversation_id: Optional[int]) -> str:
        if not conversation_id:
            return "No previous messages in this chat."

        messages = (
            self.db.query(AssistantChat)
            .filter(AssistantChat.conversation_id == conversation_id)
            .order_by(AssistantChat.timestamp.desc())
            .limit(10)
            .all()
        )
        if not messages:
            return "No previous messages in this chat."

        ordered = list(reversed(messages))
        return "\n".join([f"{m.role.upper()}: {(m.content or '')[:700]}" for m in ordered])

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
