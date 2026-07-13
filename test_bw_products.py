from curl_cffi import requests as cffi_requests
import re, json

# Try Blackwoods product search with known SKU pattern
test_products = [
    "https://www.blackwoods.com.au/search?q=steel+plate",
    "https://www.blackwoods.com.au/search?q=safety+boots",
    "https://www.blackwoods.com.au/search?q=power+drill",
    "https://www.blackwoods.com.au/search?q=scaffolding",
]

for url in test_products:
    r = cffi_requests.get(url, impersonate='chrome124', timeout=15)
    html = r.text
    
    # Look for any product detail link pattern like /p/XXXXXX
    product_links = re.findall(r'href="(/p/[a-zA-Z0-9\-]+)"', html)
    # Look for image URLs
    images = re.findall(r'src="(https://[^"]*(?:blackwoods|media|cdn)[^"]*\.(?:jpg|jpeg|png|webp))"', html, re.IGNORECASE)
    # Look for any JSON product data
    product_json = re.findall(r'ec_name["\s]*:\s*["\']([^"\']+)["\']', html)
    ec_price = re.findall(r'ec_price["\s]*:\s*([0-9.]+)', html)
    ec_image = re.findall(r'ec_images["\s]*:\s*["\']([^"\']+)["\']', html)
    ec_sku = re.findall(r'ec_sku["\s]*:\s*["\']([^"\']+)["\']', html)
    
    print(f"\nQuery: {url.split('q=')[1]}")
    print(f"Product links: {product_links[:3]}")
    print(f"Product images: {images[:2]}")
    print(f"ec_name: {product_json[:3]}")
    print(f"ec_price: {ec_price[:3]}")
    print(f"ec_sku: {ec_sku[:3]}")
    print(f"ec_images: {ec_image[:3]}")
