from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..database.models import Project, ProjectVersion
from pydantic import BaseModel
from typing import List, Optional
from ..database import crud
from ..services.llm_client import LLMClient

router = APIRouter(tags=["Projects"])
llm_client = LLMClient()

class ProjectCreate(BaseModel):
    name: str
    client_id: int

class VendorResponseRequest(BaseModel):
    vendor_email: str
    subject: str
    body: str

@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    results = []
    for p in projects:
        # Find the first email (source) for this project
        from ..database.models import EmailRecord
        source_email = db.query(EmailRecord).join(ProjectVersion).filter(ProjectVersion.project_id == p.id).order_by(EmailRecord.id.asc()).first()
        
        results.append({
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "client_id": p.client_id,
            "client_formatted_id": f"CLIENT-{str(p.client_id).zfill(4)}" if p.client_id else "N/A",
            "client_name": p.client.name if p.client else "Unknown",
            "client_email": p.client.email if p.client else "N/A",
            "source_email_id": source_email.id if source_email else None
        })
    return results

@router.post("")
def create_project(req: ProjectCreate, db: Session = Depends(get_db)):
    p = crud.create_project(db, name=req.name, client_id=req.client_id)
    return {"id": p.id, "name": p.name}

@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p: return None
    return {
        "id": p.id,
        "name": p.name,
        "status": p.status,
        "client_id": p.client_id
    }

@router.post("/{project_id}/smart-drafts")
def generate_project_smart_drafts(project_id: int, db: Session = Depends(get_db)):
    from ..services.procurement_logic import ProcurementLogic
    print(f"DEBUG: [Router] Triggering smart drafts for project {project_id}")
    
    # Get latest version
    version = db.query(ProjectVersion).filter(ProjectVersion.project_id == project_id).order_by(ProjectVersion.version_number.desc()).first()
    if not version:
        raise HTTPException(status_code=404, detail="No version found for project")
        
    logic = ProcurementLogic()
    drafts = logic.generate_smart_drafts_for_version(db, version.id)
    return {"count": len(drafts), "status": "success"}

@router.get("/{project_id}/lifecycle")
def get_project_lifecycle(project_id: int, db: Session = Depends(get_db)):
    data = crud.get_project_lifecycle(db, project_id)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Manual serialization to avoid 500 circular ref errors
    return {
        "project": {
            "id": data["project"].id,
            "name": data["project"].name,
            "status": data["project"].status,
            "created_at": data["project"].created_at.isoformat() if data["project"].created_at else None
        },
        "client": {
            "id": data["client"].id if data["client"] else None,
            "name": data["client"].name if data["client"] else "Unknown",
            "email": data["client"].email if data["client"] else ""
        },
        "emails": [{
            "id": e.id,
            "subject": e.subject,
            "sender": e.sender,
            "body": e.body,
            "classification": e.classification,
            "received_at": e.received_at.isoformat() if e.received_at else None
        } for e in data["emails"]],
        "drafts": [{
            "id": d.id,
            "subject": d.subject,
            "vendor_name": d.vendor_name,
            "status": d.status,
            "body": d.body,
            "sent_at": d.sent_at.isoformat() if d.sent_at else None
        } for d in data["drafts"]],
        "vendor_responses": [{
            "id": e.id,
            "subject": e.subject,
            "sender": e.sender,
            "body": e.body,
            "received_at": e.received_at.isoformat() if e.received_at else None
        } for e in data["vendor_responses"]],
        "comparison_data": data["comparison_data"] 
    }

@router.post("/{project_id}/process-vendor-response")
async def process_vendor_response(project_id: int, req: VendorResponseRequest, db: Session = Depends(get_db)):
    # 1. Extract quotes using AI
    print(f"DEBUG: [Projects] Extracting items for project {project_id} from {req.vendor_email}")
    extracted_items = llm_client.extract_quote_from_text(req.body)
    
    # 2. Get latest project version
    version = db.query(ProjectVersion).filter(ProjectVersion.project_id == project_id).order_by(ProjectVersion.version_number.desc()).first()
    if not version:
        raise HTTPException(status_code=404, detail="No project version found")

    # 3. Save extracted quotes
    saved_quotes = []
    for item in extracted_items:
        quote_data = {
            "project_version_id": version.id,
            "vendor_email": req.vendor_email,
            "product": item.get("product"),
            "price": item.get("price"),
            "unit": item.get("unit"),
            "vendor_notes": item.get("vendor_notes")
        }
        saved_quotes.append(crud.create_quoted_price(db, quote_data))
    
    return {"status": "success", "extracted_quotes": saved_quotes}
