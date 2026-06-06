"""
agents/procurement_pipeline/vendor_draft_builder.py
Phase 2 — Category-split vendor draft emails. ADDITIVE ONLY.
"""
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class VendorDraftBuilder:
    def __init__(self):
        try:
            from agents.rfq_agent.draft_manager import DraftManager
            self.draft_manager = DraftManager()
            self._dm_ok = True
        except Exception as e:
            logger.warning(f"[VendorDraftBuilder] DraftManager unavailable: {e}")
            self._dm_ok = False

    def build_and_save(self, project_name, project_reference, client_name,
                       grouped_items, thread_id, provider="gmail", db=None):
        """
        For each category in grouped_items:
          1. Match vendors by category (existing matcher.py)
          2. Build professional draft for each vendor with ONLY that category's items
          3. Save via DraftManager (Gmail/Outlook) + save DraftReply to DB
        Returns list of result dicts.
        """
        results = []
        for category, items in grouped_items.items():
            if not items:
                continue
            vendors = self._match_vendors(category, items)
            if not vendors:
                results.append({"category": category, "status": "no_vendors"})
                continue
            for vendor in vendors:
                try:
                    r = self._create_draft(vendor, category, items,
                                           project_name, project_reference,
                                           client_name, thread_id, provider, db)
                    results.append(r)
                except Exception as e:
                    results.append({"category": category, "vendor": vendor.get("name"), "status": "error", "error": str(e)})
        return results

    def _match_vendors(self, category, items):
        try:
            from agents.vendor_matcher.matcher import match_vendors
            item_list = [{"item_name": i["item_name"], "category": category} for i in items]
            matched = match_vendors(item_list)
            seen, vendors = set(), []
            for m in matched:
                for s in m.get("matched_suppliers", []):
                    if s.get("name") and s["name"] not in seen:
                        seen.add(s["name"])
                        vendors.append(s)
            return vendors
        except Exception as e:
            logger.error(f"[VendorDraftBuilder] Vendor match error: {e}")
            return []

    def _build_body(self, vendor_name, category, items, project_name, project_reference, client_name):
        today = datetime.now().strftime("%d %B %Y")
        lines = "\n".join(f"  {i+1}. {x['item_name']} — Qty: {x.get('quantity','TBD')}" for i, x in enumerate(items))
        return f"""Dear {vendor_name} Sales Team,

We are reaching out on behalf of {client_name} for the following project:

  Project: {project_name} | Ref: {project_reference} | Date: {today}

Please provide your best pricing and availability for these {category} items:

{lines}

For each item, please include unit price (ex. GST), lead time, and minimum order quantity.
Kindly respond within 5 business days, quoting reference: {project_reference}.

Kind regards,
Procurement Team — Executive RFQ Assistant

Note: This is a Request for Quotation only. No purchase order is implied until formal approval.
"""

    def _create_draft(self, vendor, category, items, project_name, project_reference,
                      client_name, thread_id, provider, db):
        vendor_name  = vendor.get("name", "Supplier")
        vendor_email = vendor.get("email", "")
        subject = f"[RFQ] {category} Materials — {project_name} ({project_reference})"
        body    = self._build_body(vendor_name, category, items, project_name, project_reference, client_name)

        # Try email provider draft
        provider_draft_id = None
        if self._dm_ok and vendor_email:
            try:
                r = self.draft_manager.create_draft(provider=provider, to=vendor_email, subject=subject, body=body)
                if r.get("success"):
                    provider_draft_id = r.get("draft_id")
            except Exception as e:
                logger.warning(f"[VendorDraftBuilder] Provider draft failed: {e}")

        # Save to DB
        draft_db_id = None
        if db:
            try:
                from database.models import DraftReply
                rec = DraftReply(
                    thread_id=thread_id,
                    draft_type="RFQ",
                    recipient=vendor_email or vendor_name,
                    subject=subject,
                    body=body,
                    email_provider=provider,
                    provider_draft_id=provider_draft_id or f"local-{datetime.now().timestamp()}",
                    status="DRAFT",
                    created_by="PROCUREMENT_PIPELINE"
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                draft_db_id = rec.id
            except Exception as e:
                logger.error(f"[VendorDraftBuilder] DB save failed: {e}")
                try: db.rollback()
                except: pass

        return {
            "category": category,
            "vendor": vendor_name,
            "vendor_email": vendor_email,
            "subject": subject,
            "status": "draft_created",
            "provider_draft_id": provider_draft_id,
            "db_draft_id": draft_db_id
        }
