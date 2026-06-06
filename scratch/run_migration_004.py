"""
Run Migration 004 — safely applies all 3 DB changes.
Usage: python -m scratch.run_migration_004
"""
from config.database import engine, SessionLocal
from sqlalchemy import text

print("=" * 55)
print("Running Migration 004")
print("=" * 55)

migrations = [
    {
        "name": "Add site_address to topics table",
        "sql": "ALTER TABLE topics ADD COLUMN IF NOT EXISTS site_address TEXT"
    },
    {
        "name": "Create rfq_workflows table",
        "sql": """CREATE TABLE IF NOT EXISTS rfq_workflows (
    id               SERIAL PRIMARY KEY,
    topic_id         INT REFERENCES topics(id) ON DELETE SET NULL,
    thread_id        INT REFERENCES threads(id) ON DELETE SET NULL,
    status           VARCHAR(100) DEFAULT 'ingested',
    confidence_score FLOAT,
    assigned_by      VARCHAR(100) DEFAULT 'ai',
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
)"""
    },
    {
        "name": "Create product_results table",
        "sql": """CREATE TABLE IF NOT EXISTS product_results (
    id           SERIAL PRIMARY KEY,
    topic_id     INT REFERENCES topics(id) ON DELETE SET NULL,
    item_name    TEXT NOT NULL,
    supplier     TEXT,
    unit_price   NUMERIC(10, 2),
    unit         VARCHAR(50),
    source_url   TEXT,
    fetched_at   TIMESTAMP DEFAULT NOW()
)"""
    }
]

with engine.connect() as conn:
    for m in migrations:
        try:
            conn.execute(text(m["sql"]))
            conn.commit()
            print(f"  [OK] {m['name']}")
        except Exception as e:
            print(f"  [ERR] {m['name']}: {e}")

print()
print("Verifying results...")
with engine.connect() as conn:
    r1 = conn.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='topics' AND column_name='site_address'"
    )).fetchone()
    print(f"  topics.site_address  : {'OK - EXISTS' if r1 else 'STILL MISSING!'}")

    r2 = conn.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_name='rfq_workflows'"
    )).fetchone()
    print(f"  rfq_workflows table  : {'OK - EXISTS' if r2 else 'STILL MISSING!'}")

    r3 = conn.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_name='product_results'"
    )).fetchone()
    print(f"  product_results table: {'OK - EXISTS' if r3 else 'STILL MISSING!'}")

    print()
    print("Existing tables (must stay intact):")
    for tbl in ['contacts', 'topics', 'threads', 'rfqs', 'suppliers', 'procurement_items']:
        rx = conn.execute(text(
            f"SELECT table_name FROM information_schema.tables WHERE table_name='{tbl}'"
        )).fetchone()
        status = "OK" if rx else "BROKEN!"
        print(f"  [{status}] {tbl}")

print("=" * 55)
