from curl_cffi import requests as cffi_requests
import re
from urllib.parse import urljoin

# Fetch the main search page
url = "https://www.blackwoods.com.au/search?q=drill"
r = cffi_requests.get(url, impersonate="chrome124", timeout=15)
html = r.text

# Extract all script tags with src
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
print(f"Found {len(scripts)} external scripts.")

# Search inside scripts
for s in scripts:
    js_url = urljoin(url, s)
    try:
        js_r = cffi_requests.get(js_url, impersonate="chrome124", timeout=10)
        js_text = js_r.text
        if "organizationid" in js_text.lower() or "token" in js_text.lower() or "coveo" in js_text.lower():
            print(f"\n--- Matching Script: {js_url} ---")
            # Extract possible API keys
            keys = re.findall(r'[\x22\x27](xx[a-zA-Z0-9\-]{20,})[\x22\x27]', js_text)
            orgs = re.findall(r'organizationId["\s]*:?["\s]*[:=]["\s]*["\']([^"\']+)["\']', js_text, re.IGNORECASE)
            tokens = re.findall(r'accessToken["\s]*:?["\s]*[:=]["\s]*["\']([^"\']+)["\']', js_text, re.IGNORECASE)
            print("Keys:", keys)
            print("Orgs:", orgs)
            print("Tokens:", tokens)
    except Exception as e:
        print(f"Error fetching {js_url}: {e}")
