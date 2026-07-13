from curl_cffi import requests as cffi_requests
import re, json

r = cffi_requests.get('https://www.blackwoods.com.au/search?q=sheet+steel', impersonate='chrome124', timeout=15)
html = r.text
print('Status:', r.status_code)
print('Total HTML size:', len(html))

# Check JSON-LD
jsonld = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL|re.IGNORECASE)
print('JSON-LD blocks found:', len(jsonld))
if jsonld:
    for j in jsonld[:2]:
        print('JSON-LD snippet:', j[:400])
        print('---')

# Check for price 
prices = re.findall(r'\$\s*(\d+[\.,]\d{2})', html)
print('Prices found:', prices[:5])

# Check for product images
imgs = re.findall(r'<img[^>]+src="([^"]*(?:product|catalog|media|cdn|blackwoods)[^"]*\.(jpg|jpeg|png|webp))"', html, re.IGNORECASE)
print('Product images found:', [i[0] for i in imgs[:3]])

# Check window.__data or similar
data_chunks = re.findall(r'window\.__(?:data|INITIAL_STATE|nuxt|catalog|products)\s*=\s*(\{.{50})', html)
print('Window data objects:', data_chunks[:2])

# Product title patterns
title_patterns = re.findall(r'"name"\s*:\s*"([^"]{5,80})"', html)
print('JSON name fields:', title_patterns[:5])

# Offer / price patterns in JSON
offer_patterns = re.findall(r'"price"\s*:\s*"?(\d+\.?\d*)"?', html)
print('JSON price fields:', offer_patterns[:5])
