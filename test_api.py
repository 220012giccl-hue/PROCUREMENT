import requests
import json

BASE = "http://127.0.0.1:8069"

# Test 1: sheet steel query
print("=" * 60)
print("TEST 1: 'sheet steel'")
r = requests.post(f"{BASE}/api/assistant/chat", json={
    "message": "gave me price of sheet steel",
    "assistant_type": "market",
    "conversation_id": "test-001"
}, timeout=60)
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    reply = data.get("response", data.get("reply", ""))
    print("Reply length:", len(reply))
    print("Reply preview:", reply[:400])
else:
    print("Error:", r.text[:300])
