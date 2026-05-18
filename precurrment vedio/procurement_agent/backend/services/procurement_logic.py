from sqlalchemy.orm import Session
from ..database.models import Vendor, EmailRecord, RFQ, VendorDraft, ProjectVersion
from ..database import crud
from ..services.llm_client import LLMClient
import json

class ProcurementLogic:
    def __init__(self):
        self.llm = LLMClient()

    def generate_smart_drafts_for_version(self, db: Session, version_id: int):
        """
        Orchestrates smart draft generation:
        1. Finds all NEW_PROCUREMENT emails for this version (email must already be saved to DB!).
        2. Extracts products ONCE per email (not once per vendor).
        3. Matched vendors per category.
        4. Unique, skips duplicates.
        """
        print(f"DEBUG: [ProcurementLogic] Generating smart drafts for version {version_id}")
        
        # 1. Get relevant emails (email MUST already be committed to DB before calling this)
        emails = db.query(EmailRecord).filter(
            EmailRecord.project_version_id == version_id,
            EmailRecord.classification == "new_procurement"
        ).all()
        
        if not emails:
            print("DEBUG: [ProcurementLogic] No new_procurement emails found in DB for this version.")
            return []

        # 2. Get all approved vendors
        vendors = db.query(Vendor).filter(Vendor.is_approved == True).all()
        if not vendors:
            print("DEBUG: [ProcurementLogic] No approved vendors found. Cannot generate drafts.")
            return []
        
        results = []
        
        for email in emails:
            # --- Step A: Extract products ONCE per email ---
            print(f"DEBUG: [ProcurementLogic] Extracting products from email: {email.subject}")
            products_list = self.llm.analyze_email(email.body)
            
            if products_list:
                products_display = "\n".join([
                    f"- {p.get('product', 'Item')}: {p.get('quantity', 'N/A')}"
                    for p in products_list
                ])
            else:
                # Fallback: use first 500 chars of body as summary requirement
                products_display = email.body[:500] if email.body else "General procurement requirement"
            
            print(f"DEBUG: [ProcurementLogic] Products extracted: {products_display[:100]}...")
            
            # --- Step B: Match vendors by category ---
            category = (email.requirement_category or "General").strip()
            print(f"DEBUG: [ProcurementLogic] Matching vendors for category: '{category}'")
            
            # Strict matching for specific professional categories
            matched_vendors = [
                v for v in vendors 
                if v.category and v.category.strip().lower() == category.lower()
                and v.category.strip().title() in ["Builder", "Plumber", "Electrician"]
            ]
            
            if not matched_vendors:
                print(f"DEBUG: [ProcurementLogic] No professional category match (Builder/Plumber/Electrician) found for '{category}'. Skipping.")
                continue
            
            print(f"DEBUG: [ProcurementLogic] Matched {len(matched_vendors)} vendor(s): {[v.name for v in matched_vendors]}")
            
            # --- Step C: Generate one draft per vendor ---
            for vendor in matched_vendors:
                # Check for existing draft (avoid duplicates)
                existing = db.query(VendorDraft).filter(
                    VendorDraft.recipient == vendor.email,
                    VendorDraft.source_id == email.id
                ).first()
                if existing:
                    print(f"DEBUG: [ProcurementLogic] Draft already exists for {vendor.name} + email {email.id}. Skipping.")
                    continue

                print(f"DEBUG: [ProcurementLogic] Generating draft for vendor: {vendor.name} (Category: {category})")
                
                # Generate the draft
                draft_content = self.llm.generate_draft(vendor.name, category, products_display)
                
                # Guard against None/empty draft
                if not draft_content or not draft_content.strip():
                    print(f"WARNING: [ProcurementLogic] LLM returned empty draft for {vendor.name}. Skipping.")
                    continue
                
                # Save draft
                draft_data = {
                    "rfq_id": None,
                    "project_version_id": version_id,
                    "recipient": vendor.email,
                    "vendor_name": vendor.name,
                    "subject": f"RFQ: {email.subject[:60]}",
                    "body": draft_content,
                    "vendor_email": vendor.email,
                    "source_id": email.id
                }
                draft = crud.create_vendor_draft(db, draft_data)
                results.append(draft)
                print(f"DEBUG: [ProcurementLogic] ✅ Draft saved: ID={draft.id} for {vendor.name}")
        
        print(f"DEBUG: [ProcurementLogic] Total drafts generated: {len(results)}")
        return results
