from sqlalchemy.orm import Session
from .models import EmailRecord, Vendor, Project, Client, VendorDraft, ProjectVersion, QuotedPrice, RFQ

def create_email_record(db: Session, email_data: dict):
    db_email = EmailRecord(
        message_id=email_data.get('id'),
        subject=email_data.get('subject'),
        sender=email_data.get('sender'),
        body=email_data.get('body'),
        provider=email_data.get('provider'),
        classification=email_data.get('classification', 'unknown'),
        requirement_category=email_data.get('requirement_category', 'General'),
        is_processed=email_data.get('is_processed', False),
        is_read=email_data.get('is_read', False),
        project_version_id=email_data.get('project_version_id')
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email

def get_emails(db: Session, skip: int = 0, limit: int = 100):
    return db.query(EmailRecord).offset(skip).limit(limit).all()

def get_vendors(db: Session):
    return db.query(Vendor).all()

def create_vendor_draft(db: Session, draft_data: dict):
    db_draft = VendorDraft(
        rfq_id=draft_data.get('rfq_id'),
        project_version_id=draft_data.get('project_version_id'),
        vendor_email=draft_data.get('recipient'),
        recipient=draft_data.get('recipient'),
        vendor_name=draft_data.get('vendor_name'),
        subject=draft_data.get('subject'),
        body=draft_data.get('body'),
        source_id=draft_data.get('source_id'),
        status="pending"
    )
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    return db_draft

def create_quoted_price(db: Session, quote_data: dict):
    db_quote = QuotedPrice(**quote_data)
    db.add(db_quote)
    db.commit()
    db.refresh(db_quote)
    return db_quote

def get_clients(db: Session):
    return db.query(Client).all()

def create_client(db: Session, name: str, email: str):
    db_client = Client(name=name, email=email)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def create_project(db: Session, name: str, client_id: int):
    db_project = Project(name=name, client_id=client_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    # Create initial version
    version = ProjectVersion(project_id=db_project.id, version_number=1)
    db.add(version)
    db.commit()
    return db_project

def get_project_lifecycle(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project: return None
    
    client = project.client
    # Get all versions for this project
    versions = db.query(ProjectVersion).filter(ProjectVersion.project_id == project_id).all()
    version_ids = [v.id for v in versions]
    
    # Get all related data across versions
    emails = db.query(EmailRecord).filter(EmailRecord.project_version_id.in_(version_ids)).all()
    # Get drafts linked either via RFQ or directly via project_version_id
    drafts = db.query(VendorDraft).filter(VendorDraft.project_version_id.in_(version_ids)).all()
    quotes = db.query(QuotedPrice).filter(QuotedPrice.project_version_id.in_(version_ids)).all()
    
    return {
        "project": project,
        "client": client,
        "emails": emails,
        "drafts": drafts,
        "vendor_responses": [e for e in emails if e.classification == "quote"],
        "comparison_data": quotes
    }
