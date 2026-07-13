"""
blackwoods_playwright_scraper.py
=================================
Live dynamic scraper for Blackwoods.com.au using Playwright.
Intercepts Coveo search API network responses to get:
 - Real product names, brands, SKUs
 - Exact live prices (ec_price)
 - Real Blackwoods CDN image URLs (ec_images / ec_image)
 - Direct product page URLs

This module is imported by market_scraper.py as Layer 0 (highest priority).
Falls back gracefully if Playwright is unavailable or times out.
"""

import json
import time
from urllib.parse import quote_plus
from typing import List, Dict, Optional


def _normalize_image(img_raw) -> str:
    """Extract a usable image URL from ec_images or ec_image fields."""
    if not img_raw:
        return ""
    
    # ec_images is sometimes a JSON-encoded list string
    if isinstance(img_raw, str):
        # Try parse as JSON array
        if img_raw.startswith("["):
            try:
                arr = json.loads(img_raw)
                if arr and isinstance(arr, list):
                    first = arr[0]
                    # Each element might be a dict with 'src' key
                    if isinstance(first, dict):
                        return first.get("src", "") or first.get("url", "") or ""
                    return str(first)
            except Exception:
                pass
        # Try parse as JSON object
        if img_raw.startswith("{"):
            try:
                obj = json.loads(img_raw)
                return obj.get("src", "") or obj.get("url", "") or ""
            except Exception:
                pass
        return img_raw  # Plain string URL
    
    if isinstance(img_raw, list):
        if img_raw:
            first = img_raw[0]
            if isinstance(first, dict):
                return first.get("src", "") or first.get("url", "") or str(first)
            return str(first)
    
    if isinstance(img_raw, dict):
        return img_raw.get("src", "") or img_raw.get("url", "") or ""
    
    return str(img_raw)


def _extract_products_from_coveo(coveo_data: dict, query: str, max_results: int = 6) -> List[Dict]:
    """Parse Coveo search API response JSON into our product dict format."""
    products = []
    results = coveo_data.get("results", [])
    
    for item in results[:max_results]:
        raw = item.get("raw", {})
        
        name = (
            item.get("title", "") or
            raw.get("ec_name", "") or
            raw.get("title", "")
        ).strip()
        
        if not name:
            continue
        
        # Price
        price_raw = raw.get("ec_price") or raw.get("price")
        if price_raw:
            try:
                price_str = f"AUD ${float(price_raw):.2f}"
            except (TypeError, ValueError):
                price_str = str(price_raw)
        else:
            price_str = "Contact for Price"
        
        # Image — Coveo uses ec_images (array) or ec_image (string)
        img = _normalize_image(raw.get("ec_images") or raw.get("ec_image") or raw.get("image", ""))
        
        # Ensure full URL
        if img and img.startswith("//"):
            img = "https:" + img
        
        # SKU
        sku = raw.get("ec_sku") or raw.get("sku", "")
        
        # Brand
        brand = raw.get("ec_brand") or raw.get("brand", "N/A")
        
        # Product page URL
        source_url = item.get("clickUri") or item.get("uri") or ""
        if source_url.startswith("product://"):
            # Coveo returns internal URIs sometimes, convert to search fallback
            source_url = f"https://www.blackwoods.com.au/search?q={quote_plus(query)}"
        elif source_url and not source_url.startswith("http"):
            if not source_url.startswith("/"):
                source_url = "/" + source_url
            source_url = "https://www.blackwoods.com.au" + source_url
        
        if not source_url:
            source_url = f"https://www.blackwoods.com.au/search?q={quote_plus(query)}"
        
        # Category / specs
        category = raw.get("ec_category", "") or raw.get("category", "")
        if isinstance(category, list):
            category = " > ".join(category)
        
        desc = raw.get("ec_shortdescription") or raw.get("ec_description") or category or "See website for full specifications."
        if isinstance(desc, list):
            desc = " ".join(desc)
        desc = str(desc)[:300]
        
        products.append({
            "name": name,
            "supplier": "Blackwoods",
            "brand": str(brand) if brand else "N/A",
            "price": price_str,
            "specs": desc,
            "source": source_url,
            "image": img,
            "sku": str(sku) if sku else "",
        })
    
    return products


def scrape_blackwoods_live(query: str, max_results: int = 6, timeout_ms: int = 20000) -> List[Dict]:
    """
    Use Playwright with system-installed Chrome or Edge to load Blackwoods search page,
    intercept Coveo API network response, and return live product data.
    
    Returns empty list if Playwright is unavailable or times out.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        print("[PlaywrightScraper] playwright not installed. Skipping live scrape.")
        return []
    
    url = f"https://www.blackwoods.com.au/search?q={quote_plus(query)}"
    print(f"[PlaywrightScraper] Starting live scrape for: '{query}'")
    print(f"[PlaywrightScraper] URL: {url}")
    
    captured_products = []
    
    # Detect system browser paths (Windows)
    import os
    browser_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    system_browser = next((p for p in browser_paths if os.path.exists(p)), None)
    
    if not system_browser:
        print("[PlaywrightScraper] No system Chrome/Edge found. Skipping live scrape.")
        return []
    
    print(f"[PlaywrightScraper] Using system browser: {system_browser}")
    
    try:
        with sync_playwright() as p:
            # Use system Chrome/Edge via channel or executable path
            is_edge = "msedge" in system_browser.lower()
            
            if is_edge:
                browser = p.chromium.launch(
                    channel="msedge",
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ]
                )
            else:
                browser = p.chromium.launch(
                    executable_path=system_browser,
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ]
                )
            
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="en-AU",
            )
            
            # Anti-detection script
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-AU', 'en']});
            """)
            
            page = context.new_page()
            
            # Intercept API responses
            def handle_response(response):
                if captured_products:  # Already got data, skip
                    return
                resp_url = response.url.lower()
                
                # Skip static assets to reduce noise
                if any(x in resp_url for x in [".jpg", ".png", ".svg", ".css", ".js", ".gif", "google", "clarity", "akstat"]):
                    return
                
                try:
                    if response.status == 200:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            data = response.json()
                            print(f"[DEBUG] JSON Intercepted: {resp_url}")
                            print(f"        Keys: {list(data.keys())[:10]}")
                            
                            # Check if this JSON contains our products
                            if "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
                                print(f"[DEBUG] FOUND RESULTS IN: {resp_url}")
                                products = _extract_products_from_coveo(data, query, max_results)
                                if products:
                                    captured_products.extend(products)
                                    print(f"[PlaywrightScraper] Intercepted Data: {len(products)} products found!")
                except Exception:
                    pass
            
            page.on("response", handle_response)
            
            try:
                # Navigate to search page
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                
                # Wait for products to load — give JS time to fire Coveo API
                deadline = time.time() + 12  # 12 seconds max wait
                while time.time() < deadline:
                    if captured_products:
                        break
                    page.wait_for_timeout(500)
                
                if not captured_products:
                    # Extra wait if still nothing
                    page.wait_for_timeout(3000)
                
            except PlaywrightTimeout:
                print(f"[PlaywrightScraper] Page load timed out — returning what we captured so far.")
            
            browser.close()
            
    except Exception as e:
        print(f"[PlaywrightScraper] Error during live scrape: {e}")
        return []
    
    print(f"[PlaywrightScraper] Completed. Total products captured: {len(captured_products)}")
    return captured_products[:max_results]


if __name__ == "__main__":
    import sys
    import json as json_lib
    
    args = sys.argv[1:]
    api_mode = "--api" in args
    if api_mode:
        args.remove("--api")
        # Suppress prints by redefining print temporarily
        import builtins
        original_print = builtins.print
        builtins.print = lambda *a, **k: None
    
    q = " ".join(args) if args else "safety boots"
    
    if not api_mode:
        print(f"\nTesting live scrape for: '{q}'\n" + "="*50)
        
    results = scrape_blackwoods_live(q, max_results=5)
    
    if api_mode:
        # Restore print and output json
        builtins.print = original_print
        print(json_lib.dumps(results))
    else:
        if results:
            for i, p in enumerate(results, 1):
                print(f"\n{i}. {p['name']}")
                print(f"   Brand : {p['brand']}")
                print(f"   Price : {p['price']}")
                print(f"   SKU   : {p['sku']}")
                print(f"   Image : {p['image'][:80]}..." if len(p['image']) > 80 else f"   Image : {p['image']}")
                print(f"   URL   : {p['source'][:80]}...")
        else:
            print("No products found. Playwright may need chromium install.")
            print("Run: playwright install chromium")
