-- Migration 008: Tool Scores
-- Store computed GenLens Score (0-100) per tool
-- Updated nightly via /api/cron/score

CREATE TABLE IF NOT EXISTS tool_scores (
  id SERIAL PRIMARY KEY,
  tool_id INT NOT NULL UNIQUE REFERENCES tools(id) ON DELETE CASCADE,
  
  -- Composite score (0-100)
  score INT NOT NULL,
  
  -- Component scores
  speed_score INT NOT NULL DEFAULT 50,      -- Time savings vs baseline
  cost_score INT NOT NULL DEFAULT 50,       -- Cost savings vs baseline
  quality_score INT NOT NULL DEFAULT 50,    -- Quality improvement
  adoption_score INT NOT NULL DEFAULT 50,   -- Adoption velocity
  
  -- Metadata
  signals_count INT DEFAULT 0,
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_scores_score ON tool_scores(score DESC);
CREATE INDEX IF NOT EXISTS idx_tool_scores_updated ON tool_scores(last_updated DESC);

-- Score history for movers calculation (week-over-week delta)
CREATE TABLE IF NOT EXISTS tool_score_history (
  id SERIAL PRIMARY KEY,
  tool_id INT NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
  score INT NOT NULL,
  snapshot_date DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_score_history_tool ON tool_score_history(tool_id);
CREATE INDEX IF NOT EXISTS idx_score_history_date ON tool_score_history(snapshot_date DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_score_history_unique ON tool_score_history(tool_id, snapshot_date);
