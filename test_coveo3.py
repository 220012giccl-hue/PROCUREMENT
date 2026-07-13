from curl_cffi import requests as cffi_requests
import re, json

# Try to find the backendIntegrations JS file which likely has API key
r2 = cffi_requests.get('https://www.blackwoods.com.au/wro/coveo/20260611/backendIntegrations.js', impersonate='chrome124', timeout=15)
js2 = r2.text
print('backendIntegrations.js size:', len(js2))
print('First 2000 chars:')
print(js2[:2000])

api_key2 = re.findall(r'["\']xx[a-f0-9\-]{10,}["\']', js2)
org2 = re.findall(r'organizationId[^"\']{0,5}["\']([^"\']{5,30})["\']', js2)
coveo_org2 = re.findall(r'["\']([a-z0-9]{10,30})["\']', js2)
print("API keys:", api_key2[:3])
print("Org IDs:", org2[:3])
