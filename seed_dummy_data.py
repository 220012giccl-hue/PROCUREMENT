import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from config.database import SessionLocal
from database.models import Thread, Contact, Topic, Attachment, Email, ProductComparison

def seed_data():
    db = SessionLocal()
    
    # 1. Create a dummy Contact and Topic if not exist
    contact = db.query(Contact).first()
    if not contact:
        contact = Contact(contact_name="Saudi Aramco", email_domain="aramco.com", contact_emails=["procurement@aramco.com"])
        db.add(contact)
        db.commit()
        db.refresh(contact)

    topic = db.query(Topic).first()
    if not topic:
        topic = Topic(contact_id=contact.id, topic_name="NEOM Steel Supply Phase 2", thread_id="TOPIC-001")
        db.add(topic)
        db.commit()
        db.refresh(topic)

    # 2. Action Required (Meeting Suggestion)
    meeting_thread = db.query(Thread).filter_by(thread_id="THR-SA-2026-0004").first()
    if not meeting_thread:
        meeting_thread = Thread(
            thread_id="THR-SA-2026-0004",
            contact_id=contact.id,
            topic_id=topic.id,
            subject="Urgent: Clarification on BOQ items for Structural Steel",
            contact_name=contact.contact_name,
            topic_name=topic.topic_name,
            status="ACTION_REQUIRED",
            source="gmail",
            meta_data={}
        )
        db.add(meeting_thread)
    
    # Create the Email for this thread which holds the meeting suggestion
    meeting_email = db.query(Email).filter_by(thread_id="THR-SA-2026-0004").first()
    if not meeting_email:
        meeting_email = Email(
            thread_id="THR-SA-2026-0004",
            email_id="meeting_email_123",
            subject="Urgent: Clarification on BOQ items for Structural Steel",
            sender="procurement@aramco.com",
            recipients=["you@company.com"],
            body="We need a meeting to clarify the BOQ items.",
            received_at=datetime.utcnow(),
            processed=True,
            meta_data={
                "meeting_suggestion": {
                    "topic": "Clarification Meeting: BOQ Items",
                    "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    "is_booked": False
                }
            }
        )
        db.add(meeting_email)
    else:
        meeting_email.processed = True
        meeting_email.received_at = datetime.utcnow()
        meeting_email.meta_data = {
            **(meeting_email.meta_data or {}),
            "meeting_suggestion": {
                "topic": "Clarification Meeting: BOQ Items",
                "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "is_booked": False
            }
        }

    # 3. Strategic Project Overview
    project_thread = db.query(Thread).filter_by(thread_id="THR-SA-2026-0005").first()
    if not project_thread:
        project_thread = Thread(
            thread_id="THR-SA-2026-0005",
            contact_id=contact.id,
            topic_id=topic.id,
            subject="AlFursan Residential Complex - Concrete Supply",
            contact_name=contact.contact_name,
            topic_name=topic.topic_name,
            status="PROCESSING",
            source="gmail",
            meta_data={
                "submission_deadline": (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d"),
                "location": "Riyadh, Saudi Arabia"
            }
        )
        db.add(project_thread)
    else:
        project_thread.meta_data = {
            **(project_thread.meta_data or {}),
            "submission_deadline": (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "location": "Riyadh, Saudi Arabia"
        }

    # 3.5 Recent Comparisons
    comp = db.query(ProductComparison).filter_by(title="Concrete Mix Grade Comparison").first()
    if not comp:
        comp = ProductComparison(
            title="Concrete Mix Grade Comparison",
            category="Raw Materials",
            confidence_level="HIGH",
            created_at=datetime.utcnow(),
            products_json=["C30 Ready Mix", "C40 Ready Mix"],
            comparison_table_json=[{"feature": "Strength", "C30": "30 MPa", "C40": "40 MPa"}],
            recommendation="Use C40 for foundational structures.",
            missing_info_json=[]
        )
        db.add(comp)

    # 4. Document Versioning
    # Adding a v1 and v2 document for a thread
    doc_thread_id = "THR-SA-2026-0005"
    
    # Check if we already have V1
    doc_v1 = db.query(Attachment).filter_by(filename="AlFursan_ReadyMixConcrete_BOQ_v1.xlsx", version=1).first()
    if not doc_v1:
        doc_v1 = Attachment(
            thread_id=doc_thread_id,
            email_id="dummy_email_1",
            category="BOQ",
            filename="AlFursan_ReadyMixConcrete_BOQ_v1.xlsx",
            original_filename="AlFursan_ReadyMixConcrete_BOQ_v1.xlsx",
            file_path="/documents/AlFursan_ReadyMixConcrete_BOQ_v1.xlsx",
            file_hash="hash_v1",
            file_size_bytes=2640000,
            doc_type="Excel",
            summary="Original BOQ with unclear specifications on compressive strength.",
            is_correct=False,
            version=1
        )
        db.add(doc_v1)

    # Add V2 (Correction)
    doc_v2 = db.query(Attachment).filter_by(filename="AlFursan_ReadyMixConcrete_BOQ_v2.xlsx", version=2).first()
    if not doc_v2:
        doc_v2 = Attachment(
            thread_id=doc_thread_id,
            email_id="dummy_email_2",
            category="BOQ",
            filename="AlFursan_ReadyMixConcrete_BOQ_v2.xlsx",
            original_filename="AlFursan_ReadyMixConcrete_BOQ_v2.xlsx",
            file_path="/documents/AlFursan_ReadyMixConcrete_BOQ_v2.xlsx",
            file_hash="hash_v2",
            file_size_bytes=2700000,
            doc_type="Excel",
            summary="Updated BOQ with clarified compressive strength requirements (C40).",
            is_correct=True,
            version=2
        )
        db.add(doc_v2)

    db.commit()
    print("Database successfully seeded with dummy data for UI testing!")

if __name__ == "__main__":
    seed_data()
