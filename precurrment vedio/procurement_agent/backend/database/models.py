from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .session import Base

# --- Models ---

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="client")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    name = Column(String, index=True)
    status = Column(String, default="active") # active, closed
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="projects")
    versions = relationship("ProjectVersion", back_populates="project")

class ProjectVersion(Base):
    __tablename__ = "project_versions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    version_number = Column(Integer, default=1)
    status = Column(String, default="procurement") # planning, procurement, review, complete
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="versions")
    emails = relationship("EmailRecord", back_populates="project_version")
    rfqs = relationship("RFQ", back_populates="project_version")

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    category = Column(String, index=True) # Builder, Plumber, etc.
    region = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class EmailRecord(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True, nullable=True)
    project_version_id = Column(Integer, ForeignKey("project_versions.id"), nullable=True)
    sender = Column(String, index=True)
    subject = Column(String)
    body = Column(Text)
    provider = Column(String, nullable=True)
    role = Column(String) # client, vendor, unknown
    classification = Column(String) # new_procurement, quote, info, irrelevant
    is_processed = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False) # For server-side sync
    requirement_category = Column(String, nullable=True) # e.g. Plumber, Electrician, Civil
    received_at = Column(DateTime, default=datetime.utcnow)

    project_version = relationship("ProjectVersion", back_populates="emails")

class QuotedPrice(Base):
    __tablename__ = "quoted_prices"
    id = Column(Integer, primary_key=True, index=True)
    project_version_id = Column(Integer, ForeignKey("project_versions.id"))
    vendor_email = Column(String, index=True)
    product = Column(String)
    price = Column(Integer)
    unit = Column(String, nullable=True)
    vendor_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime, nullable=True) # Linked email date

    project_version = relationship("ProjectVersion", backref="quoted_prices")

class RFQ(Base):
    __tablename__ = "rfqs"
    id = Column(Integer, primary_key=True, index=True)
    project_version_id = Column(Integer, ForeignKey("project_versions.id"))
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    project_version = relationship("ProjectVersion", back_populates="rfqs")
    drafts = relationship("VendorDraft", back_populates="rfq")

class VendorDraft(Base):
    __tablename__ = "vendor_drafts"
    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id"), nullable=True)
    project_version_id = Column(Integer, ForeignKey("project_versions.id"), nullable=True) # Direct link
    vendor_email = Column(String)
    recipient = Column(String, nullable=True) # Adding recipient for consistency
    vendor_name = Column(String, nullable=True) # Adding vendor_name
    subject = Column(String)
    body = Column(Text)
    status = Column(String, default="pending") # pending, sent
    sent_at = Column(DateTime, nullable=True)
    source_id = Column(Integer, nullable=True) # Link to EmailRecord or File for Refer/Backlink

    rfq = relationship("RFQ", back_populates="drafts")
    project_version = relationship("ProjectVersion", backref="drafts")
