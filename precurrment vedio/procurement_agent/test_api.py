import requests
import json

url = "https://ai.gcucsstudent.site/api/chat"
payload = {
    "model": "ai-agent",
    "messages": [
        {"role": "user", "content": "hi"}
    ],
    "stream": False,
    "format": "json"
}

print(f"Testing API at: {url}")
try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        data = response.json()
        if 'message' in data and 'content' in data['message']:
            print(f"\nSUCCESS! Content: {data['message']['content']}")
        else:
            print("\nResponse format unexpected.")
except Exception as e:
    print(f"Error: {e}")
