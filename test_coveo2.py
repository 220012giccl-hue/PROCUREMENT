from curl_cffi import requests as cffi_requests
import re, json

# Fetch the atomicUtils JS file to find Coveo API key and orgId
r = cffi_requests.get('https://www.blackwoods.com.au/wro/coveo/20260611/atomicUtils.js', impersonate='chrome124', timeout=15)
js = r.text
print('atomicUtils.js size:', len(js))

# Find API key
api_key = re.findall(r'["\']?(xx[a-f0-9\-]{20,})["\']?', js)
access_token = re.findall(r'accessToken["\s]*[:=]["\s]*(["\'][^"\']+["\'])', js)
org_id = re.findall(r'organizationId["\s]*[:=]["\s]*(["\'][^"\']+["\'])', js)

print("API keys found:", api_key[:3])
print("Access tokens:", access_token[:3])
print("Org IDs:", org_id[:3])

# Also check for platform URL
platform_url = re.findall(r'https://[^"\']*coveo[^"\']{5,50}', js)
print("Coveo URLs:", platform_url[:5])

# Print first 1000 chars
print("\nFirst 1000 chars of atomicUtils.js:")
print(js[:1000])
