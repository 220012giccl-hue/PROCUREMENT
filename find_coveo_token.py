"""
Find Coveo API credentials from Blackwoods JS files.
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import re
from curl_cffi import requests as cffi_requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.blackwoods.com.au/",
}

KEY_JS_FILES = [
    "https://www.blackwoods.com.au/wro/coveo/20260611/initializer-core.js",
    "https://www.blackwoods.com.au/wro/coveo/20260611/backendIntegrations.js",
    "https://www.blackwoods.com.au/wro/coveo/20260611/atomicUtils.js",
    "https://www.blackwoods.com.au/searchAssets/assets/05062026_PROD_SLP_001/coveo-custom-components-v3.esm.js",
]

def search_file(url):
    print(f"\n[Fetching] {url}")
    try:
        r = cffi_requests.get(url, headers=HEADERS, impersonate="chrome124", timeout=20)
        text = r.text
        print(f"  Size: {len(text)} chars")

        # Broad patterns for Coveo credentials
        results = {}

        # Organization ID patterns
        org_patterns = [
            r'organizationId["\s]*[:=,]\s*["\']([a-zA-Z0-9_\-]{5,50})["\']',
            r'"org(?:anization)?[Ii]d"\s*:\s*"([^"]{5,50})"',
            r'orgid["\s]*=\s*["\']([^"\']{5,50})["\']',
            r'ORGANIZATION_?ID\s*[:=]\s*["\']([^"\']{5,50})["\']',
            r'organizationId:\s*["\']([^"\']{5,50})["\']',
        ]
        for pat in org_patterns:
            m = re.findall(pat, text, re.IGNORECASE)
            if m:
                results['orgId'] = m
                print(f"  [ORG] {m}")

        # Access token patterns
        token_patterns = [
            r'accessToken["\s]*[:=,]\s*["\']([a-zA-Z0-9_\-\.]{20,100})["\']',
            r'access[_-]?token["\s]*[:=,]\s*["\']([^"\']{20,100})["\']',
            r'apiKey["\s]*[:=,]\s*["\']([^"\']{20,100})["\']',
            r'bearerToken["\s]*[:=,]\s*["\']([^"\']{20,100})["\']',
        ]
        for pat in token_patterns:
            m = re.findall(pat, text, re.IGNORECASE)
            if m:
                results['token'] = m
                print(f"  [TOKEN] {m[:2]}")

        # Pipeline / source patterns (helps with search API call)
        pipe_patterns = [
            r'pipeline["\s]*[:=,]\s*["\']([^"\']{2,50})["\']',
            r'searchHub["\s]*[:=,]\s*["\']([^"\']{2,50})["\']',
        ]
        for pat in pipe_patterns:
            m = re.findall(pat, text, re.IGNORECASE)
            if m:
                print(f"  [PIPE/HUB] {m[:3]}")

        if not results:
            print("  [--] Nothing useful found")

        return results
    except Exception as e:
        print(f"  [ERR] {e}")
        return {}

# Also check main HTML page for inline config
def check_main_html():
    print("\n[Fetching main search page HTML]")
    r = cffi_requests.get("https://www.blackwoods.com.au/search?q=drill", headers=HEADERS, impersonate="chrome124", timeout=20)
    html = r.text
    print(f"  Size: {len(html)} chars")
    
    # Look for inline JSON config blocks
    # Coveo often embeds config in window.__coveo or similar
    config_patterns = [
        r'window\.__coveo\s*=\s*(\{[^;]+\})',
        r'CoveoForSitecoreSettings\s*=\s*(\{[^;]+\})',
        r'"accessToken"\s*:\s*"([^"]{20,})"',
        r'"organizationId"\s*:\s*"([^"]{5,50})"',
        r'atomic-search-interface[^>]+access-token="([^"]+)"',
        r'atomic-search-interface[^>]+organization-id="([^"]+)"',
        r'data-organization-id="([^"]+)"',
        r'data-access-token="([^"]+)"',
        r'<atomic-search-interface([^>]+)>',
    ]
    for pat in config_patterns:
        m = re.findall(pat, html, re.IGNORECASE | re.DOTALL)
        if m:
            print(f"  [FOUND] Pattern '{pat[:40]}': {str(m)[:200]}")

if __name__ == "__main__":
    for url in KEY_JS_FILES:
        search_file(url)
    check_main_html()
    print("\nDone.")
