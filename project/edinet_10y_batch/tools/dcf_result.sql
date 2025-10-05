-- dcf_result.sql (minimal initial DDL)
CREATE TABLE IF NOT EXISTS dcf_result (
  id BIGSERIAL PRIMARY KEY,
  source_id TEXT NOT NULL,
  valuation_base NUMERIC,
  valuation_bull NUMERIC,
  valuation_bear NUMERIC,
  wacc NUMERIC,
  g NUMERIC,
  as_of TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_dcf_sid ON dcf_result(source_id);
