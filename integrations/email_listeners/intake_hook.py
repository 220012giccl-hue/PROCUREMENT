"""
Intake Hook — Glues the email listener to the context resolver and background tasks.
"""
import logging
from config.database import SessionLocal
from database.models import Thread, RFQWorkflow
from agents.context_resolver.resolver import resolve
from api.tasks import run_market_research
import asyncio

logger = logging.getLogger(__name__)

def on_email_received(sender_email: str, subject: str, body: str, thread_id: str):
    """
    Called by email listener when a new email arrives.
    """
    db = SessionLocal()
    try:
        # 1. Save to existing threads table (already exists — use existing model)
        # Check if thread exists
        thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
        if not thread:
            thread = Thread(
                thread_id=thread_id,
                subject=subject,
                source_email=sender_email,
                source_sender=sender_email,
                status="PROCESSING"
            )
            db.add(thread)
            db.commit()
            db.refresh(thread)
            
        # 2. Call context resolver
        result = resolve(sender_email, body)
        
        # 3. Create rfq_workflow record
        workflow = RFQWorkflow(
            topic_id=result.get("topic_id"),
            thread_id=thread.id,
            status=result["status"],
            confidence_score=result["confidence"],
            assigned_by="ai"
        )
        db.add(workflow)
        db.commit()
        
        # 4. Branch on result
        if result["status"] == "researching":
            # Kick off async background task — does NOT block the webhook
            parsed_items = [] # We can pass extracted items here if available
            asyncio.create_task(run_market_research(workflow.topic_id, parsed_items))
            
        elif result["status"] == "triage":
            # Do nothing automatically — wait for human assignment on triage.html
            pass
            
    except Exception as e:
        logger.error(f"[IntakeHook] Error: {e}")
        db.rollback()
    finally:
        db.close()
