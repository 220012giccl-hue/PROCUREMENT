from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ARRAY, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

# Association table for Many-to-Many relationship between Email and Tag
email_tags = Table(
    'email_tags',
    Base.metadata,
    Column('email_id', Integer, ForeignKey('emails.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

# Association table for Many-to-Many relationship between Thread and Tag
thread_tags = Table(
    'thread_tags',
    Base.metadata,
    Column('thread_id', Integer, ForeignKey('threads.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Contact(Base):
    """Formerly Client"""
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    contact_name = Column(String(255), nullable=False)
    email_domain = Column(String(100))
    contact_emails = Column(ARRAY(Text))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_contact = Column(DateTime)
    total_interactions = Column(Integer, default=0)
    meta_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topics = relationship('Topic', back_populates='contact')
    threads = relationship('Thread', back_populates='contact')

class Topic(Base):
    """Formerly Project"""
    __tablename__ = 'topics'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    topic_name = Column(String(255))
    topic_reference = Column(String(100))
    thread_id = Column(String(50), unique=True)
    status = Column(String(50), default='ACTIVE')
    folder_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_data = Column(JSONB)
    
    # Relationships
    contact = relationship('Contact', back_populates='topics')
    threads = relationship('Thread', back_populates='topic')

class Tag(Base):
    """New Category/Tag Model"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(20), default='#6366f1') # Default indigo
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    emails = relationship('Email', secondary=email_tags, back_populates='tags')
    threads = relationship('Thread', secondary=thread_tags, back_populates='tags')

class Thread(Base):
    """Formerly Tender"""
    __tablename__ = 'threads'
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(String(50), unique=True, nullable=False)
    status = Column(String(50), nullable=False, default='PROCESSING')
    
    # Foreign Keys
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    topic_id = Column(Integer, ForeignKey('topics.id'))
    
    # Details
    subject = Column(Text)
    contact_name = Column(String(255))
    topic_name = Column(String(255))
    thread_reference = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(50))
    source_email = Column(String(255))
    source_sender = Column(String(255))
    meta_data = Column(JSONB)
    
    # Relationships
    contact = relationship('Contact', back_populates='threads')
    topic = relationship('Topic', back_populates='threads')
    tags = relationship('Tag', secondary=thread_tags, back_populates='threads')

class Email(Base):
    __tablename__ = 'emails'
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(String(50), index=True) # Link to Thread.thread_id
    email_id = Column(String(255), unique=True)
    message_id = Column(String(255), index=True) # RFC 2822 Message-ID
    in_reply_to = Column(String(255), index=True) # Parent Message-ID
    subject = Column(Text)
    sender = Column(String(255))
    recipients = Column(ARRAY(Text))
    body = Column(Text)
    received_at = Column(DateTime(timezone=True))
    is_actionable = Column(Boolean, default=True)
    is_junk = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False) # New: Track outgoing mail
    detection_confidence = Column(Float)
    tags_suggested = Column(ARRAY(Text))
    processed = Column(Boolean, default=False)
    meta_data = Column(JSONB) # New: Store meeting details, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tags = relationship('Tag', secondary=email_tags, back_populates='emails')

class Attachment(Base):
    """Formerly Document"""
    __tablename__ = 'attachments'
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(String(50), index=True)
    email_id = Column(String(255), index=True) # Link to specific email
    category = Column(String(100)) # e.g. "01_Instructions", "02_Scope_of_Work"
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size_bytes = Column(Integer)
    doc_type = Column(String(50)) # e.g. "Invoice", "Contract", "Image"
    summary = Column(Text)
    is_correct = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50))

# Aliases for backward compatibility
Document = Attachment

class DraftReply(Base):
    """Formerly DraftEmail / RFIDraft"""
    __tablename__ = 'draft_replies'
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(String(50), index=True)
    draft_type = Column(String(50))  # 'REPLY', 'CLARIFICATION', 'ACKNOWLEDGMENT'
    
    # Email details
    recipient = Column(String(255), nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    
    # Provider details (Outlook/Gmail)
    email_provider = Column(String(20))  # 'outlook' or 'gmail'
    provider_draft_id = Column(String(255))  # Draft ID from email provider
    
    # Status and metadata
    status = Column(String(50), default='DRAFT')  # 'DRAFT', 'SENT', 'DELETED'
    created_by = Column(String(50), default='GENERAL_EMAIL_ASSISTANT')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = Column(DateTime)
    
    # Link to original email
    in_reply_to_email_id = Column(String(255))
    meta_data = Column(JSONB)
    scheduled_at = Column(DateTime) # For future "Send Later" feature

class FollowupTask(Base):
    """New: Track threads that need following up"""
    __tablename__ = 'followup_tasks'
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(String(50), ForeignKey('threads.thread_id'))
    original_email_id = Column(String(255)) # ID of the sent email we are following up on
    recipient = Column(String(255))
    suggested_body = Column(Text)
    status = Column(String(50), default='PENDING') # PENDING, ACTIONED, IGNORED
    due_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default='user') # 'superadmin', 'admin', 'user'
    is_active = Column(Boolean, default=True)
    preferences = Column(JSONB, default=lambda: {})
    
    # Intelligence & Style Settings
    brand_voice = Column(Text) # Raw samples provided by user
    custom_instructions = Column(Text) # Explicit user preferences
    writing_style_guide = Column(Text) # AI analyzed communication style rules
    last_style_sync = Column(DateTime) # Last time background sync ran
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    audit_logs = relationship('AuditLog', back_populates='user')

class AuditLog(Base):
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    thread_id = Column(String(50))
    agent = Column(String(50), default='RFI_AGENT') 
    action = Column(String(100), nullable=False)
    details = Column(JSONB)
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='audit_logs')

class AssistantConversation(Base):
    __tablename__ = 'assistant_conversations'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), default='New Conversation')
    mode = Column(String(20), default='enterprise') # 'enterprise' or 'general'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AssistantChat(Base):
    __tablename__ = 'assistant_chat'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('assistant_conversations.id'), nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Supplier(Base):
    """Database of suppliers and vendors"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    categories = Column(Text) # Comma-separated categories e.g. "Tools, Safety Gear, Concrete"
    location = Column(String(255))
    rating = Column(Float, default=0.0)
    preferred_supplier = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProcurementItem(Base):
    """Items saved to the procurement list"""
    __tablename__ = 'procurement_items'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('topics.id'), nullable=True) # Link to Topic (Project)
    item_name = Column(String(255), nullable=False)
    category = Column(String(100))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    quantity = Column(String(50))
    required_date = Column(DateTime)
    estimated_cost = Column(Float)
    source_url = Column(Text)
    technical_notes = Column(Text)
    ai_recommendation = Column(Text)
    status = Column(String(50), default='RESEARCHING') # RESEARCHING, RFQ_NEEDED, ORDERED, etc.
    approval_status = Column(String(50), default='PENDING') # PENDING, APPROVED, REJECTED
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RFQ(Base):
    """Request for Quote records"""
    __tablename__ = 'rfqs'
    
    id = Column(Integer, primary_key=True)
    rfq_number = Column(String(50), unique=True, nullable=False)
    project_id = Column(Integer, ForeignKey('topics.id'))
    procurement_item_id = Column(Integer, ForeignKey('procurement_items.id'))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    quantity = Column(String(50))
    delivery_location = Column(Text)
    required_delivery_date = Column(DateTime)
    technical_requirements = Column(Text)
    status = Column(String(50), default='DRAFT')
    # Valid statuses: DRAFT | READY | SENT | SUPPLIER_ACKNOWLEDGED | RECEIVED |
    #                 CLARIFICATION_REQUIRED | UNDER_COMPARISON | UNDER_REVIEW |
    #                 APPROVED | REJECTED | CLOSED | EXPIRED | OVERDUE
    email_subject = Column(Text)
    email_body = Column(Text)
    # ── Extended fields (Migration 005) ─────────────────────────────────────
    quote_due_date          = Column(DateTime, nullable=True)
    supplier_sent_date      = Column(DateTime, nullable=True)
    supplier_response_date  = Column(DateTime, nullable=True)
    internal_owner          = Column(String(255), nullable=True)
    site_address            = Column(Text, nullable=True)
    drawing_reference       = Column(Text, nullable=True)
    compliance_requirements = Column(Text, nullable=True)
    follow_up_sent          = Column(Boolean, default=False)
    follow_up_count         = Column(Integer, default=0)
    # ────────────────────────────────────────────────────────────────────────
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SupplierQuote(Base):
    """Quotes received from suppliers for specific RFQs"""
    __tablename__ = 'supplier_quotes'
    
    id = Column(Integer, primary_key=True)
    rfq_id = Column(Integer, ForeignKey('rfqs.id'))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    quoted_price = Column(Float)
    lead_time = Column(String(100))
    warranty = Column(String(255))
    compliance_notes = Column(Text)
    attachment_id = Column(Integer, ForeignKey('attachments.id'), nullable=True)
    ai_extracted_summary = Column(Text)
    status = Column(String(50), default='PENDING') # PENDING, REVIEWED, SELECTED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Extended fields (migration 006) ──────────────────────────────────────
    brand      = Column(String(255), nullable=True)  # Brand vendor is quoting
    specs_json = Column(JSONB, default={})           # Vendor-provided specs (same keys as ProductResult)

class ProductComparison(Base):
    """Stores side-by-side comparison results generated by AI or User"""
    __tablename__ = 'product_comparisons'
    
    id = Column(Integer, primary_key=True)
    query_id = Column(String(255), nullable=True) # ID of the chat or search query
    title = Column(String(255)) # e.g. "Hammer Drill Comparison"
    category = Column(String(100)) # Tools, PPE, Building Materials
    products_json = Column(JSONB) # List of product objects being compared
    comparison_table_json = Column(JSONB) # The actual table data (headers and rows)
    recommendation = Column(Text) # AI reasoning for the best choice
    missing_info_json = Column(JSONB) # Fields that were not found for some suppliers
    confidence_level = Column(String(50)) # High, Medium, Low
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PrioritySearchSource(Base):
    """Specific websites that the AI should prioritize during product research"""
    __tablename__ = 'priority_search_sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255)) # e.g. "Bunnings", "Masters"
    url = Column(String(1000)) # e.g. "https://www.bunnings.com.au"
    priority = Column(Integer, default=1) # Higher number = higher priority
    priority_for = Column(String(255), nullable=True) # e.g. "PPE", "Tools", "General Hardware"
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── New Models (PRD v2.1 — Migration 004) ──────────────────────────────────────

class RFQWorkflow(Base):
    """
    Tracks the lifecycle state of each incoming RFQ email as it moves through
    the pipeline: ingested → triage/researching → drafts_ready → sent → quotes_received
    Added in PRD v2.1 (migration 004).
    """
    __tablename__ = 'rfq_workflows'

    id               = Column(Integer, primary_key=True)
    topic_id         = Column(Integer, ForeignKey('topics.id'), nullable=True)
    thread_id        = Column(Integer, ForeignKey('threads.id'), nullable=True)
    status           = Column(String(100), default='ingested')
    # status values: ingested | triage | researching | drafts_ready | sent | quotes_received
    confidence_score = Column(Float, nullable=True)   # 0.0 – 1.0 from Context Resolver
    assigned_by      = Column(String(100), default='ai')  # 'ai' or 'human'
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    topic  = relationship('Topic',  foreign_keys=[topic_id])
    thread = relationship('Thread', foreign_keys=[thread_id])


class ProductResult(Base):
    """
    Stores market research price data fetched from public supplier catalogues
    (Bunnings, Sydney Tools, Blackwoods) for a given topic/project.
    Added in PRD v2.1 (migration 004).
    Extended in migration 006: added category, brand, specs_json, confidence_level, image_url, best_for.
    """
    __tablename__ = 'product_results'

    id               = Column(Integer, primary_key=True)
    topic_id         = Column(Integer, ForeignKey('topics.id'), nullable=True)
    item_name        = Column(Text, nullable=False)
    supplier         = Column(Text)             # e.g. "Bunnings", "Sydney Tools"
    unit_price       = Column(Float, nullable=True)
    unit             = Column(String(50))       # e.g. "each", "m", "box"
    source_url       = Column(Text)
    fetched_at       = Column(DateTime, default=datetime.utcnow)

    # ── Extended fields (migration 006) ──────────────────────────────────────
    # Category drives which comparison table columns to show in the frontend
    # Values: 'Tools' | 'PPE' | 'Building Materials' | 'Ladders' | 'Fasteners' | 'General'
    category         = Column(String(100), nullable=True)
    brand            = Column(String(255), nullable=True)   # e.g. "Milwaukee", "DeWalt"
    # Dynamic technical specs dict, keys depend on category:
    #   Tools:     {"Voltage": "18V", "Battery Included": "Yes", "Warranty": "3 Years"}
    #   PPE:       {"Safety Rating": "AS/NZS 2161", "Size Range": "S-3XL", "Material": "Leather"}
    #   Building:  {"Material": "Treated Pine", "Size": "90x45mm", "Pack Qty": "20", "Compliance": "AS 1720"}
    specs_json       = Column(JSONB, default={})
    confidence_level = Column(String(50), nullable=True)    # 'High' | 'Medium' | 'Low'
    image_url        = Column(Text, nullable=True)           # Product image URL from supplier
    best_for         = Column(Text, nullable=True)           # e.g. "Heavy site work"

    # Relationships
    topic = relationship('Topic', foreign_keys=[topic_id])


# ── New Models (Migration 005) ──────────────────────────────────────────────────

class ApprovalSummary(Base):
    """
    AI-generated manager approval summary for a procurement item or RFQ.
    Human reviews this before any purchase decision is made.
    Added in migration 005.
    """
    __tablename__ = 'approval_summaries'

    id                  = Column(Integer, primary_key=True)
    rfq_id              = Column(Integer, ForeignKey('rfqs.id'), nullable=True)
    procurement_item_id = Column(Integer, ForeignKey('procurement_items.id'), nullable=True)
    topic_id            = Column(Integer, ForeignKey('topics.id'), nullable=True)
    generated_by_ai     = Column(Boolean, default=True)
    summary_text        = Column(Text, nullable=False)
    recommended_action  = Column(Text)
    risk_notes          = Column(Text)
    missing_info        = Column(Text)
    status              = Column(String(50), default='PENDING')  # PENDING | APPROVED | REJECTED
    reviewed_by         = Column(String(255))
    reviewed_at         = Column(DateTime, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rfq   = relationship('RFQ',             foreign_keys=[rfq_id])
    topic = relationship('Topic',           foreign_keys=[topic_id])


# ── Aliases for backward compatibility with RFQ Agent code base ────────────────
Tender = Thread
DraftEmail = DraftReply
Client = Contact
Project = Topic
RFIDraft = DraftReply
