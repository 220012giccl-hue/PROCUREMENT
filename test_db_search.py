import sys
sys.path.insert(0, '.')
from agents.executive.market_scraper import search_all_sources

tests = ['sheet steel', 'drill', 'safety boots', 'pvc pipe', 'scaffold', 'road', 'concrete', 'hammer drill']
for q in tests:
    res = search_all_sources(q)
    products = res['products']
    src = res.get('source_type', 'unknown')
    print(f"\nQuery: '{q}' -> {len(products)} results [{src}]")
    for p in products[:2]:
        print(f"  - {p['name'][:50]} | {p['price']} | {p['supplier']}")
