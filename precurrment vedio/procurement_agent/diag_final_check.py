
import asyncio
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.main import get_emails
from backend.database import SessionLocal

async def test_fetch():
    print("--- Starting Diagnostic Fetch ---")
    db = SessionLocal()
    try:
        # We test with gmail (or whatever the user has connected)
        # This will run the actual logic in main.py
        result = await get_emails(provider="gmail", db=db)
        
        if isinstance(result, list):
            print(f"SUCCESS: Fetched and processed {len(result)} emails.")
            if len(result) > 0:
                print("First email snippet:", result[0].get('subject'))
        else:
            # If it returned a JSONResponse (due to our error handler)
            print("FAILURE: Endpoint returned an error response.")
            print("Response info:", result)
            
    except Exception as e:
        print(f"CRASH: The function itself raised an exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    print("--- Diagnostic Complete ---")

if __name__ == "__main__":
    asyncio.run(test_fetch())
