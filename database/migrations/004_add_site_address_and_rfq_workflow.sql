-- ============================================================
-- Migration 004: Add site_address + rfq_workflows + product_results
-- PRD Version: 2.1
-- Date: 2026-06-02
-- Rule: Additive only. Never remove or alter existing columns.
-- ============================================================

-- Step 1: Add site_address column to existing topics table
-- (IF NOT EXISTS prevents duplicate column errors on re-run)
ALTER TABLE topics ADD COLUMN IF NOT EXISTS site_address TEXT;

-- Step 2: Create rfq_workflows table
-- Tracks the state of each RFQ as it moves through the pipeline.
-- References: topics(id) and threads(id) — both exist in current DB.
CREATE TABLE IF NOT EXISTS rfq_workflows (
    id               SERIAL PRIMARY KEY,
    topic_id         INT REFERENCES topics(id) ON DELETE SET NULL,
    thread_id        INT REFERENCES threads(id) ON DELETE SET NULL,
    status           VARCHAR(100) DEFAULT 'ingested',
    -- Status values: ingested | triage | researching | drafts_ready | sent | quotes_received
    confidence_score FLOAT,
    assigned_by      VARCHAR(100) DEFAULT 'ai',  -- 'ai' or 'human'
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

-- Step 3: Create product_results table
-- Stores market research price results per topic.
-- NOTE: If you prefer to use product_comparisons table instead, skip this block.
CREATE TABLE IF NOT EXISTS product_results (
    id           SERIAL PRIMARY KEY,
    topic_id     INT REFERENCES topics(id) ON DELETE SET NULL,
    item_name    TEXT NOT NULL,
    supplier     TEXT,           -- e.g. "Bunnings", "Sydney Tools", "Blackwoods"
    unit_price   NUMERIC(10, 2),
    unit         VARCHAR(50),    -- e.g. "each", "m", "box"
    source_url   TEXT,
    fetched_at   TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- Verification queries (run manually to confirm):
-- SELECT column_name FROM information_schema.columns WHERE table_name='topics' AND column_name='site_address';
-- SELECT table_name FROM information_schema.tables WHERE table_name IN ('rfq_workflows','product_results');
-- ============================================================
