import json
import os
from .config import VENDORS_FILE, EMAILS_FILE, DRAFTS_FILE
from .database import SessionLocal, Vendor, EmailRecord, Client, Project, ProjectVersion

def migrate_json_to_db():
    db = SessionLocal()
    try:
        # 1. Migrate Vendors
        if os.path.exists(VENDORS_FILE):
            with open(VENDORS_FILE, "r") as f:
                vendors = json.load(f)
                for v in vendors:
                    exists = db.query(Vendor).filter(Vendor.email == v['email']).first()
                    if not exists:
                        db.add(Vendor(
                            name=v['name'],
                            email=v['email'],
                            category=v['category'],
                            region=v.get('region', ""),
                            description=v.get('description', ""),
                            is_approved=True
                        ))
            db.commit()
            print("✅ Vendors migrated.")

        # 2. Migrate Emails (Legacy)
        if os.path.exists(EMAILS_FILE):
            with open(EMAILS_FILE, "r") as f:
                emails = json.load(f)
                for e in emails:
                    sender = e.get('sender') or e.get('from') or "unknown@example.com"
                    db.add(EmailRecord(
                        sender_email=sender,
                        subject=e.get('subject', 'No Subject'),
                        body=e.get('body', ''),
                        role="unknown",
                        classification="migrated"
                    ))
            db.commit()
            print("✅ Emails migrated.")

        # Note: Projects and Drafts migration is complex due to IDs, 
        # so we'll start fresh with them or handle as needed.
        
    finally:
        db.close()

if __name__ == "__main__":
    migrate_json_to_db()
