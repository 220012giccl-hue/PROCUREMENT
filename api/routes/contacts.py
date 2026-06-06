from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from database.models import Contact, User
from config.database import get_db
from auth.dependencies import get_current_user

router = APIRouter(tags=["contacts"])

@router.get("/api/contacts")
async def get_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()
    return {
        "success": True,
        "count": len(contacts),
        "data": [
            {
                "id": c.id,
                "name": c.contact_name,
                "email": c.email_domain,
                "phone": (c.meta_data or {}).get("phone"),
                "threads": len(c.threads) if c.threads else 0,
                "status": (c.meta_data or {}).get("status", "active"),
                "notes": (c.meta_data or {}).get("notes", "")
            }
            for c in contacts
        ]
    }

@router.get("/api/contacts/{contact_id}")
async def get_contact(contact_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {
        "success": True,
        "data": {
            "id": contact.id,
            "name": contact.contact_name,
            "email": contact.email_domain,
            "phone": (contact.meta_data or {}).get("phone"),
            "status": (contact.meta_data or {}).get("status", "active"),
            "notes": (contact.meta_data or {}).get("notes", ""),
            "first_seen": contact.first_seen.isoformat() if contact.first_seen else None,
            "last_contact": contact.last_contact.isoformat() if contact.last_contact else None,
            "threads": len(contact.threads) if contact.threads else 0
        }
    }

@router.post("/api/contacts")
async def add_contact(contact_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        name = (contact_data.get("name") or "").strip()
        email = (contact_data.get("email") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Contact name is required")
        if not email:
            raise HTTPException(status_code=400, detail="Email or domain is required")

        meta_data = contact_data.get("meta_data", {}) or {}
        meta_data.update({
            "phone": (contact_data.get("phone") or "").strip(),
            "status": contact_data.get("status") or "active",
            "notes": (contact_data.get("notes") or "").strip()
        })
        new_contact = Contact(
            contact_name=name,
            email_domain=email,
            meta_data=meta_data
        )
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        return {"success": True, "data": {"id": new_contact.id}}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@router.put("/api/contacts/{contact_id}")
async def update_contact(contact_id: int, contact_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    name = (contact_data.get("name") or "").strip()
    email = (contact_data.get("email") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Contact name is required")
    if not email:
        raise HTTPException(status_code=400, detail="Email or domain is required")

    meta_data = contact.meta_data or {}
    meta_data.update({
        "phone": (contact_data.get("phone") or "").strip(),
        "status": contact_data.get("status") or "active",
        "notes": (contact_data.get("notes") or "").strip()
    })
    contact.contact_name = name
    contact.email_domain = email
    contact.meta_data = meta_data
    db.commit()
    return {"success": True, "data": {"id": contact.id}}

@router.get("/api/contacts/{contact_id}/intelligence")
async def get_contact_intelligence(contact_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch intelligence data for a specific contact"""
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Fetch recent thread history for this contact
        from database.models import Thread
        recent_threads = db.query(Thread).filter(Thread.contact_id == contact_id).order_by(Thread.updated_at.desc()).limit(5).all()
        
        history = []
        for t in recent_threads:
            history.append({
                "subject": t.subject or t.topic_name or "Project Inquiry",
                "status": t.status or "active",
                "last_update": t.updated_at.isoformat() if t.updated_at else t.created_at.isoformat()
            })
            
        return {
            "success": True,
            "contact": {
                "name": contact.contact_name,
                "domain": contact.email_domain
            },
            "recent_history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- PRD v2.1 Endpoints ---

@router.get("/api/contacts/{contact_id}/topics")
async def get_contact_topics(contact_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from database.models import Topic
    topics = db.query(Topic).filter(Topic.contact_id == contact_id).all()
    return {"success": True, "data": [{"id": t.id, "topic_name": t.topic_name, "status": t.status} for t in topics]}

@router.get("/api/contacts/lookup/email")
async def lookup_contact_by_email(email: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import text
    contact = db.execute(
        text("SELECT id, contact_name FROM contacts WHERE :email = ANY(contact_emails) LIMIT 1"),
        {"email": email}
    ).fetchone()
    
    if contact:
        return {"success": True, "found": True, "data": {"contact_id": contact[0], "contact_name": contact[1]}}
    return {"success": True, "found": False}
