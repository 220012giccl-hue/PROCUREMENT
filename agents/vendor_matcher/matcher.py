"""
Vendor Matcher Agent — PRD v2.1
================================
Given a list of procurement items with categories, finds matching
suppliers from the existing `suppliers` table.

Returns: [{item, matched_suppliers: [{id, name, email, categories}]}]

DO NOT MODIFY existing agents. This file is standalone.
"""
import logging
from config.database import SessionLocal
from database.models import Supplier

logger = logging.getLogger(__name__)

# Supplier priority map (from PRD — public demo catalogue sources)
DEMO_SUPPLIER_PRIORITY = {
    "Tools":            ["Sydney Tools", "Bunnings"],
    "Power Tools":      ["Sydney Tools", "Bunnings"],
    "Building":         ["Bunnings", "Bunnings Trade"],
    "Hardware":         ["Bunnings", "Bunnings Trade"],
    "PPE":              ["Blackwoods", "Bunnings"],
    "Safety":           ["Blackwoods", "Bunnings"],
    "Lifting":          ["Blackwoods", "Sydney Tools"],
    "Rigging":          ["Blackwoods", "Sydney Tools"],
    "Welding":          ["Blackwoods", "Sydney Tools", "Bunnings"],
    "Abrasives":        ["Blackwoods", "Sydney Tools", "Bunnings"],
    "Timber":           ["Bunnings", "Bunnings Trade"],
    "Concrete":         ["Bunnings", "Bunnings Trade"],
    "Paint":            ["Bunnings"],
    "Fasteners":        ["Bunnings", "Bunnings Trade"],
}


def match_vendors(items: list) -> list:
    """
    Main entry point.
    
    Args:
        items: list of dicts like [{"item_name": "Safety Boots", "category": "PPE"}, ...]
    
    Returns:
        list of dicts: [{"item": "Safety Boots", "matched_suppliers": [...]}]
    """
    db = SessionLocal()
    try:
        results = []

        for item in items:
            item_name = item.get("item_name", "")
            category  = item.get("category", "").strip()

            matched = _find_suppliers_by_category(db, category)

            results.append({
                "item":              item_name,
                "category":          category,
                "matched_suppliers": matched
            })

            logger.info(
                f"[VendorMatcher] '{item_name}' ({category}) → "
                f"{len(matched)} supplier(s) matched"
            )

        return results

    except Exception as e:
        logger.error(f"[VendorMatcher] Error: {e}")
        return []
    finally:
        db.close()


def _find_suppliers_by_category(db, category: str) -> list:
    """
    Queries the existing suppliers table for suppliers whose categories
    field contains the given category (case-insensitive substring match).
    Falls back to demo suppliers if DB has none.
    """
    matched = []

    if category:
        suppliers = db.query(Supplier).filter(
            Supplier.categories.ilike(f"%{category}%")
        ).all()

        for s in suppliers:
            matched.append({
                "id":         s.id,
                "name":       s.name,
                "email":      s.email or "",
                "phone":      s.phone or "",
                "website":    s.website or "",
                "categories": s.categories or ""
            })

    # If no suppliers found in DB, use demo priority list as fallback
    if not matched:
        matched = _get_demo_fallback(category)

    return matched


def _get_demo_fallback(category: str) -> list:
    """
    Returns demo supplier names from the PRD priority map.
    Used when the suppliers table has no entries for this category.
    """
    fallback_names = []
    for key, names in DEMO_SUPPLIER_PRIORITY.items():
        if key.lower() in category.lower() or category.lower() in key.lower():
            fallback_names.extend(names)

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for name in fallback_names:
        if name not in seen:
            seen.add(name)
            unique.append(name)

    return [
        {"id": None, "name": n, "email": "", "phone": "", "website": "", "categories": category}
        for n in unique
    ]
