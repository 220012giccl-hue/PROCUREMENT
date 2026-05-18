
from fastapi.testclient import TestClient
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.main import app

client = TestClient(app)

def test_request():
    print("--- Simulating Browser Request (GET /api/emails?provider=gmail) ---")
    try:
        response = client.get("/api/emails?provider=gmail")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Received {len(data)} emails.")
        else:
            print("FAILURE: Server returned error.")
            try:
                print("Error Details:", response.json())
            except:
                print("Raw Body:", response.text)
                
    except Exception as e:
        print(f"CLIENT CRASH: {e}")
        import traceback
        traceback.print_exc()
    print("--- Test Complete ---")

if __name__ == "__main__":
    test_request()
