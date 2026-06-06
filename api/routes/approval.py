"""
api/routes/approval.py
Approval Summary API — PRD Implementation Plan Phase 2.4
Generates AI-powered manager approval summaries for procurement decisions.
Additive only — does not modify any existing routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from config.database import get_db
from database.models import ApprovalSummary, RFQ, ProcurementItem, Supplier, AuditLog
from typing import Dict, Optional
from datetime import datetime
import os, httpx, json, logging

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

logger = logging.getLogger(__name__)

# ── AI Helper ──────────────────────────────────────────────────────────────────

async def _call_llm(prompt: str) -> str:
    """Calls OpenRouter LLM to generate approval summary text."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return _fallback_summary_text(prompt)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://procurement-platform.internal",
    }
    payload = {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "system", "content": (
                "You are a procurement specialist. Generate a concise, professional "
                "manager approval summary in plain text (no markdown headers). "
                "Include: Item, Supplier, Reason for selection, Estimated cost, "
                "Missing information, Risk notes, and Recommended action. "
                "End with: 'AI recommendation only — human approval required before purchase.'"
            )},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 600,
        "temperature": 0.3,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"LLM call failed for approval summary: {e}")

    return _fallback_summary_text(prompt)


def _fallback_summary_text(context: str) -> str:
    """Returns a structured fallback when LLM is unavailable."""
    return (
        "PROCUREMENT APPROVAL SUMMARY\n\n"
        "This summary was generated from procurement system data.\n\n"
        "Please review the item details, supplier information, technical requirements, "
        "and confirm pricing and delivery terms directly with the supplier before issuing "
        "a purchase order.\n\n"
        "AI recommendation only — human approval required before purchase."
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/generate")
async def generate_approval_summary(
    data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Generates an AI approval summary for an RFQ or procurement item.
    POST body: { rfq_id?: int, item_id?: int, context_text?: str }
    """
    rfq_id   = data.get("rfq_id")
    item_id  = data.get("item_id")
    extra    = data.get("context_text", "")

    rfq  = db.query(RFQ).filter(RFQ.id == rfq_id).first()             if rfq_id  else None
    item = db.query(ProcurementItem).filter(ProcurementItem.id == item_id).first() if item_id else None

    # Build context for LLM
    context_parts = []
    if rfq:
        supplier_name = ""
        if rfq.supplier_id:
            sup = db.query(Supplier).filter(Supplier.id == rfq.supplier_id).first()
            supplier_name = sup.name if sup else ""
        context_parts.append(
            f"RFQ Number: {rfq.rfq_number}\n"
            f"Supplier: {supplier_name}\n"
            f"Quantity: {rfq.quantity or 'Not specified'}\n"
            f"Delivery Location: {rfq.delivery_location or 'Not specified'}\n"
            f"Required Delivery Date: {rfq.required_delivery_date.strftime('%d %b %Y') if rfq.required_delivery_date else 'Not specified'}\n"
            f"Technical Requirements: {rfq.technical_requirements or 'Not specified'}\n"
            f"Current Status: {rfq.status}"
        )

    if item:
        context_parts.append(
            f"Procurement Item: {item.item_name}\n"
            f"Category: {item.category or 'Not specified'}\n"
            f"Estimated Cost: {item.estimated_cost or 'Not specified'}\n"
            f"Technical Notes: {item.technical_notes or 'Not specified'}\n"
            f"AI Recommendation: {item.ai_recommendation or 'None recorded'}"
        )

    if extra:
        context_parts.append(f"Additional Context:\n{extra}")

    if not context_parts:
        raise HTTPException(status_code=400, detail="Provide rfq_id, item_id, or context_text")

    prompt = (
        "Generate a professional procurement approval summary for manager review "
        "based on the following information:\n\n"
        + "\n\n".join(context_parts)
    )

    summary_text = await _call_llm(prompt)

    # Persist to database
    try:
        new_summary = ApprovalSummary(
            rfq_id              = rfq_id,
            procurement_item_id = item_id,
            summary_text        = summary_text,
            recommended_action  = "Review all details and confirm with supplier before issuing PO.",
            status              = "PENDING",
        )
        db.add(new_summary)
        db.commit()
        db.refresh(new_summary)

        log = AuditLog(
            action  = "GENERATE_APPROVAL_SUMMARY",
            agent   = "PROCUREMENT_AGENT",
            details = {"summary_id": new_summary.id, "rfq_id": rfq_id, "item_id": item_id}
        )
        db.add(log)
        db.commit()

        return {
            "success": True,
            "id": new_summary.id,
            "summary": summary_text,
            "status": "PENDING"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving approval summary: {e}")
        # Still return the generated text even if DB save fails
        return {
            "success": True,
            "id": None,
            "summary": summary_text,
            "status": "PENDING"
        }


@router.get("/list")
async def list_approval_summaries(db: Session = Depends(get_db)):
    """Lists all approval summaries ordered by newest first."""
    summaries = (
        db.query(ApprovalSummary)
        .order_by(ApprovalSummary.created_at.desc())
        .limit(100)
        .all()
    )
    return {
        "success": True,
        "data": [
            {
                "id":               s.id,
                "rfq_id":           s.rfq_id,
                "procurement_item_id": s.procurement_item_id,
                "summary_text":     s.summary_text,
                "recommended_action": s.recommended_action,
                "risk_notes":       s.risk_notes,
                "missing_info":     s.missing_info,
                "status":           s.status,
                "reviewed_by":      s.reviewed_by,
                "reviewed_at":      s.reviewed_at.isoformat() if s.reviewed_at else None,
                "created_at":       s.created_at.isoformat(),
            }
            for s in summaries
        ]
    }


@router.patch("/{summary_id}/review")
async def review_approval_summary(
    summary_id: int,
    data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Human marks approval summary as APPROVED or REJECTED.
    Body: { status: 'APPROVED'|'REJECTED', reviewed_by: str }
    """
    s = db.query(ApprovalSummary).filter(ApprovalSummary.id == summary_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Approval summary not found")

    new_status  = data.get("status", "APPROVED")
    reviewed_by = data.get("reviewed_by", "Manager")

    s.status      = new_status
    s.reviewed_by = reviewed_by
    s.reviewed_at = datetime.utcnow()
    db.commit()

    log = AuditLog(
        action  = f"APPROVAL_SUMMARY_{new_status}",
        agent   = "HUMAN",
        details = {"summary_id": summary_id, "reviewed_by": reviewed_by}
    )
    db.add(log)
    db.commit()

    return {"success": True, "status": new_status}
