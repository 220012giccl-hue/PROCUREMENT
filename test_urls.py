from curl_cffi import requests as cffi_requests
import re, json

# Try to directly access a known Blackwoods product category page 
# to get real product URLs, images, and prices
urls_to_test = [
    "https://www.blackwoods.com.au/structural-steel",
    "https://www.blackwoods.com.au/api/2.0/catalog/category/products?page=1&pageSize=10&categoryCode=steel",
    "https://www.blackwoods.com.au/p/structural-steel",
]

for url in urls_to_test:
    r = cffi_requests.get(url, impersonate='chrome124', timeout=10)
    print(f"\nURL: {url}")
    print(f"Status: {r.status_code}")
    print(f"Content type: {r.headers.get('content-type','')}")
    if r.status_code == 200:
        txt = r.text[:300]
        print(f"Content preview: {txt}")
