-- ============================================================
-- Migration 006: Add Dynamic Specification Columns
-- Purpose: Enable category-based comparison tables with
--          dynamic technical specs (Brand, Voltage, Warranty,
--          Safety Rating, Material, Compliance etc.)
-- Date: June 2026
-- ============================================================

-- 1. Extend product_results (AI Market Research data)
ALTER TABLE product_results ADD COLUMN IF NOT EXISTS category         VARCHAR(100);
ALTER TABLE product_results ADD COLUMN IF NOT EXISTS brand            VARCHAR(255);
ALTER TABLE product_results ADD COLUMN IF NOT EXISTS specs_json       JSONB DEFAULT '{}'::jsonb;
ALTER TABLE product_results ADD COLUMN IF NOT EXISTS confidence_level VARCHAR(50);
ALTER TABLE product_results ADD COLUMN IF NOT EXISTS image_url        TEXT;
ALTER TABLE product_results ADD COLUMN IF NOT EXISTS best_for         TEXT;

-- 2. Extend supplier_quotes (Vendor Quote data)
ALTER TABLE supplier_quotes ADD COLUMN IF NOT EXISTS brand            VARCHAR(255);
ALTER TABLE supplier_quotes ADD COLUMN IF NOT EXISTS specs_json       JSONB DEFAULT '{}'::jsonb;

-- 3. Index for fast category-based filtering
CREATE INDEX IF NOT EXISTS idx_product_results_category ON product_results(category);
CREATE INDEX IF NOT EXISTS idx_product_results_topic_category ON product_results(topic_id, category);

-- Verification queries (run manually to confirm):
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'product_results' ORDER BY ordinal_position;
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'supplier_quotes' ORDER BY ordinal_position;
