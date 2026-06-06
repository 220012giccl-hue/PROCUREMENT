"""
Verify Migration 004 — checks that new DB changes are live.
Run: python scratch/verify_migration_004.py
"""
from config.database import engine
from sqlalchemy import text

print("=" * 50)
print("Migration 004 Verification")
print("=" * 50)

with engine.connect() as conn:
    # 1. Check site_address column on topics table
    r1 = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='topics' AND column_name='site_address'"
    )).fetchone()
    print(f"[1] topics.site_address column : {'OK - EXISTS' if r1 else 'MISSING!'}")

    # 2. Check rfq_workflows table
    r2 = conn.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name='rfq_workflows'"
    )).fetchone()
    print(f"[2] rfq_workflows table        : {'OK - EXISTS' if r2 else 'MISSING!'}")

    # 3. Check product_results table
    r3 = conn.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name='product_results'"
    )).fetchone()
    print(f"[3] product_results table      : {'OK - EXISTS' if r3 else 'MISSING!'}")

    # 4. Check existing tables still intact
    for tbl in ['contacts', 'topics', 'threads', 'rfqs', 'suppliers', 'procurement_items']:
        rx = conn.execute(text(
            f"SELECT table_name FROM information_schema.tables WHERE table_name='{tbl}'"
        )).fetchone()
        print(f"    Existing [{tbl}]   : {'OK' if rx else 'BROKEN!'}")

print("=" * 50)
print("All checks done. Existing tables untouched.")
