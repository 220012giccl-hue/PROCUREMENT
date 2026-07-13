import sys
import os
import json
from datetime import datetime, timedelta
import random

# Fix Windows console Unicode issue
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal, init_db
from database.models import (
    ProcurementItem, ProductComparison, Supplier
)

db = SessionLocal()

def seed_missing_data():
    print("Seeding missing dummy data for UI pages...")

    # Load product_database.json
    json_path = os.path.join("agents", "executive", "product_database.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get("products", [])
    except Exception as e:
        print(f"Failed to load product_database.json: {e}")
        products = []

    # 1. Seed Suppliers (ui/suppliers.html)
    print("1. Seeding Suppliers...")
    suppliers_set = set(p.get("supplier") for p in products if p.get("supplier"))
    supplier_map = {}
    for s_name in suppliers_set:
        existing = db.query(Supplier).filter(Supplier.name == s_name).first()
        if not existing:
            supplier = Supplier(
                name=s_name,
                categories="General, Fasteners, Tools",
                rating=random.uniform(3.5, 5.0),
                email=f"sales@{s_name.lower().replace(' ', '')}.com",
                phone="1300 " + str(random.randint(100000, 999999))
            )
            db.add(supplier)
            db.flush()
            supplier_map[s_name] = supplier.id
        else:
            supplier_map[s_name] = existing.id
    db.commit()

    # 2. Seed Procurement Items (ui/procurement.html)
    print("2. Seeding Procurement Items...")
    for i, p in enumerate(products[:50]): # Insert 50 products
        existing = db.query(ProcurementItem).filter(ProcurementItem.item_name == p.get("name")).first()
        if not existing:
            item = ProcurementItem(
                item_name=p.get("name"),
                category=", ".join(p.get("category", [])),
                quantity=str(random.randint(10, 500)),
                status=random.choice(["RESEARCHING", "RFQ_NEEDED", "ORDERED"]),
                technical_notes=p.get("specs", ""),
                source_url=p.get("source", ""),
                supplier_id=supplier_map.get(p.get("supplier"))
            )
            db.add(item)
    db.commit()

    # 3. Seed Product Comparisons (ui/comparison.html)
    print("3. Seeding Product Comparisons...")
    if db.query(ProductComparison).count() == 0:
        comparisons = [
            {
                "title": "Safety Boots Comparison (Q3)",
                "category": "PPE",
                "products": [
                    {"id": 1, "name": "Oliver AT 55 Series", "supplier_name": "Blackwoods"},
                    {"id": 2, "name": "Steel Blue Argyle", "supplier_name": "Sydney Tools"}
                ],
                "table_data": {
                    "Price": {"1": "$189.00", "2": "$195.00"},
                    "Lead Time": {"1": "In Stock", "2": "2 Days"},
                    "Compliance": {"1": "AS/NZS 2210.3", "2": "AS/NZS 2210.3"}
                },
                "recommendation": "Oliver AT 55 Series is recommended due to immediate availability and slightly better pricing.",
                "confidence_level": "High"
            },
            {
                "title": "Drill Driver 18V Tender",
                "category": "Power Tools",
                "products": [
                    {"id": 1, "name": "DeWalt DCD771C2", "supplier_name": "Blackwoods"},
                    {"id": 2, "name": "Makita DDF482Z", "supplier_name": "Sydney Tools"}
                ],
                "table_data": {
                    "Price": {"1": "$199.00", "2": "$149.00 (Skin Only)"},
                    "Battery Included": {"1": "Yes (2x 1.5Ah)", "2": "No"},
                    "Torque": {"1": "42Nm", "2": "62Nm"}
                },
                "recommendation": "DeWalt is better value if batteries are required. Makita offers higher torque if we already have 18V LXT batteries on site.",
                "confidence_level": "Medium"
            }
        ]
        
        for c_data in comparisons:
            comp = ProductComparison(
                title=c_data["title"],
                category=c_data["category"],
                products_json=c_data["products"],
                comparison_table_json=c_data["table_data"],
                recommendation=c_data["recommendation"],
                missing_info_json=["Bulk discount rates"],
                confidence_level=c_data["confidence_level"]
            )
            db.add(comp)
        db.commit()

    print("Missing data seeded successfully.")

if __name__ == "__main__":
    seed_missing_data()
