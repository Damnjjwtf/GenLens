-- Migration 006: Baseline Workflows
-- Define traditional vs AI-accelerated workflows per vertical
-- Used to anchor Score formula: (baseline_time - signal_time) / baseline_time

CREATE TABLE IF NOT EXISTS baseline_workflows (
  id SERIAL PRIMARY KEY,
  vertical VARCHAR NOT NULL,
  workflow_stage VARCHAR NOT NULL,
  product_category VARCHAR,
  description TEXT,

  -- Traditional (baseline) metrics
  traditional_time_hours DECIMAL NOT NULL,
  traditional_cost_dollars DECIMAL NOT NULL,

  -- AI-accelerated metrics (for comparison)
  ai_accelerated_time_hours DECIMAL,
  ai_accelerated_cost_dollars DECIMAL,

  -- Metadata
  baseline_year INT DEFAULT 2024,
  source VARCHAR,
  notes TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_baseline_vertical ON baseline_workflows(vertical);
CREATE INDEX IF NOT EXISTS idx_baseline_stage ON baseline_workflows(workflow_stage);
CREATE INDEX IF NOT EXISTS idx_baseline_category ON baseline_workflows(product_category);

-- Historical snapshots (for trending analysis)
CREATE TABLE IF NOT EXISTS baseline_snapshots (
  id SERIAL PRIMARY KEY,
  baseline_id INT REFERENCES baseline_workflows(id) ON DELETE CASCADE,
  vertical VARCHAR NOT NULL,
  workflow_stage VARCHAR NOT NULL,
  traditional_time_hours DECIMAL,
  traditional_cost_dollars DECIMAL,
  snapshot_date DATE NOT NULL,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshot_baseline ON baseline_snapshots(baseline_id);
CREATE INDEX IF NOT EXISTS idx_snapshot_date ON baseline_snapshots(snapshot_date);
