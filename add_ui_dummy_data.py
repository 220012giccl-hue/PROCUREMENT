import sys
import os
from datetime import datetime, timedelta
import json

# Add current dir to path to import config
sys.path.append(os.getcwd())

from database.models import Thread, Tag, Email, Attachment, ProductComparison, Topic, Contact, thread_tags
from config.database import SessionLocal

db = SessionLocal()

def seed_data():
    now = datetime.utcnow()
    
    # 1. Dummy data for "Action Required"
    # Needs a Thread with "Urgent", "Meeting Request" or "meeting_suggestion"
    action_thread = db.query(Thread).filter_by(thread_id="TND-ACTION-001").first()
    if not action_thread:
        action_thread = Thread(
            thread_id="TND-ACTION-001",
            status="ACTION_REQUIRED",
            subject="Urgent: NEOM Infrastructure Meeting Booking",
            contact_name="NEOM Procurement",
            thread_reference="NEOM-INFRA-2026",
            source="email",
            source_email="procurement@neom.com",
            source_sender="Ahmed Al-Farsi",
            meta_data={"meeting_suggestion": {"start_time": (now + timedelta(days=2)).isoformat(), "duration": 60, "location": "Teams Meeting"}}
        )
        db.add(action_thread)
        
    action_email = db.query(Email).filter_by(email_id="MSG-ACTION-001").first()
    if not action_email:
        action_email = Email(
            thread_id="TND-ACTION-001",
            email_id="MSG-ACTION-001",
            message_id="<msg-action-001@neom.com>",
            subject="Urgent: NEOM Infrastructure Meeting Booking",
            sender="procurement@neom.com",
            recipients=["bids@theline.com"],
            body="Can we schedule a meeting to discuss the infrastructure details?",
            received_at=now - timedelta(minutes=10),
            is_actionable=True,
            processed=True,
            meta_data={"meeting_suggestion": {"start_time": (now + timedelta(days=2)).isoformat(), "duration": 60, "location": "Teams Meeting", "topic": "Urgent Sync"}},
            created_at=now
        )
        db.add(action_email)
    
    # 2. Dummy data for "Strategic Project Overview" / Pulse Check
    # Needs a Thread with meta_data containing submission_deadline or location
    pulse_thread = db.query(Thread).filter_by(thread_id="TND-PULSE-001").first()
    if not pulse_thread:
        pulse_thread = Thread(
            thread_id="TND-PULSE-001",
            status="PROCESSING",
            subject="RFQ: Structural Steel Supply for The Line",
            contact_name="The Line Development",
            thread_reference="TL-STEEL-26",
            source="email",
            source_email="bids@theline.com",
            source_sender="Sara M.",
            meta_data={"submission_deadline": (now + timedelta(days=14)).isoformat(), "location": "NEOM City - The Line"}
        )
        db.add(pulse_thread)
    
    # 3. Document versions
    # Create two versions of the same document for pulse_thread
    doc_v1 = db.query(Attachment).filter_by(thread_id="TND-PULSE-001", version=1).first()
    if not doc_v1:
        doc_v1 = Attachment(
            thread_id="TND-PULSE-001",
            category="02_Scope_of_Work",
            filename="Scope_of_Work_Structural_Steel_v1.pdf",
            original_filename="Scope_of_Work_Structural_Steel.pdf",
            file_path="/tmp/fake_v1.pdf",
            file_hash="fakehash1",
            file_size_bytes=1024000,
            doc_type="PDF",
            summary="Initial scope of work, missing details on anti-corrosion coating.",
            is_correct=False,
            version=1,
            uploaded_at=now - timedelta(days=2)
        )
        db.add(doc_v1)
        
    doc_v2 = db.query(Attachment).filter_by(thread_id="TND-PULSE-001", version=2).first()
    if not doc_v2:
        doc_v2 = Attachment(
            thread_id="TND-PULSE-001",
            category="02_Scope_of_Work",
            filename="Scope_of_Work_Structural_Steel_v2.pdf",
            original_filename="Scope_of_Work_Structural_Steel.pdf",
            file_path="/tmp/fake_v2.pdf",
            file_hash="fakehash2",
            file_size_bytes=1050000,
            doc_type="PDF",
            summary="Updated scope of work, including clear specs for C5 marine grade anti-corrosion coating.",
            is_correct=True,
            version=2,
            uploaded_at=now - timedelta(hours=2)
        )
        db.add(doc_v2)

    # 4. Recent Comparison
    comparison = db.query(ProductComparison).filter_by(title="Heavy Equipment Rental Rates - Q3").first()
    if not comparison:
        comparison = ProductComparison(
            title="Heavy Equipment Rental Rates - Q3",
            category="Equipment Rental",
            products_json=[],
            comparison_table_json={
                "headers": ["Equipment", "Supplier A", "Supplier B", "Recommendation"],
                "rows": [
                    ["50t Crane", "$500/day", "$550/day", "Supplier A (10% cheaper)"],
                    ["Excavator 20t", "$300/day", "$280/day", "Supplier B (Better availability)"]
                ]
            },
            recommendation="Compared rates between top two local suppliers for NEOM base camp.",
        )
        db.add(comparison)
        
    # 5. Construction Pulse Summary
    # The get_session_summary queries Threads and Emails created between from_time and to_time.
    # We will create an email and a thread today so it shows up in 'today' preset.
    pulse2 = db.query(Thread).filter_by(thread_id="TND-RECENT-001").first()
    if not pulse2:
        pulse2 = Thread(
            thread_id="TND-RECENT-001",
            status="ACTIVE",
            subject="New Tender: Solar Panels for Base Camp",
            contact_name="Energy Solutions",
            thread_reference="ES-SOLAR-01",
            source="coveo",
            source_email="procurement@energysolutions.com",
            created_at=now - timedelta(minutes=30),
            updated_at=now
        )
        db.add(pulse2)
        
    pulse2_email = db.query(Email).filter_by(email_id="MSG-RECENT-001").first()
    if not pulse2_email:
        pulse2_email = Email(
            thread_id="TND-RECENT-001",
            email_id="MSG-RECENT-001",
            message_id="<msg-recent-001@energysolutions.com>",
            subject="New Tender: Solar Panels for Base Camp",
            sender="procurement@energysolutions.com",
            recipients=["bids@neom.com"],
            body="Please find attached the tender documents for the solar panel installation.",
            received_at=now - timedelta(minutes=30),
            is_actionable=True,
            processed=True,
            created_at=now - timedelta(minutes=30)
        )
        db.add(pulse2_email)

    db.commit()
    print("UI Dummy Data seeded successfully.")

if __name__ == "__main__":
    seed_data()
