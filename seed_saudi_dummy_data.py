"""
=============================================================
  SAUDI GOVERNMENT - PROCUREMENT DUMMY DATA SEED SCRIPT
=============================================================
  Yeh script sirf database mein dummy data insert karta hai.
  Koi bhi existing file change NAHI hoti.
  
  Run karo:  python seed_saudi_dummy_data.py
=============================================================
"""

import sys
import os
# Fix Windows console Unicode issue
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
import random
import hashlib
import uuid

from config.database import SessionLocal, init_db
from database.models import (
    Contact, Topic, Tag, Thread, Email, Attachment,
    DraftReply, FollowupTask, Supplier, ProcurementItem,
    RFQ, SupplierQuote, ProductComparison, PrioritySearchSource,
    RFQWorkflow, ProductResult, ApprovalSummary, AssistantConversation, AssistantChat,
    AuditLog, User
)
from auth.security import get_password_hash

print("=" * 60)
print("  Saudi Government - Procurement Dummy Data Seeder")
print("=" * 60)

# Initialize database tables
init_db()
db = SessionLocal()

def rand_date(days_back=90, days_forward=30):
    """Random date within range"""
    offset = random.randint(-days_back, days_forward)
    return datetime.utcnow() + timedelta(days=offset)

def rand_past(days_back=60):
    return datetime.utcnow() - timedelta(days=random.randint(1, days_back))

def rand_future(days_forward=60):
    return datetime.utcnow() + timedelta(days=random.randint(1, days_forward))

try:
    # ─────────────────────────────────────────────────
    # 1. TAGS
    # ─────────────────────────────────────────────────
    print("\n[1/12] Seeding Tags...")
    tag_data = [
        ("URGENT", "#ef4444"),
        ("INFRASTRUCTURE", "#f97316"),
        ("VISION_2030", "#8b5cf6"),
        ("NEOM", "#06b6d4"),
        ("AWAITING_RESPONSE", "#f59e0b"),
        ("HIGH_VALUE", "#10b981"),
        ("GIGA_PROJECT", "#ec4899"),
        ("MINISTRY_OF_HOUSING", "#3b82f6"),
        ("CONSTRUCTION", "#84cc16"),
        ("IT_TECHNOLOGY", "#6366f1"),
    ]
    tags_created = {}
    for name, color in tag_data:
        existing = db.query(Tag).filter(Tag.name == name).first()
        if not existing:
            tag = Tag(name=name, color=color)
            db.add(tag)
            db.flush()
            tags_created[name] = tag
        else:
            tags_created[name] = existing
    db.commit()
    print(f"   ✅ {len(tag_data)} Tags ready")

    # ─────────────────────────────────────────────────
    # 2. CONTACTS (Saudi Government Entities)
    # ─────────────────────────────────────────────────
    print("\n[2/12] Seeding Contacts...")
    contacts_data = [
        {
            "contact_name": "وزارة الإسكان - Ministry of Housing",
            "email_domain": "housing.gov.sa",
            "contact_emails": ["procurement@housing.gov.sa", "tenders@housing.gov.sa"],
            "total_interactions": 24,
        },
        {
            "contact_name": "NEOM Company - نيوم",
            "email_domain": "neom.com",
            "contact_emails": ["rfq@neom.com", "construction@neom.com"],
            "total_interactions": 38,
        },
        {
            "contact_name": "Saudi Aramco - أرامكو السعودية",
            "email_domain": "aramco.com",
            "contact_emails": ["procurement@aramco.com", "supply@aramco.com"],
            "total_interactions": 56,
        },
        {
            "contact_name": "وزارة النقل - Ministry of Transport",
            "email_domain": "mot.gov.sa",
            "contact_emails": ["tenders@mot.gov.sa"],
            "total_interactions": 15,
        },
        {
            "contact_name": "ROSHN Real Estate - روشن",
            "email_domain": "roshn.sa",
            "contact_emails": ["projects@roshn.sa", "procurement@roshn.sa"],
            "total_interactions": 20,
        },
        {
            "contact_name": "Saudi Vision 2030 Office",
            "email_domain": "vision2030.gov.sa",
            "contact_emails": ["giga@vision2030.gov.sa"],
            "total_interactions": 9,
        },
        {
            "contact_name": "SABIC - سابك",
            "email_domain": "sabic.com",
            "contact_emails": ["procurement@sabic.com", "supply.chain@sabic.com"],
            "total_interactions": 33,
        },
        {
            "contact_name": "Royal Commission for AlUla",
            "email_domain": "rcu.gov.sa",
            "contact_emails": ["tenders@rcu.gov.sa"],
            "total_interactions": 11,
        },
    ]
    contacts_created = []
    for c in contacts_data:
        existing = db.query(Contact).filter(Contact.email_domain == c["email_domain"]).first()
        if not existing:
            contact = Contact(
                contact_name=c["contact_name"],
                email_domain=c["email_domain"],
                contact_emails=c["contact_emails"],
                total_interactions=c["total_interactions"],
                first_seen=rand_past(180),
                last_contact=rand_past(7),
            )
            db.add(contact)
            db.flush()
            contacts_created.append(contact)
        else:
            contacts_created.append(existing)
    db.commit()
    print(f"   ✅ {len(contacts_created)} Contacts ready")

    # ─────────────────────────────────────────────────
    # 3. TOPICS (Projects)
    # ─────────────────────────────────────────────────
    print("\n[3/12] Seeding Topics/Projects...")
    topics_data = [
        {"name": "NEOM The Line - Facade Materials RFQ", "ref": "NEOM-2026-FL-001", "contact_idx": 1, "status": "ACTIVE"},
        {"name": "Ministry of Housing - Al Fursan Community Infrastructure", "ref": "MOH-2026-AF-002", "contact_idx": 0, "status": "ACTIVE"},
        {"name": "Saudi Aramco - Ras Tanura Refinery Expansion", "ref": "SAR-2026-RT-003", "contact_idx": 2, "status": "ACTIVE"},
        {"name": "ROSHN - Sedra District Phase 3 Construction", "ref": "RSH-2026-SD-004", "contact_idx": 4, "status": "ACTIVE"},
        {"name": "AlUla Heritage Village - Tourism Infrastructure", "ref": "RCU-2026-HV-005", "contact_idx": 7, "status": "ACTIVE"},
        {"name": "Ministry of Transport - Riyadh Metro Line 6 Extension", "ref": "MOT-2026-RM-006", "contact_idx": 3, "status": "AWAITING_DOCS"},
        {"name": "SABIC - Jubail Petrochemical Complex Upgrade", "ref": "SAB-2026-JP-007", "contact_idx": 6, "status": "ACTIVE"},
        {"name": "NEOM Sindalah Island - Marine Infrastructure", "ref": "NEOM-2026-SI-008", "contact_idx": 1, "status": "ACTIVE"},
    ]
    topics_created = []
    for t in topics_data:
        existing = db.query(Topic).filter(Topic.topic_reference == t["ref"]).first()
        if not existing:
            topic = Topic(
                contact_id=contacts_created[t["contact_idx"]].id,
                topic_name=t["name"],
                topic_reference=t["ref"],
                thread_id=f"TOPIC-{t['ref']}",
                status=t["status"],
                folder_path=f"./storage/{t['ref']}",
                created_at=rand_past(60),
            )
            db.add(topic)
            db.flush()
            topics_created.append(topic)
        else:
            topics_created.append(existing)
    db.commit()
    print(f"   ✅ {len(topics_created)} Topics ready")

    # ─────────────────────────────────────────────────
    # 4. THREADS (Tenders)
    # ─────────────────────────────────────────────────
    print("\n[4/12] Seeding Threads/Tenders...")
    thread_data = [
        {
            "subject": "RFQ: Structural Steel Supply - NEOM The Line Phase 1",
            "contact_name": "NEOM Company - نيوم",
            "status": "ACTIVE",
            "source": "outlook",
            "topic_idx": 0,
            "contact_idx": 1,
        },
        {
            "subject": "Tender: Ready-Mix Concrete - Al Fursan District",
            "contact_name": "وزارة الإسكان - Ministry of Housing",
            "status": "AWAITING_DOCS",
            "source": "gmail",
            "topic_idx": 1,
            "contact_idx": 0,
        },
        {
            "subject": "RFQ: Industrial Pipe Fittings - Ras Tanura Expansion",
            "contact_name": "Saudi Aramco - أرامكو السعودية",
            "status": "URGENT",
            "source": "outlook",
            "topic_idx": 2,
            "contact_idx": 2,
        },
        {
            "subject": "Procurement: Precast Concrete Panels - Sedra District Phase 3",
            "contact_name": "ROSHN Real Estate - روشن",
            "status": "ACTIVE",
            "source": "gmail",
            "topic_idx": 3,
            "contact_idx": 4,
        },
        {
            "subject": "Supply: Heritage Stone & Limestone Cladding - AlUla Village",
            "contact_name": "Royal Commission for AlUla",
            "status": "ACTIVE",
            "source": "outlook",
            "topic_idx": 4,
            "contact_idx": 7,
        },
        {
            "subject": "RFQ: Electrical Cable Trays - Metro Line 6 Extension",
            "contact_name": "وزارة النقل - Ministry of Transport",
            "status": "AWAITING_DOCS",
            "source": "gmail",
            "topic_idx": 5,
            "contact_idx": 3,
        },
        {
            "subject": "Tender: High-Pressure Valve Systems - Jubail Petrochemical",
            "contact_name": "SABIC - سابك",
            "status": "ACTIVE",
            "source": "outlook",
            "topic_idx": 6,
            "contact_idx": 6,
        },
        {
            "subject": "RFQ: Marine Piling Materials - Sindalah Island",
            "contact_name": "NEOM Company - نيوم",
            "status": "URGENT",
            "source": "gmail",
            "topic_idx": 7,
            "contact_idx": 1,
        },
        {
            "subject": "Clarification: BOQ Review - NEOM The Line",
            "contact_name": "NEOM Company - نيوم",
            "status": "ACTIVE",
            "source": "outlook",
            "topic_idx": 0,
            "contact_idx": 1,
        },
        {
            "subject": "Supplier Pre-Qualification - ARAMCO Framework Agreement",
            "contact_name": "Saudi Aramco - أرامكو السعودية",
            "status": "ACTIVE",
            "source": "outlook",
            "topic_idx": 2,
            "contact_idx": 2,
        },
        {
            "subject": "RFI: Safety Equipment Standards - Vision 2030 Projects",
            "contact_name": "Saudi Vision 2030 Office",
            "status": "AWAITING_DOCS",
            "source": "gmail",
            "topic_idx": 0,
            "contact_idx": 5,
        },
        {
            "subject": "Tender: HVAC Systems for ROSHN Residential Towers",
            "contact_name": "ROSHN Real Estate - روشن",
            "status": "ACTIVE",
            "source": "gmail",
            "topic_idx": 3,
            "contact_idx": 4,
        },
    ]
    threads_created = []
    for i, t in enumerate(thread_data):
        thread_id = f"THR-SA-{2026}-{str(i+1).zfill(4)}"
        existing = db.query(Thread).filter(Thread.thread_id == thread_id).first()
        if not existing:
            thread = Thread(
                thread_id=thread_id,
                subject=t["subject"],
                contact_name=t["contact_name"],
                topic_name=topics_created[t["topic_idx"]].topic_name,
                thread_reference=f"REF-{thread_id}",
                status=t["status"],
                source=t["source"],
                source_email=contacts_created[t["contact_idx"]].contact_emails[0],
                source_sender=t["contact_name"],
                contact_id=contacts_created[t["contact_idx"]].id,
                topic_id=topics_created[t["topic_idx"]].id,
                created_at=rand_past(45),
                updated_at=rand_past(5),
            )
            db.add(thread)
            db.flush()
            threads_created.append(thread)
        else:
            threads_created.append(existing)
    db.commit()
    print(f"   ✅ {len(threads_created)} Threads ready")

    # ─────────────────────────────────────────────────
    # 5. EMAILS
    # ─────────────────────────────────────────────────
    print("\n[5/12] Seeding Emails...")
    email_subjects = [
        ("Structural Steel Supply - Technical Specifications", "procurement@neom.com"),
        ("Re: Ready-Mix Concrete BOQ Attachment", "tenders@housing.gov.sa"),
        ("URGENT: Pipe Fittings Delivery Schedule Confirmation", "supply@aramco.com"),
        ("Precast Panel Submission - Drawing Set A", "projects@roshn.sa"),
        ("Heritage Stone Samples - Lab Test Results", "tenders@rcu.gov.sa"),
        ("Electrical Cable Tray Catalog - Metro L6", "tenders@mot.gov.sa"),
        ("High-Pressure Valve Compliance Certificate", "procurement@sabic.com"),
        ("Marine Piling - Environmental Impact Assessment", "construction@neom.com"),
        ("NEOM The Line: Revised BOQ v2.3", "rfq@neom.com"),
        ("Framework Agreement Draft - ARAMCO 2026", "procurement@aramco.com"),
        ("Safety Equipment: SASO Standard Compliance", "giga@vision2030.gov.sa"),
        ("HVAC System Load Calculation Report - ROSHN", "procurement@roshn.sa"),
        ("Follow-up: Steel Supply Lead Time Query", "rfq@neom.com"),
        ("Supplier Registration Form - Vendor Portal", "supply.chain@sabic.com"),
        ("Meeting Invitation: Bid Clarification Session - 2026-08-15", "construction@neom.com"),
    ]
    emails_created = []
    for i, (subj, sender) in enumerate(email_subjects):
        t = threads_created[i % len(threads_created)]
        email_id = f"EMAIL-SA-{uuid.uuid4().hex[:12].upper()}"
        existing = db.query(Email).filter(Email.email_id == email_id).first()
        if not existing:
            email = Email(
                thread_id=t.thread_id,
                email_id=email_id,
                message_id=f"<{email_id}@procurement.sa>",
                subject=subj,
                sender=sender,
                recipients=["procurement@globalaigroup.online"],
                body=f"Dear Procurement Team,\n\nPlease find attached the required documents for {subj}.\n\nThis is in reference to our ongoing project under Vision 2030 initiative. We kindly request your prompt review and confirmation.\n\nBest Regards,\nSaudi Government Procurement Office",
                received_at=rand_past(30),
                is_actionable=True,
                is_junk=False,
                is_sent=False,
                processed=random.choice([True, True, False]),
                detection_confidence=round(random.uniform(0.75, 0.98), 2),
            )
            db.add(email)
            db.flush()
            emails_created.append(email)
    db.commit()
    print(f"   ✅ {len(emails_created)} Emails ready")

    # ─────────────────────────────────────────────────
    # 6. ATTACHMENTS
    # ─────────────────────────────────────────────────
    print("\n[6/12] Seeding Attachments...")
    attachment_data = [
        ("NEOM_TheLinePhase1_StructuralSteel_Specs.pdf", "04_Specifications", "PDF", "THR-SA-2026-0001"),
        ("AlFursan_ReadyMixConcrete_BOQ_v1.xlsx", "05_BOQ", "Excel", "THR-SA-2026-0002"),
        ("ARAMCO_PipeFittings_Instructions.pdf", "01_Instructions", "PDF", "THR-SA-2026-0003"),
        ("Sedra_Phase3_PrecastPanels_Drawings.dwg", "03_Drawings", "DWG", "THR-SA-2026-0004"),
        ("AlUla_HeritageStoneCladding_Scope.pdf", "02_Scope_of_Work", "PDF", "THR-SA-2026-0005"),
        ("MetroL6_ElectricalCableTray_Specs.pdf", "04_Specifications", "PDF", "THR-SA-2026-0006"),
        ("Jubail_ValveSystem_SBC_Standard.pdf", "06_Standards", "PDF", "THR-SA-2026-0007"),
        ("Sindalah_MarinePiling_Terms.pdf", "07_Commercial", "PDF", "THR-SA-2026-0008"),
        ("NEOM_TheLinePhase1_BOQ_v2.3.xlsx", "05_BOQ", "Excel", "THR-SA-2026-0009"),
        ("ARAMCO_FrameworkAgreement_2026.pdf", "07_Commercial", "PDF", "THR-SA-2026-0010"),
        ("Vision2030_SafetyEquipment_SASO_Cert.pdf", "06_Standards", "PDF", "THR-SA-2026-0011"),
        ("ROSHN_HVAC_LoadCalc_Report.pdf", "04_Specifications", "PDF", "THR-SA-2026-0012"),
        ("NEOM_SteelSupply_Instructions_v1.pdf", "01_Instructions", "PDF", "THR-SA-2026-0001"),
        ("SABIC_VendorRegistration_Form.pdf", "01_Instructions", "PDF", "THR-SA-2026-0007"),
        ("Sindalah_MarinePiling_EnvImpact.pdf", "02_Scope_of_Work", "PDF", "THR-SA-2026-0008"),
    ]
    for fname, category, doc_type, thread_id in attachment_data:
        fake_hash = hashlib.md5(fname.encode()).hexdigest()
        existing = db.query(Attachment).filter(Attachment.file_hash == fake_hash).first()
        if not existing:
            att = Attachment(
                thread_id=thread_id,
                email_id=f"EMAIL-SA-{fake_hash[:12].upper()}",
                category=category,
                filename=fname,
                original_filename=fname,
                file_path=f"./storage/{thread_id}/{category}/{fname}",
                file_hash=fake_hash,
                file_size_bytes=random.randint(150000, 5000000),
                doc_type=doc_type,
                summary=f"Document contains technical requirements and specifications related to {fname.replace('_', ' ').replace('.pdf','').replace('.xlsx','')}. Reviewed by AI with high confidence.",
                is_correct=True,
                version=1,
                source="email",
            )
            db.add(att)
    db.commit()
    print(f"   ✅ {len(attachment_data)} Attachments ready")

    # ─────────────────────────────────────────────────
    # 7. SUPPLIERS
    # ─────────────────────────────────────────────────
    print("\n[7/12] Seeding Suppliers...")
    suppliers_data = [
        {
            "name": "Al-Rajhi Steel Company - شركة الراجحي للصلب",
            "contact_person": "Eng. Mohammed Al-Rajhi",
            "email": "sales@alrajhisteel.com.sa",
            "phone": "+966-11-4567890",
            "website": "https://www.alrajhisteel.com.sa",
            "categories": "Structural Steel, Rebar, Steel Plates",
            "location": "Riyadh, Saudi Arabia",
            "rating": 4.8,
            "preferred_supplier": True,
            "notes": "ISO 9001:2015 certified. Preferred supplier for Vision 2030 mega projects.",
        },
        {
            "name": "Saudi Readymix Concrete Company",
            "contact_person": "Eng. Khalid Al-Dosari",
            "email": "procurement@srmcc.com.sa",
            "phone": "+966-13-8901234",
            "website": "https://www.srmcc.com.sa",
            "categories": "Ready-Mix Concrete, Precast Panels, Cement",
            "location": "Dammam, Saudi Arabia",
            "rating": 4.6,
            "preferred_supplier": True,
            "notes": "ARAMCO-approved vendor. Specializes in high-performance concrete mixes.",
        },
        {
            "name": "Gulf Pipes & Fittings Co. - خليج للأنابيب",
            "contact_person": "Eng. Abdullah Al-Shammari",
            "email": "rfq@gulfpipes.sa",
            "phone": "+966-13-3456789",
            "website": "https://www.gulfpipes.sa",
            "categories": "Industrial Pipes, Valves, Fittings",
            "location": "Jubail, Saudi Arabia",
            "rating": 4.5,
            "preferred_supplier": False,
            "notes": "SABIC and ARAMCO approved. API 5L certified piping systems.",
        },
        {
            "name": "Al-Bawani Construction Materials",
            "contact_person": "Mr. Saud Al-Bawani",
            "email": "supply@albawani.com.sa",
            "phone": "+966-11-2345678",
            "website": "https://www.albawani.com.sa",
            "categories": "Construction Materials, Precast, Insulation",
            "location": "Riyadh, Saudi Arabia",
            "rating": 4.3,
            "preferred_supplier": True,
            "notes": "National supplier with over 20 years in Saudi infrastructure projects.",
        },
        {
            "name": "Siemens Saudi Arabia - سيمنز",
            "contact_person": "Mr. Ahmed Riaz",
            "email": "procurement.sa@siemens.com",
            "phone": "+966-11-5678901",
            "website": "https://www.siemens.com/sa",
            "categories": "Electrical Systems, HVAC, Smart Building Technology",
            "location": "Riyadh, Saudi Arabia",
            "rating": 4.9,
            "preferred_supplier": True,
            "notes": "Preferred for all electrical and smart systems integration in NEOM.",
        },
        {
            "name": "Saudi Cable Company - شركة الكابلات السعودية",
            "contact_person": "Eng. Fahad Al-Otaibi",
            "email": "sales@scc.com.sa",
            "phone": "+966-12-6789012",
            "website": "https://www.scc.com.sa",
            "categories": "Electrical Cables, Cable Trays, Fiber Optic",
            "location": "Jeddah, Saudi Arabia",
            "rating": 4.7,
            "preferred_supplier": True,
            "notes": "Saudi Aramco and Saudi Electricity Company approved vendor.",
        },
        {
            "name": "National Marine Dredging Company",
            "contact_person": "Capt. Yousef Al-Mutlaq",
            "email": "rfq@nmdc.ae",
            "phone": "+971-2-6677889",
            "website": "https://www.nmdc.ae",
            "categories": "Marine Construction, Dredging, Offshore Piling",
            "location": "Abu Dhabi, UAE",
            "rating": 4.6,
            "preferred_supplier": False,
            "notes": "Approved for NEOM Sindalah Island marine infrastructure.",
        },
        {
            "name": "Johnson Controls Middle East",
            "contact_person": "Mr. Mark Johnson",
            "email": "me.procurement@jci.com",
            "phone": "+971-4-4567890",
            "website": "https://www.johnsoncontrols.com",
            "categories": "HVAC, Building Management Systems, Fire Safety",
            "location": "Dubai, UAE",
            "rating": 4.8,
            "preferred_supplier": True,
            "notes": "Authorized supplier for ROSHN residential HVAC systems.",
        },
    ]
    suppliers_created = []
    for s in suppliers_data:
        existing = db.query(Supplier).filter(Supplier.email == s["email"]).first()
        if not existing:
            supplier = Supplier(**{k: v for k, v in s.items()})
            db.add(supplier)
            db.flush()
            suppliers_created.append(supplier)
        else:
            suppliers_created.append(existing)
    db.commit()
    print(f"   ✅ {len(suppliers_created)} Suppliers ready")

    # ─────────────────────────────────────────────────
    # 8. PROCUREMENT ITEMS
    # ─────────────────────────────────────────────────
    print("\n[8/12] Seeding Procurement Items...")
    items_data = [
        ("Structural Steel H-Beams 300x300mm", "Steel", 0, 0, "850 MT", 4250000, "RESEARCHING", "APPROVED"),
        ("Ready-Mix Concrete Grade 50", "Concrete", 1, 1, "12,000 m³", 1800000, "RFQ_NEEDED", "PENDING"),
        ("API 5L Grade X65 Carbon Steel Pipes", "Piping", 2, 2, "3,500 LM", 2100000, "ORDERED", "APPROVED"),
        ("Glass Fiber Reinforced Precast Panels", "Precast", 3, 3, "6,500 m²", 975000, "RFQ_NEEDED", "PENDING"),
        ("Al-Hejaz Limestone Cladding Tiles", "Stone", 4, None, "8,200 m²", 1640000, "RESEARCHING", "PENDING"),
        ("Aluminum Cable Tray 300x100mm", "Electrical", 5, 5, "22 KM", 550000, "RFQ_NEEDED", "APPROVED"),
        ("API 600 High-Pressure Gate Valves DN300", "Valves", 6, 2, "180 units", 720000, "ORDERED", "APPROVED"),
        ("Marine Steel Piles 600mm dia", "Marine", 7, 6, "950 units", 3800000, "RESEARCHING", "PENDING"),
        ("Zinc-coated Wire Mesh Reinforcement", "Concrete", 0, 0, "2,100 MT", 840000, "RFQ_NEEDED", "PENDING"),
        ("VRF HVAC System 5-Ton Units", "HVAC", 3, 7, "450 units", 2025000, "ORDERED", "APPROVED"),
        ("Solar PV Panels 550W Monocrystalline", "Energy", 0, 4, "8,000 units", 3200000, "RESEARCHING", "PENDING"),
        ("Fire Suppression Sprinkler System", "Safety", 1, 7, "1 System", 680000, "RFQ_NEEDED", "APPROVED"),
    ]
    proc_items_created = []
    for name, cat, topic_idx, sup_idx, qty, cost, status, approval in items_data:
        existing = db.query(ProcurementItem).filter(ProcurementItem.item_name == name).first()
        if not existing:
            item = ProcurementItem(
                project_id=topics_created[topic_idx].id,
                item_name=name,
                category=cat,
                supplier_id=suppliers_created[sup_idx].id if sup_idx is not None else None,
                quantity=qty,
                required_date=rand_future(90),
                estimated_cost=cost,
                technical_notes=f"Must comply with Saudi Building Code (SBC) and SASO standards. All materials require third-party inspection certificate from approved testing labs.",
                ai_recommendation=f"Based on market research, {suppliers_created[sup_idx].name if sup_idx is not None else 'local suppliers'} offer the best value. Recommend issuing formal RFQ to at least 3 qualified vendors.",
                status=status,
                approval_status=approval,
            )
            db.add(item)
            db.flush()
            proc_items_created.append(item)
        else:
            proc_items_created.append(existing)
    db.commit()
    print(f"   ✅ {len(proc_items_created)} Procurement Items ready")

    # ─────────────────────────────────────────────────
    # 9. RFQs
    # ─────────────────────────────────────────────────
    print("\n[9/12] Seeding RFQs...")
    rfq_statuses = ["SENT", "RECEIVED", "UNDER_COMPARISON", "APPROVED", "DRAFT", "OVERDUE", "UNDER_REVIEW"]
    rfqs_created = []
    rfq_details = [
        ("RFQ-SA-2026-001", "Structural Steel H-Beams - NEOM The Line", 0, 0, 0),
        ("RFQ-SA-2026-002", "Ready-Mix Concrete Grade 50 - Al Fursan", 1, 1, 1),
        ("RFQ-SA-2026-003", "API 5L Carbon Steel Pipes - Ras Tanura", 2, 2, 2),
        ("RFQ-SA-2026-004", "Precast Glass Fiber Panels - Sedra Phase 3", 3, 3, 3),
        ("RFQ-SA-2026-005", "Limestone Cladding - AlUla Heritage Village", 4, 4, 4),
        ("RFQ-SA-2026-006", "Aluminum Cable Trays - Metro Line 6", 5, 5, 5),
        ("RFQ-SA-2026-007", "High-Pressure Gate Valves - Jubail", 6, 6, 6),
        ("RFQ-SA-2026-008", "Marine Steel Piles - Sindalah Island", 7, 7, 7),
        ("RFQ-SA-2026-009", "Solar PV Panels 550W - NEOM The Line", 0, 0, 8),
        ("RFQ-SA-2026-010", "VRF HVAC System - ROSHN Sedra Towers", 3, 3, 9),
    ]
    for rfq_num, item_desc, topic_idx, sup_idx, item_idx in rfq_details:
        existing = db.query(RFQ).filter(RFQ.rfq_number == rfq_num).first()
        if not existing:
            rfq_status = random.choice(rfq_statuses)
            rfq = RFQ(
                rfq_number=rfq_num,
                project_id=topics_created[topic_idx].id,
                procurement_item_id=proc_items_created[item_idx].id if item_idx < len(proc_items_created) else None,
                supplier_id=suppliers_created[sup_idx].id,
                quantity=proc_items_created[item_idx].quantity if item_idx < len(proc_items_created) else "TBD",
                delivery_location=f"Project Site - {topics_created[topic_idx].topic_name[:30]}..., Saudi Arabia",
                required_delivery_date=rand_future(60),
                technical_requirements=f"All materials must comply with:\n- Saudi Building Code (SBC)\n- SASO Standards\n- ISO/ASTM international standards\n- Third-party inspection required\n- ARAMCO-approved testing only",
                status=rfq_status,
                email_subject=f"Request for Quotation: {item_desc} - {rfq_num}",
                email_body=f"Dear Supplier,\n\nWe invite you to submit your quotation for:\n\nItem: {item_desc}\nRFQ Reference: {rfq_num}\nProject: {topics_created[topic_idx].topic_name}\n\nPlease ensure all submissions comply with Saudi Building Code (SBC) standards.\n\nSubmission Deadline: {rand_future(14).strftime('%Y-%m-%d')}\n\nBest Regards,\nProcurement Department\nSaudi Government Procurement Office",
                quote_due_date=rand_future(21),
                supplier_sent_date=rand_past(10) if rfq_status not in ["DRAFT"] else None,
                internal_owner="Eng. Abdullah Al-Qahtani",
                site_address=f"{topics_created[topic_idx].topic_name[:40]}, Saudi Arabia",
                compliance_requirements="SBC, SASO, ISO 9001:2015",
                follow_up_sent=rfq_status in ["SENT", "OVERDUE"],
                follow_up_count=random.randint(0, 3),
            )
            db.add(rfq)
            db.flush()
            rfqs_created.append(rfq)
        else:
            rfqs_created.append(existing)
    db.commit()
    print(f"   ✅ {len(rfqs_created)} RFQs ready")

    # ─────────────────────────────────────────────────
    # 10. SUPPLIER QUOTES
    # ─────────────────────────────────────────────────
    print("\n[10/12] Seeding Supplier Quotes...")
    quote_statuses = ["PENDING", "REVIEWED", "SELECTED", "REJECTED"]
    for i, rfq in enumerate(rfqs_created[:6]):
        for j in range(random.randint(2, 3)):
            sup = suppliers_created[(i + j) % len(suppliers_created)]
            base_price = proc_items_created[i % len(proc_items_created)].estimated_cost
            variation = random.uniform(0.85, 1.20)
            quote = SupplierQuote(
                rfq_id=rfq.id,
                supplier_id=sup.id,
                quoted_price=round(base_price * variation, 2),
                lead_time=f"{random.randint(4, 16)} weeks",
                warranty=f"{random.choice([12, 18, 24, 36])} months - {random.choice(['International', 'Saudi Local', 'Manufacturer'])} warranty",
                compliance_notes="Compliant with Saudi Building Code (SBC), SASO standards, and international ISO certifications.",
                ai_extracted_summary=f"Supplier offers competitive pricing at {round(base_price * variation / 1000)}K SAR. Lead time is acceptable. Full SBC compliance confirmed. Recommend for final evaluation.",
                status=random.choice(quote_statuses),
                brand=random.choice(["Samsung", "Siemens", "ABB", "Honeywell", "Local Brand", "Al-Rajhi", "SABIC"]),
            )
            db.add(quote)
    db.commit()
    print(f"   ✅ Supplier Quotes ready")

    # ─────────────────────────────────────────────────
    # 11. DRAFTS
    # ─────────────────────────────────────────────────
    print("\n[11/12] Seeding Draft Replies...")
    draft_data = [
        {
            "thread_id": "THR-SA-2026-0001",
            "draft_type": "CLARIFICATION",
            "recipient": "procurement@neom.com",
            "subject": "RE: RFQ: Structural Steel Supply - Clarification Required",
            "body": "Dear NEOM Procurement Team,\n\nThank you for submitting RFQ reference NEOM-2026-FL-001.\n\nWe require the following clarifications:\n1. Please confirm the exact delivery point coordinates for The Line Phase 1\n2. Are there any special coating requirements (anti-corrosion for desert climate)?\n3. What is the minimum batch size per delivery?\n\nPlease respond by the end of this week to maintain the project timeline.\n\nBest Regards,\nProcurement Intelligence Assistant",
        },
        {
            "thread_id": "THR-SA-2026-0002",
            "draft_type": "ACKNOWLEDGMENT",
            "recipient": "tenders@housing.gov.sa",
            "subject": "RE: Tender: Ready-Mix Concrete - Acknowledgment",
            "body": "Dear Ministry of Housing Procurement Team,\n\nWe acknowledge receipt of your tender for Ready-Mix Concrete Grade 50 for the Al Fursan District project.\n\nYour submission is under review. We will revert within 3 business days with our formal response.\n\nReference: MOH-2026-AF-002\n\nKind Regards,\nSaudi Procurement Office",
        },
        {
            "thread_id": "THR-SA-2026-0003",
            "draft_type": "REPLY",
            "recipient": "supply@aramco.com",
            "subject": "RE: URGENT: Pipe Fittings Delivery Schedule",
            "body": "Dear Saudi Aramco Supply Team,\n\nWith reference to your urgent request for API 5L Pipe Fittings for the Ras Tanura expansion:\n\nWe confirm that delivery will be prioritized. Our logistics team has scheduled the following:\n- First shipment: 800 LM within 14 days\n- Remaining balance: 2,700 LM within 6 weeks\n\nAll items will be accompanied by material certificates and inspection reports.\n\nBest Regards,\nProcurement Team",
        },
        {
            "thread_id": "THR-SA-2026-0008",
            "draft_type": "CLARIFICATION",
            "recipient": "construction@neom.com",
            "subject": "RE: Marine Piling Materials - Environmental Compliance Query",
            "body": "Dear NEOM Marine Division,\n\nRegarding the Marine Piling requirement for Sindalah Island:\n\nWe need clarification on:\n1. Environmental impact assessment approval status from NCBE?\n2. Are the piles required to be coated with anti-fouling paint?\n3. What is the seabed condition report reference?\n\nThis information is required to finalize technical specifications.\n\nKind Regards,\nSenior Procurement Analyst",
        },
    ]
    for d in draft_data:
        existing = db.query(DraftReply).filter(
            DraftReply.recipient == d["recipient"],
            DraftReply.thread_id == d["thread_id"]
        ).first()
        if not existing:
            draft = DraftReply(
                thread_id=d["thread_id"],
                draft_type=d["draft_type"],
                recipient=d["recipient"],
                subject=d["subject"],
                body=d["body"],
                email_provider=random.choice(["outlook", "gmail"]),
                status="DRAFT",
                created_by="RFI_ASSISTANT",
            )
            db.add(draft)
    db.commit()
    print(f"   ✅ {len(draft_data)} Draft Replies ready")

    # ─────────────────────────────────────────────────
    # 12. APPROVAL SUMMARIES & PRIORITY SOURCES
    # ─────────────────────────────────────────────────
    print("\n[12/12] Seeding Approval Summaries & Search Sources...")
    
    # Approval Summaries
    approval_data = [
        {
            "rfq_id": rfqs_created[0].id,
            "topic_id": topics_created[0].id,
            "summary_text": "RFQ-SA-2026-001 for Structural Steel H-Beams has received 3 competitive quotations ranging from SAR 3.8M to 4.6M. The lowest compliant bid from Al-Rajhi Steel Company at SAR 4.05M offers full SBC compliance, 18-month warranty, and 6-week lead time. Recommend approval.",
            "recommended_action": "APPROVE - Al-Rajhi Steel at SAR 4,050,000",
            "risk_notes": "Steel market prices are volatile. Lock in price with supply agreement. Verify certification validity.",
            "status": "PENDING",
        },
        {
            "rfq_id": rfqs_created[1].id,
            "topic_id": topics_created[1].id,
            "summary_text": "RFQ-SA-2026-002 for Ready-Mix Concrete Grade 50 has 2 compliant bids. Saudi Readymix (SAR 1.71M) and a competitor (SAR 1.89M). Saudi Readymix is ARAMCO-approved and offers better mix consistency based on past project data.",
            "recommended_action": "APPROVE - Saudi Readymix Concrete at SAR 1,710,000",
            "risk_notes": "Ensure dedicated plant allocation for Al Fursan District proximity.",
            "status": "APPROVED",
            "reviewed_by": "Eng. Mohammed Al-Qahtani",
            "reviewed_at": rand_past(5),
        },
        {
            "rfq_id": rfqs_created[2].id,
            "topic_id": topics_created[2].id,
            "summary_text": "URGENT: RFQ-SA-2026-003 for API 5L Grade X65 Pipes is overdue. Gulf Pipes & Fittings has confirmed availability with API certification. Price SAR 2.1M is within budget estimate. ARAMCO approval required before issuance.",
            "recommended_action": "APPROVE URGENTLY - Gulf Pipes & Fittings at SAR 2,100,000",
            "risk_notes": "Project delay risk is HIGH if not approved within 48 hours.",
            "missing_info": "ARAMCO Vendor Qualification Certificate needs renewal verification.",
            "status": "PENDING",
        },
    ]
    for a in approval_data:
        approval = ApprovalSummary(
            rfq_id=a.get("rfq_id"),
            topic_id=a.get("topic_id"),
            generated_by_ai=True,
            summary_text=a["summary_text"],
            recommended_action=a.get("recommended_action"),
            risk_notes=a.get("risk_notes"),
            missing_info=a.get("missing_info"),
            status=a.get("status", "PENDING"),
            reviewed_by=a.get("reviewed_by"),
            reviewed_at=a.get("reviewed_at"),
        )
        db.add(approval)

    # Priority Search Sources (Saudi supplier portals)
    sources_data = [
        ("Etimad Platform - منصة اعتماد", "https://etimad.sa", 10, "Government Procurement"),
        ("Nupco - National Unified Procurement Co.", "https://nupco.com", 9, "Medical & Government"),
        ("SABIC Supplier Portal", "https://sabic.com/suppliers", 8, "Petrochemical"),
        ("Aramco Supplier Portal", "https://supplier.aramco.com.sa", 10, "Oil & Gas"),
        ("NEOM Procurement Portal", "https://procurement.neom.com", 9, "Mega Projects"),
        ("Saudi Aramco Materials Portal", "https://materials.aramco.com.sa", 8, "Industrial Materials"),
        ("Ministry of Housing Tender Portal", "https://housing.gov.sa/tenders", 7, "Construction"),
        ("Al-Bawani B2B Platform", "https://b2b.albawani.com.sa", 6, "Construction Materials"),
        ("Blackwoods", "https://www.blackwoods.com.au/", 9, "Industrial & Safety"),
        ("Sydney Tools", "https://sydneytools.com.au/", 9, "Tools & Equipment"),
    ]
    for name, url, priority, priority_for in sources_data:
        existing = db.query(PrioritySearchSource).filter(PrioritySearchSource.url == url).first()
        if not existing:
            source = PrioritySearchSource(
                name=name,
                url=url,
                priority=priority,
                priority_for=priority_for,
                is_active=True,
            )
            db.add(source)
    db.commit()
    print(f"   ✅ Approval Summaries & Search Sources ready")

    # ─────────────────────────────────────────────────
    # AUDIT LOGS (for dashboard activity feed)
    # ─────────────────────────────────────────────────
    admin_user = db.query(User).filter(User.role.in_(["admin", "superadmin"])).first()
    audit_actions = [
        ("EMAIL_PROCESSED", "Processed email: Structural Steel RFQ from NEOM", "THR-SA-2026-0001"),
        ("RFQ_CREATED", "Created RFQ-SA-2026-001 for NEOM Steel Supply", "THR-SA-2026-0001"),
        ("SUPPLIER_QUOTE_RECEIVED", "Received quote from Al-Rajhi Steel SAR 4.05M", "THR-SA-2026-0001"),
        ("APPROVAL_REQUESTED", "Approval requested for RFQ-SA-2026-002 Ready-Mix Concrete", "THR-SA-2026-0002"),
        ("EMAIL_PROCESSED", "Processed URGENT: Pipe Fittings from ARAMCO", "THR-SA-2026-0003"),
        ("DRAFT_CREATED", "AI drafted clarification reply for NEOM Marine Piling", "THR-SA-2026-0008"),
        ("SUPPLIER_ADDED", "New supplier added: Johnson Controls Middle East", None),
        ("RFQ_SENT", "RFQ-SA-2026-003 dispatched to Gulf Pipes & Fittings", "THR-SA-2026-0003"),
        ("APPROVAL_GRANTED", "RFQ-SA-2026-002 approved by Eng. Mohammed Al-Qahtani", "THR-SA-2026-0002"),
        ("EMAIL_SYNCED", "Email sync completed: 15 new emails from Outlook/Gmail", None),
    ]
    for action, details_str, thread_id in audit_actions:
        log = AuditLog(
            user_id=admin_user.id if admin_user else None,
            thread_id=thread_id,
            agent="RFI_ASSISTANT",
            action=action,
            details={"message": details_str, "source": "Saudi_Procurement_System"},
            ip_address="192.168.1.1",
            timestamp=rand_past(14),
        )
        db.add(log)
    db.commit()

    # ─────────────────────────────────────────────────
    # ASSISTANT CONVERSATIONS
    # ─────────────────────────────────────────────────
    # 1. Procurement Mode Conversation
    conv_proc = AssistantConversation(
        title="NEOM Steel Supply Analysis",
        mode="procurement",
    )
    db.add(conv_proc)
    db.flush()
    chats_proc = [
        ("user", "What is the best steel supplier for NEOM The Line project?"),
        ("assistant", "Based on my analysis of current market data and vendor qualifications, Al-Rajhi Steel Company is the top recommendation for NEOM The Line structural steel requirement.\n\n**Key Reasons:**\n- ISO 9001:2015 certified\n- ARAMCO and NEOM approved vendor\n- Competitive pricing at ~SAR 4.7M for your required volume\n- 6-week lead time meets project schedule\n- Full SBC compliance documentation available\n\nWould you like me to draft an RFQ to send them?"),
        ("user", "Yes, draft an RFQ for 850MT of H-Beams 300x300mm"),
        ("assistant", "RFQ draft prepared for RFQ-SA-2026-001:\n\n**To:** Al-Rajhi Steel Company\n**Item:** Structural Steel H-Beams 300x300mm\n**Quantity:** 850 Metric Tons\n**Delivery:** NEOM The Line Site, Tabuk Region\n**Compliance:** SBC, SASO, ISO 9001:2015\n\nThe draft is now in your Drafts folder. Shall I also include anti-corrosion coating specifications for desert climate?"),
    ]
    for role, content in chats_proc:
        chat = AssistantChat(conversation_id=conv_proc.id, role=role, content=content)
        db.add(chat)

    # 2. Market Mode Conversation
    conv_market = AssistantConversation(
        title="Drill & Tools Market Sync",
        mode="market",
    )
    db.add(conv_market)
    db.flush()
    chats_market = [
        ("user", "Compare cordless hammer drills from Bunnings and Sydney Tools"),
        ("assistant", "Here is a comparison of cordless hammer drills from Bunnings and Sydney Tools based on our priority sources:\n\n1. **DeWalt 18V XR Brushless Hammer Drill**\n   - **Sydney Tools:** SAR 890 (In Stock, 3 Year Warranty)\n   - **Bunnings:** SAR 920 (Special Order, 3 Year Warranty)\n   - **Recommendation:** Purchase from Sydney Tools for direct cost savings.\n\n2. **Milwaukee 18V FUEL Heavy Duty Hammer Drill**\n   - **Sydney Tools:** SAR 1,150 (In Stock, 5 Year Warranty)\n   - **Bunnings:** N/A (Not stocked in this configuration)\n   - **Recommendation:** Sydney Tools is the sole provider for this heavy-duty spec.\n\nWould you like me to prepare an RFQ template for the DeWalt drills?"),
    ]
    for role, content in chats_market:
        chat = AssistantChat(conversation_id=conv_market.id, role=role, content=content)
        db.add(chat)

    # 3. General Mode Conversation
    conv_gen = AssistantConversation(
        title="BOQ Best Practices",
        mode="general",
    )
    db.add(conv_gen)
    db.flush()
    chats_gen = [
        ("user", "What is a Bill of Quantities (BOQ)?"),
        ("assistant", "A Bill of Quantities (BOQ) is a detailed document prepared by a quantity surveyor or cost estimator that lists the quantities of materials, parts, and labor required for a construction project.\n\n**Its primary purposes are:**\n1. **Tendering:** It enables all bidding contractors to price the project based on the exact same measurements, ensuring fair competition.\n2. **Valuation:** It provides a basis for valuing progress payments and variations during construction.\n3. **Cost Control:** Helps project managers track actual costs against the original budget.\n\nDo you need help parsing a BOQ Excel sheet?"),
    ]
    for role, content in chats_gen:
        chat = AssistantChat(conversation_id=conv_gen.id, role=role, content=content)
        db.add(chat)

    db.commit()

    # ─────────────────────────────────────────────────
    # PRODUCT RESULTS (for comparison page)
    # ─────────────────────────────────────────────────
    product_results = [
        {
            "item_name": "Structural Steel H-Beam 300x300mm",
            "supplier": "Al-Rajhi Steel",
            "unit_price": 4980.0,
            "unit": "MT",
            "source_url": "https://alrajhisteel.com.sa/h-beam-300",
            "category": "Building Materials",
            "brand": "Al-Rajhi",
            "specs_json": {"Grade": "S355", "Standard": "ASTM A36", "Coating": "Hot-dip galvanized", "Compliance": "SBC-304"},
            "confidence_level": "High",
            "best_for": "Heavy structural framing in desert climate",
            "topic_id": topics_created[0].id,
        },
        {
            "item_name": "Ready-Mix Concrete Grade C50",
            "supplier": "Saudi Readymix",
            "unit_price": 145.0,
            "unit": "m³",
            "source_url": "https://srmcc.com.sa/grade-50",
            "category": "Building Materials",
            "brand": "Saudi Readymix",
            "specs_json": {"Grade": "C50", "Aggregate": "20mm crushed limestone", "Slump": "150mm", "Compliance": "SASO 2000"},
            "confidence_level": "High",
            "best_for": "High-rise structural slabs and foundations",
            "topic_id": topics_created[1].id,
        },
        {
            "item_name": "VRF HVAC System 5-Ton",
            "supplier": "Johnson Controls",
            "unit_price": 4560.0,
            "unit": "unit",
            "source_url": "https://johnsoncontrols.com/vrf-5ton",
            "category": "Tools",
            "brand": "York",
            "specs_json": {"Voltage": "380V 3-phase", "EER": "4.2", "Refrigerant": "R410A", "Warranty": "3 Years"},
            "confidence_level": "High",
            "best_for": "Residential towers in hot climate",
            "topic_id": topics_created[3].id,
        },
        {
            "item_name": "VRF HVAC System 5-Ton",
            "supplier": "Siemens Saudi Arabia",
            "unit_price": 4980.0,
            "unit": "unit",
            "source_url": "https://siemens.com/sa/hvac",
            "category": "Tools",
            "brand": "Siemens",
            "specs_json": {"Voltage": "380V 3-phase", "EER": "4.5", "Refrigerant": "R410A", "Warranty": "5 Years"},
            "confidence_level": "High",
            "best_for": "Smart building integration with BMS",
            "topic_id": topics_created[3].id,
        },
    ]
    for pr in product_results:
        result = ProductResult(**pr)
        db.add(result)
    db.commit()

    print("\n" + "=" * 60)
    print("  ✅ ALL DUMMY DATA SEEDED SUCCESSFULLY!")
    print("=" * 60)
    print("\n📊 Data Summary:")
    print(f"   • Tags:               {db.query(__import__('database.models', fromlist=['Tag']).Tag).count()}")
    print(f"   • Contacts:           {db.query(Contact).count()}")
    print(f"   • Topics/Projects:    {db.query(Topic).count()}")
    print(f"   • Threads/Tenders:    {db.query(Thread).count()}")
    print(f"   • Emails:             {db.query(Email).count()}")
    print(f"   • Attachments:        {db.query(Attachment).count()}")
    print(f"   • Suppliers:          {db.query(Supplier).count()}")
    print(f"   • Procurement Items:  {db.query(ProcurementItem).count()}")
    print(f"   • RFQs:               {db.query(RFQ).count()}")
    print(f"   • Supplier Quotes:    {db.query(SupplierQuote).count()}")
    print(f"   • Draft Replies:      {db.query(DraftReply).count()}")
    print(f"   • Approval Summaries: {db.query(ApprovalSummary).count()}")
    print(f"   • Audit Logs:         {db.query(AuditLog).count()}")
    print("\n🚀 Ab server chalao:")
    print("   python api/main.py")
    print("\n🌐 Browser mein kholo:")
    print("   http://localhost:8069")
    print("\n🔑 Login credentials:")
    print("   user123 / user12345")
    print("   admin@123 / admin123")
    print("   superadmin / superadmin123")
    print("=" * 60)

except Exception as e:
    db.rollback()
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
