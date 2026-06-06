"""
unified_comparison.py — API Router for Unified AI + Vendor Quote Comparison
v3.0 — Category-aware dynamic spec comparison.

Returns merged data from ProductResult (AI market data) and SupplierQuote (vendor bids),
grouped by product category so the frontend can render different column sets per category.

Endpoints:
  GET /api/unified-comparison/list         → List all projects that have any comparison data
  GET /api/unified-comparison/{project_id} → Full unified comparison for a specific project
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from config.database import get_db
from auth.dependencies import get_current_user
from database.models import Topic, RFQ, Supplier, SupplierQuote, ProductResult

router = APIRouter(prefix="/api/unified-comparison", tags=["Unified Comparison"])


# ── Category metadata: which spec keys belong to each category ─────────────────
CATEGORY_SPEC_KEYS = {
    "Tools":              ["Brand", "Voltage", "Battery Included", "Warranty"],
    "PPE":                ["Brand", "Safety Rating", "Size Range", "Material"],
    "Building Materials": ["Category", "Material", "Size", "Pack Qty", "Compliance"],
    "Ladders":            ["Material", "Height", "Load Rating", "Compliance"],
    "Fasteners":          ["Material", "Size", "Coating", "Pack Qty", "Application"],
    "General":            ["Brand", "Specification", "Compliance"],
}

CATEGORY_ICONS = {
    "Tools":              "🔧",
    "PPE":                "🦺",
    "Building Materials": "🧱",
    "Ladders":            "🪜",
    "Fasteners":          "🔩",
    "General":            "📦",
}

CATEGORY_COLORS = {
    "Tools":              "#0369a1",
    "PPE":                "#ea580c",
    "Building Materials": "#15803d",
    "Ladders":            "#7c3aed",
    "Fasteners":          "#475569",
    "General":            "#334155",
}


# ── Helper: format a price as a display string ────────────────────────────────
def _fmt_price(price: float | None, unit: str | None = None) -> str:
    if price is None:
        return "N/A"
    s = f"${price:,.2f}"
    if unit:
        s += f" / {unit}"
    return s


def _normalize_category(cat: str | None) -> str:
    """Normalize raw category string to one of our known keys."""
    if not cat:
        return "General"
    cat_lower = cat.strip().lower()
    mapping = {
        "tools": "Tools",
        "power tools": "Tools",
        "hand tools": "Tools",
        "ppe": "PPE",
        "safety": "PPE",
        "safety equipment": "PPE",
        "building materials": "Building Materials",
        "building": "Building Materials",
        "materials": "Building Materials",
        "ladders": "Ladders",
        "access equipment": "Ladders",
        "fasteners": "Fasteners",
        "fixings": "Fasteners",
        "hardware": "Fasteners",
    }
    for key, value in mapping.items():
        if key in cat_lower:
            return value
    return "General"


# ── GET /api/unified-comparison/list ─────────────────────────────────────────
@router.get("/list")
def list_projects_with_data(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Returns all projects (Topics) that have at least one ProductResult (AI data)
    or at least one SupplierQuote (vendor quote) linked via an RFQ.
    """
    try:
        ai_project_ids = set(
            row[0] for row in
            db.query(ProductResult.topic_id)
            .filter(ProductResult.topic_id.isnot(None))
            .distinct().all()
        )

        rfq_project_ids = set(
            row[0] for row in
            db.query(RFQ.project_id)
            .join(SupplierQuote, SupplierQuote.rfq_id == RFQ.id)
            .filter(RFQ.project_id.isnot(None))
            .distinct().all()
        )

        all_project_ids = ai_project_ids | rfq_project_ids

        if not all_project_ids:
            return {"success": True, "data": []}

        projects = (
            db.query(Topic)
            .filter(Topic.id.in_(all_project_ids))
            .order_by(Topic.created_at.desc())
            .all()
        )

        data = []
        for p in projects:
            data.append({
                "project_id":        p.id,
                "project_name":      p.topic_name or "Unnamed Project",
                "project_reference": p.topic_reference or "—",
                "status":            p.status,
                "has_ai_data":       p.id in ai_project_ids,
                "has_vendor_quotes": p.id in rfq_project_ids,
            })

        return {"success": True, "data": data}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ── GET /api/unified-comparison/{project_id} ─────────────────────────────────
@router.get("/{project_id}")
def get_unified_comparison(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Returns a category-grouped unified comparison for a project.
    Each category group has:
      - spec_headers: list of dynamic column names for that category
      - icon / color: for frontend rendering
      - items: merged AI + vendor data rows
    """
    try:
        project = db.query(Topic).filter(Topic.id == project_id).first()
        if not project:
            return {"success": False, "error": "Project not found"}

        # ── 1. Load AI market data ────────────────────────────────────────────
        ai_results = (
            db.query(ProductResult)
            .filter(ProductResult.topic_id == project_id)
            .order_by(ProductResult.unit_price)
            .all()
        )

        # Group AI results by normalized item key
        ai_by_item: dict[str, list] = {}
        for r in ai_results:
            key = (r.item_name or "").strip().lower()
            ai_by_item.setdefault(key, []).append(r)

        # ── 2. Load RFQs + SupplierQuotes ────────────────────────────────────
        rfqs = (
            db.query(RFQ)
            .filter(RFQ.project_id == project_id)
            .all()
        )

        vendor_by_item: dict[str, list] = {}
        for rfq in rfqs:
            item_key = (rfq.technical_requirements or rfq.rfq_number or "").strip().lower()
            quotes = (
                db.query(SupplierQuote)
                .filter(SupplierQuote.rfq_id == rfq.id)
                .all()
            )
            for q in quotes:
                supplier = db.query(Supplier).filter(Supplier.id == q.supplier_id).first()
                vendor_name = supplier.name if supplier else f"Supplier #{q.supplier_id}"
                vendor_by_item.setdefault(item_key, []).append({
                    "vendor":          vendor_name,
                    "quoted_price":    q.quoted_price,
                    "price_display":   _fmt_price(q.quoted_price),
                    "lead_time":       q.lead_time,
                    "warranty":        q.warranty,
                    "compliance":      q.compliance_notes,
                    "status":          q.status or "PENDING",
                    "rfq_number":      rfq.rfq_number,
                    "brand":           getattr(q, 'brand', None),
                    "specs":           getattr(q, 'specs_json', {}) or {},
                })

        # ── 3. Merge items & group by category ────────────────────────────────
        all_keys = set(ai_by_item.keys()) | set(vendor_by_item.keys())
        # category_groups: category_name → list of item rows
        category_groups: dict[str, list] = {}

        for key in sorted(all_keys):
            ai_entries = ai_by_item.get(key, [])
            vendor_entries = vendor_by_item.get(key, [])

            # Determine category from the first AI result, fall back to General
            raw_category = ai_entries[0].category if ai_entries and ai_entries[0].category else "General"
            category = _normalize_category(raw_category)

            # Best AI price
            best_ai = None
            if ai_entries:
                sorted_ai = sorted(
                    [e for e in ai_entries if e.unit_price is not None],
                    key=lambda x: x.unit_price
                )
                if sorted_ai:
                    best_ai = sorted_ai[0]

            # Variance analysis
            recommended_vendor = None
            variance_note = None
            if vendor_entries and best_ai and best_ai.unit_price:
                ai_price = best_ai.unit_price
                cheapest = min(
                    [v for v in vendor_entries if v["quoted_price"] is not None],
                    key=lambda v: v["quoted_price"],
                    default=None
                )
                if cheapest:
                    diff_pct = ((cheapest["quoted_price"] - ai_price) / ai_price) * 100
                    recommended_vendor = cheapest["vendor"]
                    if diff_pct < -5:
                        variance_note = f"✅ {abs(diff_pct):.1f}% below market — great deal"
                    elif diff_pct > 10:
                        variance_note = f"⚠️ {diff_pct:.1f}% above market estimate"
                    else:
                        variance_note = f"~{diff_pct:+.1f}% vs market"

            # Display name
            display_name = (
                ai_entries[0].item_name if ai_entries
                else (vendor_entries[0]["rfq_number"] if vendor_entries else key)
            )

            # Collect all spec keys available for this item (from AI + vendors)
            all_spec_keys: set = set()
            if ai_entries:
                for ae in ai_entries:
                    specs = getattr(ae, 'specs_json', {}) or {}
                    all_spec_keys.update(specs.keys())
            for ve in vendor_entries:
                all_spec_keys.update((ve.get("specs") or {}).keys())

            item_row = {
                "item_name":          display_name,
                "category":           category,
                "has_ai":             len(ai_entries) > 0,
                "has_quotes":         len(vendor_entries) > 0,
                "ai_market_data": [
                    {
                        "supplier":      e.supplier,
                        "unit_price":    e.unit_price,
                        "unit":          e.unit,
                        "price_display": _fmt_price(e.unit_price, e.unit),
                        "source_url":    e.source_url,
                        "brand":         getattr(e, 'brand', None),
                        "image_url":     getattr(e, 'image_url', None),
                        "confidence":    getattr(e, 'confidence_level', None),
                        "best_for":      getattr(e, 'best_for', None),
                        "specs":         getattr(e, 'specs_json', {}) or {},
                    }
                    for e in ai_entries
                ],
                "best_ai_price": {
                    "supplier":      best_ai.supplier,
                    "unit_price":    best_ai.unit_price,
                    "unit":          best_ai.unit,
                    "price_display": _fmt_price(best_ai.unit_price, best_ai.unit),
                    "source_url":    best_ai.source_url,
                    "brand":         getattr(best_ai, 'brand', None),
                    "best_for":      getattr(best_ai, 'best_for', None),
                    "specs":         getattr(best_ai, 'specs_json', {}) or {},
                } if best_ai else None,
                "vendor_quotes":      vendor_entries,
                "recommended_vendor": recommended_vendor,
                "variance_note":      variance_note,
                "spec_keys":          sorted(list(all_spec_keys)),
            }

            category_groups.setdefault(category, []).append(item_row)

        # ── 4. Build final categories response ───────────────────────────────
        all_items_flat = [item for items in category_groups.values() for item in items]
        summary = {
            "project_name":             project.topic_name,
            "project_reference":        project.topic_reference,
            "total_items":              len(all_items_flat),
            "items_with_ai_data":       sum(1 for r in all_items_flat if r["has_ai"]),
            "items_with_vendor_quotes": sum(1 for r in all_items_flat if r["has_quotes"]),
            "items_fully_covered":      sum(1 for r in all_items_flat if r["has_ai"] and r["has_quotes"]),
            "total_categories":         len(category_groups),
        }

        # Build category blocks with metadata
        categories = {}
        for cat_name, items in category_groups.items():
            # Collect all unique spec keys across all items in this category
            # Use predefined order from CATEGORY_SPEC_KEYS, then append any extras
            predefined = CATEGORY_SPEC_KEYS.get(cat_name, ["Brand", "Specification"])
            extra_keys = []
            for item in items:
                for k in item.get("spec_keys", []):
                    if k not in predefined and k not in extra_keys:
                        extra_keys.append(k)
            spec_headers = predefined + extra_keys

            # Collect all unique vendor names across this category
            all_vendors = []
            for item in items:
                for vq in item.get("vendor_quotes", []):
                    if vq["vendor"] not in all_vendors:
                        all_vendors.append(vq["vendor"])

            categories[cat_name] = {
                "icon":         CATEGORY_ICONS.get(cat_name, "📦"),
                "color":        CATEGORY_COLORS.get(cat_name, "#334155"),
                "spec_headers": spec_headers,
                "vendors":      all_vendors,
                "items":        items,
            }

        return {
            "success":    True,
            "summary":    summary,
            "categories": categories,
            # Keep flat data for backward compat
            "data":       all_items_flat,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
