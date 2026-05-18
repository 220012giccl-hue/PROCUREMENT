from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..services.mail_handler import MailHandler
from ..services.auth_handler import OAuthHandler

router = APIRouter(tags=["Emails"])
mail_handler = MailHandler()
oauth_handler = OAuthHandler()

from ..database import crud
from ..services.classification_engine import ClassificationEngine

classification_engine = ClassificationEngine()

def process_emails_background(db: Session):
    print("\nDEBUG: [Background] Starting global email fetch and classification...")
    providers = ["gmail", "outlook"]
    new_drafts_count = 0
    
    for provider in providers:
        token, email_addr = oauth_handler.get_token_details(provider)
        if not token:
            print(f"DEBUG: [Background] {provider} not connected. Skipping.")
            continue
            
        print(f"DEBUG: [Background] Fetching for {provider}: {email_addr}")
        emails = mail_handler.fetch_emails(provider, token=token, email_address=email_addr)
        
        if not emails:
            print(f"DEBUG: [Background] No new emails for {provider}")
            continue
            
        print(f"DEBUG: [Background] Processing {len(emails)} emails from {provider}...")
        
        for em in emails:
            try:
                # --- DUPLICATE CHECK: skip if already in DB ---
                from ..database.models import EmailRecord
                existing = db.query(EmailRecord).filter(
                    EmailRecord.message_id == em.get('id')
                ).first()
                if existing:
                    print(f"DEBUG: [Background] Skipping duplicate message_id: {em.get('id')}")
                    continue
                
                # Classification
                print(f"DEBUG: [Background] Classifying: {em['subject']}")
                result = classification_engine.classify_and_route(db, em['sender'], em['subject'], em['body'])
                em['classification'] = result['classification']
                em['requirement_category'] = result.get('requirement_category', 'General')
                
                print(f"DEBUG: [Background] Classified as: {em['classification']} ({em['requirement_category']})")
                
                # Logic for NEW_PROCUREMENT: Auto-create Client, Project & Mark as Read
                project_version_id = None
                if em['classification'] == "new_procurement":
                    print(f"DEBUG: [Background] *** SMART PROCUREMENT DETECTED *** Identifying project...")
                    from ..database.models import Client, Project, ProjectVersion
                    
                    # 1. Get or Create Client
                    client = db.query(Client).filter(Client.email == em['sender']).first()
                    if not client:
                        client = crud.create_client(db, name=result.get('entity_name') or em['sender'].split('@')[0], email=em['sender'])
                        print(f"DEBUG: [Background] Created new client: {client.name}")
                    
                    # 2. Identify/Create Project
                    project = None
                    is_new = result.get('is_new_project', True)
                    topic = result.get('project_topic', em['subject'])
                    
                    if not is_new:
                        # Try to find existing project for this client by topic or name
                        project = db.query(Project).filter(
                            Project.client_id == client.id,
                            (Project.name.ilike(f"%{topic}%") | Project.name.ilike(f"%{em['subject']}%"))
                        ).first()
                        if project:
                            print(f"DEBUG: [Background] Matched existing project ID={project.id}: {project.name}")
                    
                    if not project:
                        project = crud.create_project(db, name=topic, client_id=client.id)
                        print(f"DEBUG: [Background] Created new project ID={project.id}: {project.name}")
                    
                    # 3. Get latest Version ID
                    version = db.query(ProjectVersion).filter(ProjectVersion.project_id == project.id).order_by(ProjectVersion.version_number.desc()).first()
                    project_version_id = version.id if version else None

                    # Mark as Read on Server
                    try:
                        mail_handler.mark_as_read(provider, em['id'], token=token, email_address=email_addr)
                        em['is_read'] = True
                        print(f"DEBUG: [Background] Marked email as read on {provider}")
                    except Exception as mr_err:
                        print(f"WARNING: [Background] Could not mark as read: {mr_err}")
                
                em['project_version_id'] = project_version_id
                
                # Save to DB FIRST
                saved_email = crud.create_email_record(db, em)
                print(f"DEBUG: [Background] Saved email ID={saved_email.id} | {em['classification']} | {em.get('requirement_category', 'General')}")

                # Auto-Generate Smart Drafts AFTER email is saved
                if em['classification'] == "new_procurement" and project_version_id:
                    from ..services.procurement_logic import ProcurementLogic
                    logic = ProcurementLogic()
                    print(f"DEBUG: [Background] *** Triggering smart drafts for version {project_version_id} ***")
                    new_drafts = logic.generate_smart_drafts_for_version(db, project_version_id)
                    new_drafts_count += len(new_drafts)
                    print(f"DEBUG: [Background] Generated {len(new_drafts)} drafts for this email.")
                    
            except Exception as e:
                db.rollback()
                print(f"ERROR: [Background] Failed processing email '{em.get('subject', '?')}': {e}")
                import traceback
                traceback.print_exc()
    
    print(f"DEBUG: [Background] *** DONE. Total new drafts generated this run: {new_drafts_count} ***")

from pydantic import BaseModel
from typing import List, Optional

class VendorDraftRequest(BaseModel):
    vendor_name: str
    vendor_email: str
    subject: str
    body: str

@router.post("/fetch")
def trigger_email_fetch(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    print("DEBUG: [Router] Fetch triggered via API. Spawning background task.")
    background_tasks.add_task(process_emails_background, db)
    return {"status": "fetch_initiated", "message": "Email synchronization started in background"}

@router.get("")
def list_emails(
    classification: Optional[str] = None,
    query: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    from ..database.models import EmailRecord
    stmt = db.query(EmailRecord)
    if classification:
        stmt = stmt.filter(EmailRecord.classification == classification)
    if query:
        stmt = stmt.filter(EmailRecord.subject.ilike(f"%{query}%") | EmailRecord.body.ilike(f"%{query}%"))
        
    emails = stmt.order_by(EmailRecord.received_at.desc()).offset(skip).limit(limit).all()
    return emails

@router.get("/vendor-drafts")
def list_vendor_drafts(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    from ..database.models import VendorDraft
    stmt = db.query(VendorDraft)
    if status:
        stmt = stmt.filter(VendorDraft.status == status)
    drafts = stmt.order_by(VendorDraft.id.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": d.id,
            "vendor_name": d.vendor_name or d.recipient or "Unknown Vendor",
            "recipient": d.recipient or d.vendor_email or "",
            "vendor_email": d.vendor_email or d.recipient or "",
            "subject": d.subject or "",
            "body": d.body or "",
            "status": d.status or "pending",
            "source_id": d.source_id,
            "sent_at": d.sent_at.isoformat() if d.sent_at else None,
        }
        for d in drafts
    ]

@router.post("/vendor-drafts")
def create_manual_draft(req: VendorDraftRequest, db: Session = Depends(get_db)):
    from ..database.crud import create_vendor_draft
    print(f"DEBUG: [Router] Creating manual draft for {req.vendor_email}")
    draft_data = {
        "vendor_id": None, # Manual draft might not have a linked vendor ID yet
        "subject": req.subject,
        "body": req.body,
        "vendor_name": req.vendor_name,
        "recipient": req.vendor_email
    }
    draft = create_vendor_draft(db, draft_data)
    return {"id": draft.id, "status": "saved"}

@router.get("/{email_id}")
def get_email(email_id: int, db: Session = Depends(get_db)):
    from ..database.models import EmailRecord
    email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
    if not email:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@router.post("/send-draft")
def send_draft_email(draft_id: int, db: Session = Depends(get_db)):
    from ..database.models import VendorDraft
    print(f"DEBUG: [Router] Sending draft {draft_id}")
    draft = db.query(VendorDraft).filter(VendorDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Placeholder for real mail sending logic
    mail_handler.send_email(draft.recipient or "unknown@vendor.com", draft.subject, draft.body)
    draft.status = "sent"
    db.commit()
    return {"status": "success"}
