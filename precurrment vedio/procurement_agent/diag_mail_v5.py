import sys
sys.path.insert(0, '.')
from backend.auth_handler import OAuthHandler
from backend.mail_handler import MailHandler
from backend.classification_engine import ClassificationEngine
from backend.database import SessionLocal

auth = OAuthHandler()
mail = MailHandler()
engine = ClassificationEngine()
db = SessionLocal()

provider = "gmail"
token, email_addr = auth.get_token_details(provider)
print(f"DEBUG: Token for {provider}: {bool(token)}, Email: {email_addr}")

if token:
    raw_emails = mail.fetch_emails(provider, token=token, email_address=email_addr)
    print(f"DEBUG: Fetched {len(raw_emails)} raw emails")
    
    for email in raw_emails:
        subj = email.get('subject', '')
        send = email.get('sender', '')
        body = email.get('body', '')
        
        # Test the classification directly
        result = engine.classify_and_route(db, send, subj, body)
        print(f"\n--- Email: {subj} ---")
        print(f"Sender: {send}")
        print(f"Classification: {result['role']} ({result['classification']})")
        print(f"Label: {result['label']}")
        
        # Relevance check like in main.py
        is_relevant = result.get('role') in ['client', 'vendor', 'potential_vendor'] and result.get('classification') != 'irrelevant'
        print(f"Is Relevant: {is_relevant}")

db.close()
