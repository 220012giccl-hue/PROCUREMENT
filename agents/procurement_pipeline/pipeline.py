"""
agents/procurement_pipeline/pipeline.py
Main pipeline runner — ties CategoryExtractor, VendorDraftBuilder, MarketResearcher together.
ADDITIVE ONLY — called from api/tasks.py as a background task.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def run_procurement_pipeline(
    email_subject: str,
    email_body: str,
    sender_name: str,
    sender_email: str,
    thread_id: str,
    provider: str = "gmail",
    db=None
) -> dict:
    """
    Full pipeline:
      1. Extract products + categories from email (CategoryExtractor)
      2. Build category-split vendor drafts   (VendorDraftBuilder)
      3. Search market prices + save report   (MarketResearcher)

    Returns summary dict with all results.
    """
    logger.info(f"[Pipeline] Starting for thread: {thread_id}")
    summary = {"thread_id": thread_id, "status": "started"}

    try:
        # ── Step 1: Category Extraction ──────────────────────────────────────
        from agents.procurement_pipeline.category_extractor import CategoryExtractor
        extractor = CategoryExtractor()
        extraction = extractor.extract(email_subject, email_body, sender_name)

        if extraction.get("error") == "not_procurement":
            logger.info(f"[Pipeline] Email is not procurement — skipping. Reason: {extraction.get('reason')}")
            return {"thread_id": thread_id, "status": "skipped", "reason": extraction.get("reason")}

        project_name      = extraction.get("project_name", "Unknown Project")
        project_reference = extraction.get("project_reference", f"PRJ-{thread_id}")
        client_name       = extraction.get("client_name", sender_name)
        grouped_items     = extractor.group_by_category(extraction)

        summary["project_name"]      = project_name
        summary["project_reference"] = project_reference
        summary["categories_found"]  = list(grouped_items.keys())
        summary["total_items"]       = sum(len(v) for v in grouped_items.values())

        logger.info(f"[Pipeline] Extracted {summary['total_items']} items across {len(grouped_items)} categories")

        # ── Step 2: Vendor Drafts ────────────────────────────────────────────
        from agents.procurement_pipeline.vendor_draft_builder import VendorDraftBuilder
        builder = VendorDraftBuilder()
        draft_results = builder.build_and_save(
            project_name=project_name,
            project_reference=project_reference,
            client_name=client_name,
            grouped_items=grouped_items,
            thread_id=thread_id,
            provider=provider,
            db=db
        )
        summary["drafts_created"] = len([r for r in draft_results if r.get("status") == "draft_created"])
        summary["draft_results"]  = draft_results

        # ── Step 3: Market Research ──────────────────────────────────────────
        from agents.procurement_pipeline.market_researcher import MarketResearcher
        researcher = MarketResearcher()
        research_result = researcher.research_and_save(
            project_name=project_name,
            project_reference=project_reference,
            grouped_items=grouped_items,
            db=db
        )
        summary["report_path"]    = research_result.get("report_path")
        summary["status"]         = "completed"

        logger.info(f"[Pipeline] ✅ Complete. Drafts: {summary['drafts_created']}, Report: {summary['report_path']}")

    except Exception as e:
        logger.error(f"[Pipeline] ❌ Error: {e}", exc_info=True)
        summary["status"] = "error"
        summary["error"]  = str(e)

    return summary
