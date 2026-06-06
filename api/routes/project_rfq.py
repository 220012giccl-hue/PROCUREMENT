"""
api/routes/project_rfq.py
Project-level RFQ KPI endpoints — for the Project Folder view in rfq.html.
ADDITIVE ONLY — new file, no existing routes modified.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from config.database import get_db
from database.models import RFQ, Topic, Contact
from pathlib import Path
import os

router = APIRouter(prefix="/api/projects", tags=["project-rfq"])

REPORTS_DIR = Path("storage/market_reports")


@router.get("/list")
async def list_projects_with_rfqs(db: Session = Depends(get_db)):
    """
    Returns all Topics (projects) that have at least one RFQ,
    with summary counts for the folder view.
    """
    try:
        # Get all RFQs grouped by project_id
        rfq_counts = (
            db.query(RFQ.project_id, func.count(RFQ.id).label("total"))
            .filter(RFQ.project_id.isnot(None))
            .group_by(RFQ.project_id)
            .all()
        )

        project_ids = [r.project_id for r in rfq_counts]
        count_map   = {r.project_id: r.total for r in rfq_counts}

        if not project_ids:
            # Also return projects from Topic table even without RFQs for reference
            topics = db.query(Topic).order_by(Topic.created_at.desc()).limit(20).all()
        else:
            topics = db.query(Topic).filter(Topic.id.in_(project_ids)).all()

        projects = []
        for t in topics:
            total = count_map.get(t.id, 0)
            # Quick KPI counts
            sent = db.query(RFQ).filter(
                RFQ.project_id == t.id,
                RFQ.status.in_(["SENT", "SUPPLIER_ACKNOWLEDGED"])
            ).count()
            quotes = db.query(RFQ).filter(
                RFQ.project_id == t.id,
                RFQ.status.in_(["RECEIVED", "UNDER_COMPARISON", "UNDER_REVIEW"])
            ).count()
            approved = db.query(RFQ).filter(
                RFQ.project_id == t.id,
                RFQ.status == "APPROVED"
            ).count()

            # Check if market report exists
            reports = _get_reports_for_ref(t.topic_reference or str(t.id))

            projects.append({
                "id": t.id,
                "project_name": t.topic_name or f"Project #{t.id}",
                "project_reference": t.topic_reference or f"PRJ-{t.id}",
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "kpis": {
                    "total": total,
                    "sent": sent,
                    "quotes_received": quotes,
                    "approved": approved
                },
                "has_report": len(reports) > 0,
                "reports": reports
            })

        return {"success": True, "data": projects}

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/{project_id}/rfqs")
async def get_project_rfqs(project_id: int, db: Session = Depends(get_db)):
    """All RFQs for a specific project (used in popup modal)."""
    try:
        rfqs = db.query(RFQ).filter(RFQ.project_id == project_id).order_by(RFQ.created_at.desc()).all()
        data = []
        for r in rfqs:
            data.append({
                "id": r.id,
                "rfq_number": r.rfq_number,
                "supplier_id": r.supplier_id,
                "quantity": r.quantity,
                "delivery_location": r.delivery_location,
                "required_delivery_date": r.required_delivery_date.isoformat() if r.required_delivery_date else None,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "technical_requirements": r.technical_requirements,
            })
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/{project_id}/kpis")
async def get_project_kpis(project_id: int, db: Session = Depends(get_db)):
    """KPI stats for a single project — used to update top KPI cards in folder view."""
    try:
        total    = db.query(RFQ).filter(RFQ.project_id == project_id).count()
        sent     = db.query(RFQ).filter(RFQ.project_id == project_id, RFQ.status.in_(["SENT","SUPPLIER_ACKNOWLEDGED"])).count()
        quotes   = db.query(RFQ).filter(RFQ.project_id == project_id, RFQ.status.in_(["RECEIVED","UNDER_COMPARISON","UNDER_REVIEW"])).count()
        approved = db.query(RFQ).filter(RFQ.project_id == project_id, RFQ.status == "APPROVED").count()

        topic = db.query(Topic).filter(Topic.id == project_id).first()
        ref   = (topic.topic_reference or str(project_id)) if topic else str(project_id)

        return {
            "success": True,
            "data": {
                "total": total,
                "sent": sent,
                "quotes_received": quotes,
                "approved": approved,
                "reports": _get_reports_for_ref(ref)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/{project_id}/reports")
async def get_project_reports(project_id: int, db: Session = Depends(get_db)):
    """List all market research report files for a project."""
    try:
        topic = db.query(Topic).filter(Topic.id == project_id).first()
        ref   = (topic.topic_reference or str(project_id)) if topic else str(project_id)
        return {"success": True, "data": _get_reports_for_ref(ref)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_reports_for_ref(project_ref: str) -> list:
    """Scan storage/market_reports/ for files matching project reference."""
    if not REPORTS_DIR.exists():
        return []
    safe_ref = project_ref.replace("/", "-").replace(" ", "_")
    files = sorted(REPORTS_DIR.glob(f"{safe_ref}_*.html"), reverse=True)
    return [
        {
            "filename": f.name,
            "url": f"/api/projects/report-file/{f.name}",
            "created": f.stat().st_mtime
        }
        for f in files
    ]


@router.get("/report-file/{filename}")
async def serve_report_file(filename: str):
    """Serve a market report HTML file directly in browser."""
    from fastapi.responses import FileResponse, JSONResponse
    # Security: strip any path traversal
    safe_name = Path(filename).name
    filepath  = REPORTS_DIR / safe_name
    if not filepath.exists():
        return JSONResponse({"error": "Report not found"}, status_code=404)
    return FileResponse(filepath, media_type="text/html")
