"""
Blackwoods Real Image Extractor
Fetches each product's search page on blackwoods.com.au,
extracts the real image CDN URL, and updates product_database.json.
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import json
import re
import sys
import os
import time
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    print("[ERROR] curl_cffi not installed. Run: pip install curl-cffi")
    sys.exit(1)

DB_PATH = "agents/executive/product_database.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Referer": "https://www.blackwoods.com.au/",
}

def extract_image_from_search_html(html: str, base_url: str = "https://www.blackwoods.com.au") -> str:
    """Try multiple patterns to find a product image URL in Blackwoods HTML."""
    # Pattern 1: og:image meta tag (most reliable)
    og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if og:
        return og.group(1)

    # Pattern 2: product image in any img tag with typical CDN patterns
    patterns = [
        r'<img[^>]+src=["\']([^"\']*(?:blackwoods|hybris|scene7|akamai|cloudfront|cdn)[^"\']*(?:\.jpg|\.jpeg|\.png|\.webp))["\']',
        r'<img[^>]+src=["\']([^"\']*/_ui/[^"\']+(?:\.jpg|\.jpeg|\.png|\.webp))["\']',
        r'<img[^>]+src=["\']([^"\']+(?:product|catalogue|item)[^"\']+(?:\.jpg|\.jpeg|\.png|\.webp))["\']',
        r'"imageUrl"\s*:\s*"([^"]+)"',
        r'"image"\s*:\s*"([^"]+(?:\.jpg|\.jpeg|\.png|\.webp))"',
        r'data-src=["\']([^"\']+(?:\.jpg|\.jpeg|\.png|\.webp))["\']',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            url = m.group(1)
            if url.startswith('/'):
                url = urljoin(base_url, url)
            return url

    return ""

def get_blackwoods_product_image(query: str, product_name: str) -> str:
    """Fetch Blackwoods search page and extract first product image."""
    search_url = f"https://www.blackwoods.com.au/search?q={query.replace(' ', '+')}"
    try:
        resp = cffi_requests.get(search_url, headers=HEADERS, impersonate="chrome124", timeout=20)
        html = resp.text
        
        img = extract_image_from_search_html(html)
        if img:
            print(f"  [OK] Found image: {img[:80]}...")
            return img
        
        # Try searching in JSON blobs in page
        json_blobs = re.findall(r'\{[^{}]*"image[Uu]rl"[^{}]*\}', html)
        for blob in json_blobs:
            url_m = re.search(r'"image[Uu]rl"\s*:\s*"([^"]+)"', blob)
            if url_m:
                print(f"  [OK] Found from JSON blob: {url_m.group(1)[:80]}")
                return url_m.group(1)

        print(f"  [--] No image found in HTML for: {product_name}")
        return ""
    except Exception as e:
        print(f"  [ERR] Error fetching {search_url}: {e}")
        return ""

def main():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    products = db["products"]
    updated = 0

    for i, p in enumerate(products):
        print(f"\n[{i+1}/{len(products)}] {p['name']}")
        
        # Build targeted search from product name
        query = " ".join(p['name'].split()[:5])  # Use first 5 words for focused search
        
        real_image = get_blackwoods_product_image(query, p['name'])
        
        if real_image:
            old = p.get("image", "")
            p["image"] = real_image
            if old != real_image:
                print(f"  --> Updated image URL")
                updated += 1
        else:
            print(f"  --> Keeping existing image (no real image found)")
        
        # Respectful rate limiting
        time.sleep(1.5)

    # Save updated DB
    db["last_updated"] = "2026-07-13"
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done! Updated {updated}/{len(products)} product images with real Blackwoods CDN URLs.")
    print(f"Database saved to: {DB_PATH}")
    
    # Print summary
    print("\n--- Image URL Summary ---")
    for p in db["products"]:
        img = p.get("image", "")
        src = "real" if "blackwoods" in img or "hybris" in img or "scene7" in img else "fallback"
        print(f"  [{src}] {p['name'][:50]}: {img[:60]}...")

if __name__ == "__main__":
    main()
