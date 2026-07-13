from curl_cffi import requests

try:
    print("Testing Blackwoods...")
    r = requests.get("https://www.blackwoods.com.au/search?q=doors&format=json", impersonate="chrome124", timeout=15)
    print("Blackwoods Status:", r.status_code)
    print("Blackwoods content snippet:", r.text[:200])
except Exception as e:
    print("Blackwoods failed:", e)

try:
    print("\nTesting Sydney Tools API...")
    r2 = requests.get("https://sydneytools.com.au/api/search?q=doors&limit=2", impersonate="chrome124", timeout=15)
    print("Sydney Tools API Status:", r2.status_code)
    print("Sydney Tools API content snippet:", r2.text[:200])
except Exception as e:
    print("Sydney Tools API failed:", e)

try:
    print("\nTesting Sydney Tools HTML...")
    r3 = requests.get("https://sydneytools.com.au/search?q=doors", impersonate="chrome124", timeout=15)
    print("Sydney Tools HTML Status:", r3.status_code)
    print("Sydney Tools HTML content length:", len(r3.text))
except Exception as e:
    print("Sydney Tools HTML failed:", e)
