from curl_cffi import requests as cffi_requests
import re, json

# Look for Coveo API calls in HTML
r = cffi_requests.get('https://www.blackwoods.com.au/search?q=sheet+steel', impersonate='chrome124', timeout=15)
html = r.text

# Find Coveo API key / org ID
coveo_org = re.findall(r'organizationId["\s]*[:=]["\s]*([a-zA-Z0-9]+)', html)
coveo_api_key = re.findall(r'searchApiKey["\s]*[:=]["\s]*([a-zA-Z0-9\-]+)', html)
coveo_key2 = re.findall(r'apiKey["\s]*[:=]["\s]*"([a-zA-Z0-9\-]+)"', html)
coveo_url = re.findall(r'(https://[a-z0-9]+\.org\.coveo\.com[^"\']+)', html)
coveo_platform = re.findall(r'(https://platform\.cloud\.coveo\.com[^"\']+)', html)

print("Coveo OrgID:", coveo_org[:3])
print("Coveo search API key:", coveo_api_key[:3])
print("Coveo api key2:", coveo_key2[:3])
print("Coveo URL patterns:", coveo_url[:3])
print("Coveo platform URLs:", coveo_platform[:3])

# Also dump first 5000 chars of the script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL|re.IGNORECASE)
print(f"\nFound {len(scripts)} script tags. Searching for Coveo config...")
for i, s in enumerate(scripts):
    if 'coveo' in s.lower() and len(s) > 100:
        print(f"Script {i} ({len(s)} chars):", s[:600])
        print("---")
