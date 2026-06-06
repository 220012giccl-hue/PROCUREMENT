"""
RFQ Workflow KPI State Endpoints — PRD v2.1
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import asyncio

from config.database import get_db
from database.models import RFQWorkflow, Topic, Thread, ProductResult, RFQ, SupplierQuote, User
from auth.dependencies import get_current_user
from api.tasks import run_market_research

router = APIRouter(tags=["rfq-workflow"])

class StatusUpdate(BaseModel):
    status: str
    topic_id: Optional[int] = None
    assigned_by: str = "human"

@router.get("/api/rfq-workflows")
async def list_workflows(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workflows = db.query(RFQWorkflow).all()
    return {"success": True, "data": [{"id": w.id, "status": w.status, "topic_id": w.topic_id} for w in workflows]}

@router.get("/api/rfq-workflows/triage")
async def list_triage_queue(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    triage_items = db.query(RFQWorkflow).filter(RFQWorkflow.status == "triage").all()
    results = []
    for w in triage_items:
        thread = db.query(Thread).filter(Thread.id == w.thread_id).first()
        topic = db.query(Topic).filter(Topic.id == w.topic_id).first() if w.topic_id else None
        
        results.append({
            "id": w.id,
            "thread_id": w.thread_id,
            "email_subject": thread.subject if thread else "Unknown",
            "sender": thread.source_email if thread else "Unknown",
            "received_at": thread.created_at.isoformat() if thread and thread.created_at else None,
            "best_guess_topic_id": w.topic_id,
            "best_guess_topic_name": topic.topic_name if topic else "None",
            "confidence": w.confidence_score,
        })
    return {"success": True, "data": results}

@router.get("/api/rfq-workflows/{workflow_id}")
async def get_workflow(workflow_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = db.query(RFQWorkflow).filter(RFQWorkflow.id == workflow_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    has_thread = w.thread_id is not None
    is_assigned = w.status != "triage" and w.status != "ingested"
    
    has_research = False
    has_drafts = False
    has_sent = False
    has_quotes = False
    
    if w.topic_id:
        has_research = db.query(ProductResult).filter(ProductResult.topic_id == w.topic_id).count() > 0
        has_drafts = db.query(RFQ).filter(RFQ.project_id == w.topic_id, RFQ.status == 'DRAFT').count() > 0
        has_sent = db.query(RFQ).filter(RFQ.project_id == w.topic_id, RFQ.status == 'SENT').count() > 0
        
        rfq_ids = [r.id for r in db.query(RFQ).filter(RFQ.project_id == w.topic_id).all()]
        if rfq_ids:
            has_quotes = db.query(SupplierQuote).filter(SupplierQuote.rfq_id.in_(rfq_ids)).count() > 0

    return {
        "success": True,
        "data": {
            "id": w.id,
            "status": w.status,
            "topic_id": w.topic_id,
            "steps_completed": {
                "email_received": has_thread,
                "topic_assigned": is_assigned,
                "market_research": has_research,
                "drafts_ready": has_drafts,
                "sent_to_vendors": has_sent,
                "quotes_received": has_quotes
            }
        }
    }

@router.patch("/api/rfq-workflows/{workflow_id}/status")
async def update_status(workflow_id: int, update: StatusUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = db.query(RFQWorkflow).filter(RFQWorkflow.id == workflow_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    w.status = update.status
    w.assigned_by = update.assigned_by
    if update.topic_id is not None:
        w.topic_id = update.topic_id
        
    db.commit()
    db.refresh(w)
    
    if update.status == "researching" and w.topic_id:
        asyncio.create_task(run_market_research(w.topic_id, []))
        
    return {"success": True, "data": {"id": w.id, "status": w.status}}
