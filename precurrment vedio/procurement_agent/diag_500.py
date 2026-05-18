
import sys
import os

# Add the current directory to sys.path to allow importing from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.main import get_emails
from backend.database import SessionLocal
import asyncio

async def test():
    db = SessionLocal()
    try:
        print("Testing get_emails('gmail')...")
        result = await get_emails(provider='gmail', db=db)
        print("Success!")
        print(f"Result count: {len(result)}")
    except Exception as e:
        print(f"FAILED with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test())
