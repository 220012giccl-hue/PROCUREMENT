import json
from ..database.session import SessionLocal
from ..database.models import Vendor, Client, Project, ProjectVersion
from .llm_client import LLMClient

class ClassificationEngine:
    def __init__(self):
        self.llm = LLMClient()

    def classify_and_route(self, db, sender_email, subject, body, attachment_text=None):
        vendor = db.query(Vendor).filter(Vendor.email == sender_email).first()
        if vendor:
            print(f"DEBUG: [Classification] Found verified vendor: {sender_email}")
            return {"role": "vendor", "classification": "quote", "label": "Verified Supplier"}

        # AI Classification with Context
        client = db.query(Client).filter(Client.email == sender_email).first()
        existing_projects_context = ""
        if client and client.projects:
            projects_list = [f"- {p.name} (ID: {p.id}, Status: {p.status})" for p in client.projects if p.status == 'active']
            if projects_list:
                existing_projects_context = "\n[EXISTING PROJECTS FOR THIS CLIENT]:\n" + "\n".join(projects_list)
        
        print(f"DEBUG: [Classification] Running AI analysis for: {subject}")
        user_msg = f"Subject: {subject}\n\nBody:\n{body or ''}{existing_projects_context}"
        response_str = self.llm.analyze_email_classification(user_msg, attachment_text=attachment_text)
        
        try:
             result = json.loads(response_str)
             category = result.get("category", "OTHER")
             req_category = result.get("requirement_category", "General")
             project_topic = result.get("project_topic", "General Procurement")
             is_new_project = result.get("is_new_project", True)
             
             print(f"DEBUG: [Classification] AI Category Result: {category} ({req_category}) | New Project: {is_new_project}")
             
             role = "unknown"
             if category == "NEW_PROCUREMENT": role = "client"
             elif category == "QUOTATION": role = "vendor"
             
             return {
                 "role": role, 
                 "classification": category.lower(), 
                 "requirement_category": req_category,
                 "project_topic": project_topic,
                 "is_new_project": is_new_project
             }
        except Exception as e:
             print(f"ERROR: [Classification] Failed to parse AI response: {e}")
             return {"role": "unknown", "classification": "irrelevant"}
