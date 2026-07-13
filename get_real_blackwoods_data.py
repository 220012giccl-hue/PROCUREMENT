import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import json
import re
import time
from urllib.parse import quote_plus, urljoin
from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

DB_PATH = "agents/executive/product_database.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Referer": "https://www.google.com/",
}

def get_real_product_page_url(product_name: str) -> str:
    """Search DuckDuckGo for the product detail page on Blackwoods."""
    query = f"site:blackwoods.com.au {product_name}"
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        r = cffi_requests.get(url, headers=HEADERS, impersonate="chrome124", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # Look for result links
        links = soup.find_all("a", class_="result__url")
        for link in links:
            href = link.get("href", "")
            # Extract target URL from DuckDuckGo redirect if present
            if "/l/?" in href:
                m = re.search(r'uddg=([^&]+)', href)
                if m:
                    from urllib.parse import unquote
                    href = unquote(m.group(1))
            if "blackwoods.com.au" in href and "/p/" in href:
                return href
    except Exception as e:
        print(f"    DuckDuckGo search error: {e}")
    return ""

def get_image_from_product_page(product_url: str) -> str:
    """Fetch product detail page and extract the real main product image URL."""
    try:
        r = cffi_requests.get(product_url, headers=HEADERS, impersonate="chrome124", timeout=15)
        html = r.text
        
        # 1. Look for og:image
        og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if og:
            img = og.group(1)
            if not img.endswith("search-icon.png"):
                return img
                
        # 2. Look for zoom image / primary image elements
        soup = BeautifulSoup(html, "html.parser")
        img_tags = soup.find_all("img")
        for tag in img_tags:
            src = tag.get("src") or tag.get("data-src") or ""
            if "medias" in src and "search-icon" not in src:
                return urljoin(product_url, src)
    except Exception as e:
        print(f"    Product page fetch error: {e}")
    return ""

def main():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    products = db["products"]
    updated = 0

    print(f"Starting processing for {len(products)} products...")
    
    # We will process 5 products as a test first to make sure it works perfectly
    for i, p in enumerate(products):
        print(f"\n[{i+1}/{len(products)}] {p['name']}")
        
        # 1. Search for real product page URL
        page_url = get_real_product_page_url(p["name"])
        if page_url:
            print(f"  Found Product URL: {page_url}")
            p["source"] = page_url
            
            # 2. Fetch image from product detail page
            real_image = get_image_from_product_page(page_url)
            if real_image:
                print(f"  Found Real Image: {real_image}")
                p["image"] = real_image
                updated += 1
            else:
                print("  Failed to find real image on product page.")
        else:
            print("  Failed to find product detail page on Blackwoods.")
            
        time.sleep(2) # rate limit

    # Save DB
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print(f"\nCompleted! Updated {updated} products with real URLs and images.")

if __name__ == "__main__":
    main()
