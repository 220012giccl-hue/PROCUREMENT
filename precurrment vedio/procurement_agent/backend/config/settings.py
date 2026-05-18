import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from the project root (4 parents up from config/settings.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# PROCUREMENT AGENT CONFIGURATION
APP_NAME = "PROCUREMENT AGENT"

# Project Root and Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BACKEND_DIR.parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)

# Outlook OAuth2 Settings
OUTLOOK_OAUTH_ENABLED = True
OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID", "")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET", "")
OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID", "consumers")
OUTLOOK_REDIRECT_URI = os.getenv("OUTLOOK_REDIRECT_URI", "http://localhost:5001/oauth/callback")

# Gmail OAuth2 Configuration
GMAIL_OAUTH_ENABLED = True
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:5001/gmail/oauth/callback")
GMAIL_TOKEN_FILE = ".gmail_oauth_token.json"

# Direct Settings (IMAP)
GMAIL_HOST = "imap.gmail.com"
GMAIL_PORT = 993
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD", "")

OUTLOOK_HOST = "outlook.office365.com"
OUTLOOK_PORT = 993
OUTLOOK_USER = os.getenv("OUTLOOK_USER", "")
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_PASSWORD", "")

# LLM URL
LLM_API_URL = os.getenv("LLM_API_URL", "https://openrouter.ai/api/v1/")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo-instruct")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# PostgreSQL Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/procurement_db")

# Data Paths
VENDORS_FILE = DATA_DIR / "vendors.json"
EMAILS_FILE = DATA_DIR / "emails.json"
DRAFTS_FILE = DATA_DIR / "drafts.json"
