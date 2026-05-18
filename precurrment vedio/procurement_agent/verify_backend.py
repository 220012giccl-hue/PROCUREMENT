import requests
import json

url = "http://localhost:5001/api/assistant/chat"
payload = {
    "question": "What is Python?",
    "chat_history": []
}

print(f"Testing internal API at: {url}")
try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        data = response.json()
        print(f"\nSUCCESS! AI Response: {data.get('response')}")
    else:
        print(f"\nFAILED with status {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
