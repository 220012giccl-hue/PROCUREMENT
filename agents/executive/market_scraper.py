"""
Market Scraper
==============
Fetches real product data from Blackwoods and Sydney Tools.
Used by the Market Assistant to show actual live results.
"""

import re
import json
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
from curl_cffi import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

TIMEOUT = 12  # seconds


def _get_fallback_image(name: str) -> str:
    """Pick a relevant image. Try Wikipedia first, then fallback to Unsplash."""
    n = name.lower()
    
    # Try fetching a real image from Wikipedia API
    try:
        from urllib.parse import quote
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={quote(name.split()[0])}"
        resp = requests.get(wiki_url, timeout=3, impersonate="chrome124")
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1" and "original" in page_info:
                    return page_info["original"]["source"]
    except Exception:
        pass

    if any(k in n for k in ["drill", "driver", "impact", "makita", "dewalt", "bosch", "milwaukee", "tool", "saw", "grinder"]):
        return "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=300&q=80"
    if any(k in n for k in ["boot", "safety shoe", "ppe", "glove", "vest", "helmet", "hard hat", "goggle"]):
        return "https://images.unsplash.com/photo-1582967788606-a171c1080cb0?auto=format&fit=crop&w=300&q=80"
    if any(k in n for k in ["bolt", "screw", "nut", "nail", "fastener", "anchor"]):
        return "https://images.unsplash.com/photo-1530124560072-aae8d56b0efe?auto=format&fit=crop&w=300&q=80"
    if any(k in n for k in ["pipe", "fitting", "valve", "pvc", "hose"]):
        return "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=300&q=80"
    if any(k in n for k in ["timber", "wood", "pine", "plywood", "mdf", "road", "concrete", "cement", "asphalt", "brick", "block", "paving", "paver", "gravel", "sand"]):
        return "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?auto=format&fit=crop&w=300&q=80"
    if any(k in n for k in ["ladder", "scaffold"]):
        return "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=300&q=80"
    if any(k in n for k in ["tape", "measure", "level", "square"]):
        return "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=300&q=80"
    return "https://images.unsplash.com/photo-1581094288338-2314dddb7ecc?auto=format&fit=crop&w=300&q=80"


def _clean_text(text: str) -> str:
    """Remove excess whitespace."""
    return re.sub(r'\s+', ' ', text).strip()


def search_blackwoods(query: str, max_results: int = 4) -> List[Dict]:
    """
    Search Blackwoods.com.au and return product cards.
    Uses their JSON search API endpoint.
    """
    products = []
    search_url = f"https://www.blackwoods.com.au/search?q={quote_plus(query)}&format=json"
    search_page_url = f"https://www.blackwoods.com.au/search?q={quote_plus(query)}"

    try:
        # Try JSON API first (Blackwoods uses AJAX-based search)
        resp = requests.get(search_url, headers=HEADERS, timeout=TIMEOUT, impersonate="chrome124")
        if resp.status_code == 200:
            try:
                data = resp.json()
                items = (
                    data.get("products", []) or
                    data.get("items", []) or
                    data.get("results", []) or
                    data.get("data", {}).get("products", [])
                )
                for item in items[:max_results]:
                    name = (
                        item.get("name") or
                        item.get("title") or
                        item.get("product_name") or ""
                    )
                    price_raw = (
                        item.get("price") or
                        item.get("sell_price") or
                        item.get("priceRange", {}).get("minimum", {}).get("final", {}).get("value") or
                        ""
                    )
                    price = f"${price_raw:.2f}" if isinstance(price_raw, (int, float)) else (str(price_raw) if price_raw else "Contact for Price")

                    sku = item.get("sku") or item.get("id") or item.get("product_id") or ""
                    url_slug = item.get("url_key") or item.get("slug") or item.get("url") or ""
                    if url_slug and not url_slug.startswith("http"):
                        product_url = f"https://www.blackwoods.com.au/{url_slug.lstrip('/')}"
                    elif url_slug:
                        product_url = url_slug
                    else:
                        product_url = search_page_url

                    image = item.get("image") or item.get("thumbnail") or item.get("img") or ""
                    if image and not image.startswith("http"):
                        image = f"https://www.blackwoods.com.au{image}"

                    brand = item.get("brand") or item.get("manufacturer") or "N/A"
                    specs = item.get("short_description") or item.get("description") or ""
                    if isinstance(specs, dict):
                        specs = specs.get("html", "") or str(specs)
                    specs = _clean_text(re.sub(r'<[^>]+>', '', str(specs)))[:200]

                    if name:
                        products.append({
                            "name": _clean_text(name),
                            "supplier": "Blackwoods",
                            "brand": _clean_text(str(brand)),
                            "price": price,
                            "specs": specs or "See website for full specifications.",
                            "source": product_url,
                            "image": image or _get_fallback_image(name),
                            "sku": str(sku),
                        })
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: scrape HTML search page
        if not products:
            products = _scrape_blackwoods_html(query, search_page_url, max_results)

    except requests.RequestException as e:
        print(f"[MarketScraper] Blackwoods fetch error: {e}")

    # Always ensure we have a valid fallback entry
    if not products:
        products.append({
            "name": f"{query} (Blackwoods)",
            "supplier": "Blackwoods",
            "brand": "N/A",
            "price": "Contact for Price",
            "specs": f"Search for '{query}' on Blackwoods for current stock and pricing.",
            "source": search_page_url,
            "image": _get_fallback_image(query),
            "sku": "",
        })

    return products


def _scrape_blackwoods_html(query: str, search_page_url: str, max_results: int) -> List[Dict]:
    """Fallback HTML scraping for Blackwoods."""
    products = []
    try:
        resp = requests.get(search_page_url, headers=HEADERS, timeout=TIMEOUT, impersonate="chrome124")
        if resp.status_code != 200:
            return products

        html = resp.text

        # Extract product JSON from page scripts (Blackwoods embeds product data in <script> tags)
        script_matches = re.findall(r'window\.__NUXT__\s*=\s*(\{.*?\});', html, re.DOTALL)
        if not script_matches:
            script_matches = re.findall(r'"products"\s*:\s*(\[.*?\])', html, re.DOTALL)

        # Try to extract structured data from JSON-LD
        jsonld_matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        for jld in jsonld_matches:
            try:
                data = json.loads(jld)
                if isinstance(data, list):
                    for d in data:
                        if d.get("@type") in ["Product", "ItemList"]:
                            _extract_jsonld_product(d, products, max_results, query)
                elif isinstance(data, dict):
                    _extract_jsonld_product(data, products, max_results, query)
            except json.JSONDecodeError:
                pass

        # Simple fallback: extract product names from HTML patterns
        if not products:
            name_matches = re.findall(r'class="[^"]*product[^"]*title[^"]*"[^>]*>\s*<[^>]+>\s*([^<]{5,80})', html)
            price_matches = re.findall(r'\$\s*(\d+[\.,]\d{2})', html)
            img_matches = re.findall(r'<img[^>]+src="([^"]*(?:product|catalog|media)[^"]*\.(?:jpg|jpeg|png|webp))"', html, re.IGNORECASE)

            for i, name in enumerate(name_matches[:max_results]):
                name = _clean_text(name)
                if len(name) < 4:
                    continue
                price = f"${price_matches[i]}" if i < len(price_matches) else "Contact for Price"
                image = img_matches[i] if i < len(img_matches) else _get_fallback_image(name)
                if image and not image.startswith("http"):
                    image = "https://www.blackwoods.com.au" + image
                products.append({
                    "name": name,
                    "supplier": "Blackwoods",
                    "brand": "N/A",
                    "price": price,
                    "specs": "See website for full specifications.",
                    "source": search_page_url,
                    "image": image or _get_fallback_image(query),
                    "sku": "",
                })

    except Exception as e:
        print(f"[MarketScraper] Blackwoods HTML scrape error: {e}")

    return products


def _extract_jsonld_product(data: dict, products: list, max_results: int, query: str):
    """Extract product from JSON-LD structured data."""
    if len(products) >= max_results:
        return
    ptype = data.get("@type", "")
    if ptype == "Product":
        name = data.get("name", "")
        offers = data.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = offers.get("price", "") or offers.get("lowPrice", "")
        currency = offers.get("priceCurrency", "AUD")
        price_str = f"${price}" if price else "Contact for Price"
        image = data.get("image", "")
        if isinstance(image, list):
            image = image[0] if image else ""
        url = data.get("url", "")
        brand = data.get("brand", {})
        if isinstance(brand, dict):
            brand = brand.get("name", "N/A")
        desc = data.get("description", "")[:200]
        if name:
            products.append({
                "name": _clean_text(name),
                "supplier": "Blackwoods",
                "brand": str(brand) or "N/A",
                "price": price_str,
                "specs": _clean_text(desc) or "See website for full specifications.",
                "source": url or f"https://www.blackwoods.com.au/search?q={quote_plus(query)}",
                "image": image or _get_fallback_image(name),
                "sku": data.get("sku", ""),
            })


def search_sydney_tools(query: str, max_results: int = 4) -> List[Dict]:
    """
    Search SydneyTools.com.au and return product cards.
    """
    products = []
    search_page_url = f"https://sydneytools.com.au/search?q={quote_plus(query)}"

    # Sydney Tools has a known search API endpoint
    api_url = f"https://sydneytools.com.au/api/search?q={quote_plus(query)}&limit={max_results}"

    try:
        resp = requests.get(api_url, headers={**HEADERS, "Accept": "application/json"}, timeout=TIMEOUT, impersonate="chrome124")
        if resp.status_code == 200:
            try:
                data = resp.json()
                items = data.get("products", []) or data.get("items", []) or data.get("results", []) or []
                for item in items[:max_results]:
                    name = item.get("name") or item.get("title") or ""
                    price_raw = item.get("price") or item.get("sell_price") or item.get("regular_price") or ""
                    if isinstance(price_raw, (int, float)):
                        price = f"${price_raw:.2f}"
                    elif str(price_raw).replace(".", "").isdigit():
                        price = f"${float(price_raw):.2f}"
                    else:
                        price = str(price_raw) if price_raw else "Contact for Price"

                    url_slug = item.get("url") or item.get("slug") or item.get("url_key") or ""
                    if url_slug and not url_slug.startswith("http"):
                        product_url = f"https://sydneytools.com.au/{url_slug.lstrip('/')}"
                    elif url_slug:
                        product_url = url_slug
                    else:
                        product_url = search_page_url

                    image = item.get("image") or item.get("thumbnail") or item.get("img") or ""
                    if image and not image.startswith("http"):
                        image = f"https://sydneytools.com.au{image}"

                    brand = item.get("brand") or item.get("manufacturer") or "N/A"
                    specs = item.get("short_description") or item.get("description") or ""
                    if isinstance(specs, dict):
                        specs = specs.get("html", "") or str(specs)
                    specs = _clean_text(re.sub(r'<[^>]+>', '', str(specs)))[:200]
                    sku = item.get("sku") or item.get("id") or ""

                    if name:
                        products.append({
                            "name": _clean_text(name),
                            "supplier": "Sydney Tools",
                            "brand": _clean_text(str(brand)),
                            "price": price,
                            "specs": specs or "See website for full specifications.",
                            "source": product_url,
                            "image": image or _get_fallback_image(name),
                            "sku": str(sku),
                        })
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: HTML scraping
        if not products:
            products = _scrape_sydney_tools_html(query, search_page_url, max_results)

    except requests.RequestException as e:
        print(f"[MarketScraper] Sydney Tools fetch error: {e}")

    if not products:
        products.append({
            "name": f"{query} (Sydney Tools)",
            "supplier": "Sydney Tools",
            "brand": "N/A",
            "price": "Contact for Price",
            "specs": f"Search for '{query}' on Sydney Tools for current stock and pricing.",
            "source": search_page_url,
            "image": _get_fallback_image(query),
            "sku": "",
        })

    return products


def _scrape_sydney_tools_html(query: str, search_page_url: str, max_results: int) -> List[Dict]:
    """Fallback HTML scraping for Sydney Tools."""
    products = []
    try:
        resp = requests.get(search_page_url, headers=HEADERS, timeout=TIMEOUT, impersonate="chrome124")
        if resp.status_code != 200:
            return products

        html = resp.text

        # JSON-LD structured data
        jsonld_matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        for jld in jsonld_matches:
            try:
                data = json.loads(jld)
                if isinstance(data, list):
                    for d in data:
                        if d.get("@type") == "Product":
                            _extract_jsonld_product_sydney(d, products, max_results, query)
                elif isinstance(data, dict) and data.get("@type") == "Product":
                    _extract_jsonld_product_sydney(data, products, max_results, query)
            except json.JSONDecodeError:
                pass

        # Simple regex fallback
        if not products:
            name_patterns = [
                r'class="[^"]*product[_-]?(?:name|title)[^"]*"[^>]*>\s*(?:<[^>]+>)?\s*([^<]{5,100})',
                r'"name"\s*:\s*"([^"]{5,100})"',
                r'<h\d[^>]*class="[^"]*product[^"]*"[^>]*>([^<]{5,80})</h\d>',
            ]
            names = []
            for pat in name_patterns:
                names = re.findall(pat, html)
                if names:
                    break

            price_matches = re.findall(r'\$\s*(\d+[\.,]\d{2})', html)
            img_matches = re.findall(r'<img[^>]+src="([^"]*(?:product|catalog|image)[^"]*\.(?:jpg|jpeg|png|webp))"', html, re.IGNORECASE)

            for i, name in enumerate(names[:max_results]):
                name = _clean_text(name)
                if len(name) < 4:
                    continue
                price = f"${price_matches[i]}" if i < len(price_matches) else "Contact for Price"
                image = img_matches[i] if i < len(img_matches) else _get_fallback_image(name)
                if image and not image.startswith("http"):
                    image = "https://sydneytools.com.au" + image
                products.append({
                    "name": name,
                    "supplier": "Sydney Tools",
                    "brand": "N/A",
                    "price": price,
                    "specs": "See website for full specifications.",
                    "source": search_page_url,
                    "image": image or _get_fallback_image(query),
                    "sku": "",
                })

    except Exception as e:
        print(f"[MarketScraper] Sydney Tools HTML scrape error: {e}")

    return products


def _extract_jsonld_product_sydney(data: dict, products: list, max_results: int, query: str):
    if len(products) >= max_results:
        return
    name = data.get("name", "")
    offers = data.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price", "") or offers.get("lowPrice", "")
    price_str = f"${price}" if price else "Contact for Price"
    image = data.get("image", "")
    if isinstance(image, list):
        image = image[0] if image else ""
    url = data.get("url", "")
    brand = data.get("brand", {})
    if isinstance(brand, dict):
        brand = brand.get("name", "N/A")
    desc = _clean_text(re.sub(r'<[^>]+>', '', data.get("description", "")))[:200]
    if name:
        products.append({
            "name": _clean_text(name),
            "supplier": "Sydney Tools",
            "brand": str(brand) or "N/A",
            "price": price_str,
            "specs": desc or "See website for full specifications.",
            "source": url or f"https://sydneytools.com.au/search?q={quote_plus(query)}",
            "image": image or _get_fallback_image(name),
            "sku": data.get("sku", ""),
        })


# ─── Local Database Search ──────────────────────────────────────────────────────

import os as _os

_DB_PATH = _os.path.join(_os.path.dirname(__file__), "product_database.json")
_product_db: list = []

def _load_db() -> list:
    """Load and cache the local product database."""
    global _product_db
    if _product_db:
        return _product_db
    try:
        with open(_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            _product_db = data.get("products", [])
            print(f"[MarketScraper] Loaded {len(_product_db)} products from local database.")
    except Exception as e:
        print(f"[MarketScraper] Could not load product database: {e}")
        _product_db = []
    return _product_db


def _score_product(product: dict, query_words: list) -> int:
    """Score a product by how many query words match its name, category, brand."""
    score = 0
    name_lower = product.get("name", "").lower()
    cats = [c.lower() for c in product.get("category", [])]
    brand_lower = product.get("brand", "").lower()
    specs_lower = product.get("specs", "").lower()

    for word in query_words:
        if len(word) < 3:
            continue
        if word in name_lower:
            score += 3          # exact word in name = highest weight
        if any(word in cat for cat in cats):
            score += 2          # matches category tag
        if word in brand_lower:
            score += 2          # brand name match
        if word in specs_lower:
            score += 1          # mentioned in specs

    return score


def search_local_database(query: str, supplier_filter: str = None, max_results: int = 4) -> list:
    """
    Search the local product_database.json using keyword scoring.
    Returns list of matching product dicts, sorted by relevance.
    supplier_filter: 'Blackwoods' | 'Sydney Tools' | None (both)
    """
    db = _load_db()
    if not db:
        return []

    # Clean and split query into individual meaningful words
    stop_words = {"the", "a", "an", "of", "for", "and", "or", "in", "on", "at",
                  "to", "is", "are", "was", "price", "cost", "buy", "give", "show",
                  "me", "i", "want", "need", "please", "get", "find", "search"}
    query_words = [w.lower() for w in re.split(r'\W+', query) if w.lower() not in stop_words and len(w) >= 2]

    if not query_words:
        return []

    print(f"[MarketScraper-DB] Searching local DB for words: {query_words}")

    scored = []
    for product in db:
        # Apply supplier filter if provided
        if supplier_filter and product.get("supplier", "").lower() != supplier_filter.lower():
            continue
        score = _score_product(product, query_words)
        if score > 0:
            scored.append((score, product))

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [p for _, p in scored[:max_results]]

    print(f"[MarketScraper-DB] Found {len(results)} matches in local database.")
    return results




BLACKWOODS_SEARCH_URLS = {
    "Blackwoods": "https://www.blackwoods.com.au/search?q={q}",
    "Bunnings": "https://www.bunnings.com.au/search/products?q={q}",
    "Sydney Tools": "https://sydneytools.com.au/search?q={q}"
}

def search_all_sources(query: str, max_per_source: int = 3) -> Dict:
    """
    Search for products. Strategy:
    0. LIVE (NEW): Playwright headless browser intercepts Coveo API — real images, live prices.
    1. LOCAL DB: Curated Blackwoods product database (instant, reliable).
    2. FALLBACK: Direct Blackwoods search links.
    """
    print(f"[MarketScraper] Searching for Blackwoods products: '{query}'")

    # ── Step 0: Playwright live scrape (real-time Coveo API interception) ──
    try:
        import subprocess
        import os
        import json
        
        script_path = os.path.join(os.path.dirname(__file__), "blackwoods_playwright_scraper.py")
        import sys
        result = subprocess.run(
            [sys.executable, "-X", "utf8", script_path, "--api", query],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            live_results = json.loads(result.stdout.strip())
            if live_results:
                # Filter for relevance to avoid Blackwoods Coveo returning irrelevant items
                query_words = [w.lower() for w in query.split() if len(w) > 2]
                filtered_results = []
                for p in live_results:
                    p_name = p.get('name', '').lower()
                    p_cat = p.get('category', '').lower()
                    # If it matches at least one keyword, keep it
                    if any(w in p_name or w in p_cat for w in query_words) or not query_words:
                        filtered_results.append(p)
                
                if filtered_results:
                    print(f"[MarketScraper] Live scrape success: {len(filtered_results)} relevant products from Blackwoods")
                    return {
                        "products": filtered_results,
                        "sources": ["Blackwoods"],
                        "blackwoods_count": len(filtered_results),
                        "sydney_tools_count": 0,
                        "query": query,
                        "source_type": "live_playwright",
                    }
                else:
                    print("[MarketScraper] Live results filtered out due to irrelevance. Falling back to local DB.")
            else:
                print("[MarketScraper] Playwright returned empty JSON array. Falling back to local DB.")
        else:
            print(f"[MarketScraper] Playwright subprocess failed or returned no output. Stderr: {result.stderr}")
    except Exception as pw_err:
        print(f"[MarketScraper] Playwright scrape skipped: {pw_err}")

    # ── Step 1: Search local database ──
    db_results = search_local_database(query, supplier_filter=None, max_results=max_per_source * 2)

    if db_results:
        sources_used = list(set(p.get("supplier") for p in db_results if p.get("supplier")))
        print(f"[MarketScraper] DB hit: Found {len(db_results)} products from {sources_used}")
        return {
            "products": db_results,
            "sources": sources_used,
            "blackwoods_count": len(db_results),
            "sydney_tools_count": 0,
            "query": query,
            "source_type": "local_database",
        }

    # ── Step 2: Fallback — build direct search links for Blackwoods ──
    print(f"[MarketScraper] No DB results. Generating direct Blackwoods search links for: '{query}'")
    
    fallback_products = []
    safe_q = quote_plus(query)
    for name, template in BLACKWOODS_SEARCH_URLS.items():
        fallback_products.append({
            "name": f"Search '{query}' on {name}",
            "supplier": name,
            "brand": "N/A",
            "price": "Contact for Price",
            "specs": f"Click 'View on Site' to search directly on {name} for '{query}'.",
            "source": template.format(q=safe_q),
            "image": "https://images.unsplash.com/photo-1581094288338-2314dddb7ecc?w=400&q=80&auto=format&fit=crop",
            "sku": "",
        })

    return {
        "products": fallback_products[:max_per_source],
        "sources": list(BLACKWOODS_SEARCH_URLS.keys())[:max_per_source],
        "blackwoods_count": len(fallback_products),
        "sydney_tools_count": 0,
        "query": query,
        "source_type": "blackwoods_fallback_links",
    }


