from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..database.models import Vendor, EmailRecord, VendorDraft
from sqlalchemy import func

router = APIRouter(tags=["Dashboard"])

@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    print("DEBUG: [Router] Fetching dashboard statistics")
    total_emails = db.query(func.count(EmailRecord.id)).scalar()
    total_vendors = db.query(func.count(Vendor.id)).scalar()
    pending_drafts = db.query(func.count(VendorDraft.id)).filter(VendorDraft.status == "pending").scalar()
    sent_rfqs = db.query(func.count(VendorDraft.id)).filter(VendorDraft.status == "sent").scalar()
    
    # Recent activity mockup (can be expanded later with a real activity log table)
    recent_activity = [
        {"action": "Refactored to Modular Architecture", "time": "Just now"},
        {"action": "Syncing with AI Agents", "time": "5 mins ago"}
    ]
    
    return {
        "total_emails": total_emails or 0,
        "total_vendors": total_vendors or 0,
        "pending_drafts": pending_drafts or 0,
        "sent_rfqs": sent_rfqs or 0,
        "recent_activity": recent_activity
    }
