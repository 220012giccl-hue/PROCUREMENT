import sys
import os

print("[1] Script started")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[2] Dotenv loaded")
except Exception as e:
    print("Error loading dotenv:", e)

try:
    from config.database import Base
    print("[3] Database config imported")
except Exception as e:
    print("Error loading DB config:", e)

try:
    from api.routes import auth, user, emails
    print("[4] Basic API routes imported")
except Exception as e:
    print("Error loading basic routes:", e)

try:
    from api.routes import assistant, procurement
    print("[5] Assistant routes imported")
except Exception as e:
    print("Error loading assistant routes:", e)

try:
    from api.main import app
    print("[6] Main app imported successfully!")
except Exception as e:
    print("ERROR loading main app:", e)
