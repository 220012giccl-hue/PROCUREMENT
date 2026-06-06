-- Migration 005: RFQ Extended Fields + Procurement Item Full Status Support
-- Date: June 2026
-- Principle: Additive only — never drop existing columns or tables
-- Run AFTER migration 004.

-- ── 1. Add extended tracking fields to rfqs table ───────────────────────────
ALTER TABLE rfqs
    ADD COLUMN IF NOT EXISTS quote_due_date          TIMESTAMP,
    ADD COLUMN IF NOT EXISTS supplier_sent_date       TIMESTAMP,
    ADD COLUMN IF NOT EXISTS supplier_response_date   TIMESTAMP,
    ADD COLUMN IF NOT EXISTS internal_owner           VARCHAR(255),
    ADD COLUMN IF NOT EXISTS site_address             TEXT,
    ADD COLUMN IF NOT EXISTS drawing_reference        TEXT,
    ADD COLUMN IF NOT EXISTS compliance_requirements  TEXT,
    ADD COLUMN IF NOT EXISTS follow_up_sent           BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS follow_up_count          INTEGER DEFAULT 0;

-- ── 2. Widen status column to support all 13 plan statuses ──────────────────
-- Existing statuses: DRAFT, READY, SENT, RECEIVED, UNDER_REVIEW, APPROVED, REJECTED, CLOSED
-- New statuses to support: OVERDUE, EXPIRED, CLARIFICATION_REQUIRED, SUPPLIER_ACKNOWLEDGED, UNDER_COMPARISON

-- No schema change needed for VARCHAR status — just documenting valid values:
-- DRAFT | READY | SENT | SUPPLIER_ACKNOWLEDGED | RECEIVED | CLARIFICATION_REQUIRED
-- UNDER_COMPARISON | UNDER_REVIEW | APPROVED | REJECTED | CLOSED | EXPIRED | OVERDUE

-- ── 3. Add approval_status and required_date to procurement_items ────────────
ALTER TABLE procurement_items
    ADD COLUMN IF NOT EXISTS required_date  DATE,
    ADD COLUMN IF NOT EXISTS image_url      TEXT,
    ADD COLUMN IF NOT EXISTS brand          VARCHAR(255),
    ADD COLUMN IF NOT EXISTS project_id     INTEGER REFERENCES topics(id) ON DELETE SET NULL;

-- ── 4. Create approval_summaries table (for Generate Approval Summary feature) ─
CREATE TABLE IF NOT EXISTS approval_summaries (
    id                  SERIAL PRIMARY KEY,
    rfq_id              INTEGER REFERENCES rfqs(id) ON DELETE CASCADE,
    procurement_item_id INTEGER REFERENCES procurement_items(id) ON DELETE SET NULL,
    topic_id            INTEGER REFERENCES topics(id) ON DELETE SET NULL,
    generated_by_ai     BOOLEAN DEFAULT TRUE,
    summary_text        TEXT NOT NULL,
    recommended_action  TEXT,
    risk_notes          TEXT,
    missing_info        TEXT,
    status              VARCHAR(50) DEFAULT 'PENDING',  -- PENDING | APPROVED | REJECTED
    reviewed_by         VARCHAR(255),
    reviewed_at         TIMESTAMP,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- ── 5. Add index for faster workflow lookups ─────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_rfq_status          ON rfqs(status);
CREATE INDEX IF NOT EXISTS idx_rfq_quote_due_date  ON rfqs(quote_due_date);
CREATE INDEX IF NOT EXISTS idx_approval_summaries_rfq ON approval_summaries(rfq_id);
