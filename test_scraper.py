"""Quick test for market scraper"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.executive.market_scraper import search_all_sources

result = search_all_sources("hammer drill", max_per_source=2)

print(f"Total products found: {len(result['products'])}")
print(f"Sources: {result['sources']}")
print(f"Blackwoods: {result['blackwoods_count']}, Sydney Tools: {result['sydney_tools_count']}")
print()

for p in result["products"]:
    print(f"  [{p['supplier']}] {p['name']}")
    print(f"    Price: {p['price']}")
    print(f"    Brand: {p['brand']}")
    print(f"    URL: {p['source'][:80]}")
    print(f"    Image: {p['image'][:80]}")
    print()
