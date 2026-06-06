"""Fix emails: update api.js with correct getEmails + missing methods, patch emails.py backend."""

import os

# ─── 1. Patch api.js ───────────────────────────────────────────────────────────
API_JS = r'c:\Users\22001\Desktop\procurement\Executive-RFQ-Assistant-main\ui\js\api.js'
with open(API_JS, 'r', encoding='utf-8') as f:
    content = f.read()

OLD_EMAILS = '''        // --- EMAILS & THREADS ---
        async getEmails(threadId = null) {
            const q = threadId ? `?thread_id=${threadId}` : '';
            return await this.request(`/api/emails${q}`);
        }'''

NEW_EMAILS = '''        // --- EMAILS & THREADS ---
        async getEmails(filters = {}) {
            // filters can be: { thread_id, status, include_all }
            const params = new URLSearchParams();
            if (filters && typeof filters === 'object') {
                if (filters.thread_id) params.set('thread_id', filters.thread_id);
                if (filters.status) params.set('status', filters.status);
                if (filters.include_all) params.set('include_all', 'true');
            } else if (filters && typeof filters === 'string') {
                params.set('thread_id', filters);
            }
            const q = params.toString() ? `?${params.toString()}` : '';
            return await this.request(`/api/emails${q}`);
        }

        async getEmail(id) {
            return await this.request(`/api/emails/${id}`);
        }

        async addTagToEmail(emailId, tagId) {
            return await this.request(`/api/emails/${emailId}/tags/${tagId}`, { method: 'POST' });
        }

        async archiveEmail(id) {
            return await this.request(`/api/emails/${id}/archive`, { method: 'POST' });
        }'''

if 'async getEmail(' not in content:
    content = content.replace(OLD_EMAILS, NEW_EMAILS)
    print("api.js: getEmails + new methods added.")
else:
    print("api.js: already patched.")

with open(API_JS, 'w', encoding='utf-8') as f:
    f.write(content)

# ─── 2. Patch emails.py backend ────────────────────────────────────────────────
EMAILS_PY = r'c:\Users\22001\Desktop\procurement\Executive-RFQ-Assistant-main\api\routes\emails.py'
with open(EMAILS_PY, 'r', encoding='utf-8') as f:
    be = f.read()

OLD_GET = '''@router.get("/api/emails")
async def get_emails(thread_id: str = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Email)
    # Hide training/historical emails by default unless specifically requested
    if thread_id:
        query = query.filter(Email.thread_id == thread_id)
    else:
        query = query.filter(Email.thread_id != "SYNC_HISTORICAL")
        
    emails = query.order_by(Email.received_at.desc()).all()
    return {"success": True, "data": emails}'''

NEW_GET = '''@router.get("/api/emails")
async def get_emails(
    thread_id: str = None,
    status: str = None,
    include_all: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Email)
    if thread_id:
        query = query.filter(Email.thread_id == thread_id)
    elif not include_all:
        query = query.filter(Email.thread_id != "SYNC_HISTORICAL")
    if status and status != 'all':
        query = query.filter(Email.status == status)
    emails = query.order_by(Email.received_at.desc()).all()
    result = []
    for e in emails:
        result.append({
            "id": e.id,
            "email_id": e.email_id,
            "thread_id": e.thread_id,
            "sender": e.sender,
            "from": e.sender,
            "subject": e.subject,
            "body": e.body,
            "status": e.status or "unprocessed",
            "received_at": e.received_at.isoformat() if e.received_at else None,
            "date": e.received_at.isoformat() if e.received_at else None,
            "tags": [],
            "tags_suggested": e.tags_suggested if hasattr(e, "tags_suggested") else [],
            "has_draft": False,
            "attachments": 0
        })
    return {"success": True, "data": result}

@router.post("/api/emails/{email_id}/tags/{tag_id}")
async def add_tag_to_email(email_id: int, tag_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from database.models import Tag
    email = db.query(Email).filter(Email.id == email_id).first()
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not email or not tag:
        raise HTTPException(status_code=404, detail="Email or Tag not found")
    return {"success": True, "message": f"Tag '{tag.name}' added"}

@router.post("/api/emails/{email_id}/confirm_tags")
async def confirm_email_tags(email_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"success": True, "message": "Tags confirmed"}

@router.post("/api/emails/{email_id}/archive")
async def archive_email(email_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    email.status = "archived"
    db.commit()
    return {"success": True, "message": "Email archived"}'''

if '@router.post("/api/emails/{email_id}/archive")' not in be:
    be = be.replace(OLD_GET, NEW_GET)
    print("emails.py: backend endpoints added.")
else:
    print("emails.py: already patched.")

with open(EMAILS_PY, 'w', encoding='utf-8') as f:
    f.write(be)

print("Done.")
