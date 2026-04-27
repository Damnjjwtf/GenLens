-- ═══════════════════════════════════════════════════════════
-- MIGRATION 006: Score + Index backbone
-- baseline_workflows  — denominator for the Score formula
-- tool_scores         — per tool per vertical, with weekly snapshots
-- template_scores     — per workflow template, with weekly snapshots
-- index_snapshots     — weekly Index state (top 10 + movers + entries/exits)
-- ═══════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────
-- BASELINE WORKFLOWS
-- "Traditional rendering = 14h" anchors. Every Score input is
-- traceable to a baseline, otherwise the number is meaningless.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS baseline_workflows (
  id SERIAL PRIMARY KEY,
  workflow_stage TEXT NOT NULL,         -- rendering | voice_gen | compositing | vfx_shot | etc.
  vertical VARCHAR NOT NULL,            -- product_photography | filmmaking | digital_humans
  product_category TEXT,                -- hard_goods | soft_goods | lifestyle | commercial | talking_head | etc.

  -- The denominators
  traditional_time_hours DECIMAL NOT NULL,
  traditional_cost_dollars DECIMAL NOT NULL,

  -- Sample AI-accelerated benchmark (illustrative, not authoritative)
  ai_accelerated_time_hours DECIMAL,
  ai_accelerated_cost_dollars DECIMAL,
  ai_accelerated_tool_slug TEXT,        -- which tool produced the sample numbers

  baseline_year INT NOT NULL,
  source TEXT NOT NULL,                 -- GENLENS_SPEC_v2 | industry_survey | etc.
  notes TEXT,

  is_active BOOLEAN DEFAULT true,       -- false = retired baseline (kept for history)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(workflow_stage, vertical, product_category, baseline_year)
);

CREATE INDEX idx_baselines_vertical ON baseline_workflows(vertical) WHERE is_active = true;
CREATE INDEX idx_baselines_stage ON baseline_workflows(workflow_stage) WHERE is_active = true;

-- ─────────────────────────────────────────────────────────────
-- TOOL SCORES
-- Per (tool, vertical) — same tool can score differently per vertical.
-- Each row = a snapshot. Latest snapshot per (tool_slug, vertical) is current.
-- Score history = WHERE tool_slug = X AND vertical = Y ORDER BY snapshot_date.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tool_scores (
  id SERIAL PRIMARY KEY,
  tool_slug TEXT NOT NULL,              -- references tools.slug (no FK so we can score before tool record exists)
  vertical VARCHAR NOT NULL,

  -- Composite + components (all 0-100)
  score INT NOT NULL,
  speed_score INT,                      -- time saved vs. baseline
  cost_score INT,                       -- cost saved vs. baseline
  quality_score INT,                    -- output quality delta (from signals)
  adoption_score INT,                   -- trending_score velocity

  -- Inputs (for traceability — every Score must be defensible)
  signal_ids INT[],                     -- which signals fed this snapshot
  baseline_id INT REFERENCES baseline_workflows(id),
  signal_count INT DEFAULT 0,

  -- Time positioning
  snapshot_date DATE NOT NULL,          -- week ending date for this snapshot
  computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  notes TEXT,                           -- agent reasoning, edge cases

  UNIQUE(tool_slug, vertical, snapshot_date)
);

CREATE INDEX idx_tool_scores_slug ON tool_scores(tool_slug, snapshot_date DESC);
CREATE INDEX idx_tool_scores_vertical_date ON tool_scores(vertical, snapshot_date DESC);
CREATE INDEX idx_tool_scores_score ON tool_scores(score DESC);

-- ─────────────────────────────────────────────────────────────
-- TEMPLATE SCORES
-- Per workflow template. Same shape as tool_scores.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS template_scores (
  id SERIAL PRIMARY KEY,
  template_id INT NOT NULL,             -- references templates.id (loose FK — table may exist later)
  vertical VARCHAR NOT NULL,

  score INT NOT NULL,
  speed_score INT,
  cost_score INT,
  quality_score INT,
  adoption_score INT,

  signal_ids INT[],
  baseline_id INT REFERENCES baseline_workflows(id),
  usage_count INT DEFAULT 0,            -- how many user_workflows referenced this template

  snapshot_date DATE NOT NULL,
  computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  notes TEXT,

  UNIQUE(template_id, vertical, snapshot_date)
);

CREATE INDEX idx_template_scores_id ON template_scores(template_id, snapshot_date DESC);
CREATE INDEX idx_template_scores_vertical_date ON template_scores(vertical, snapshot_date DESC);

-- ─────────────────────────────────────────────────────────────
-- INDEX SNAPSHOTS
-- One row per (vertical, week_start_date). Stores the weekly Index state:
-- top 10 tools, biggest movers, new entries, notable exits.
-- Drives /index/[date] page + Monday email + JSON API.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS index_snapshots (
  id SERIAL PRIMARY KEY,
  vertical VARCHAR NOT NULL,            -- product_photography | filmmaking | digital_humans | all
  week_start_date DATE NOT NULL,        -- Monday of the index week

  -- Snapshot payload (all jsonb for flexible rendering)
  top_tools JSONB NOT NULL,             -- [{rank, tool_slug, score, score_delta}, ...]  (top 10)
  biggest_movers_up JSONB,              -- [{tool_slug, score, delta, prev_score}, ...]   (top 5)
  biggest_movers_down JSONB,            -- [{tool_slug, score, delta, prev_score}, ...]   (top 5)
  new_entries JSONB,                    -- tools that crossed the threshold this week
  notable_exits JSONB,                  -- tools that dropped below the threshold

  -- Editorial
  headline TEXT,                        -- agent-generated, human-approved
  lede TEXT,                            -- 2-sentence index summary
  summary_signal_ids INT[],             -- signals that drove this week's narrative

  -- Lifecycle
  status VARCHAR DEFAULT 'draft',       -- draft | approved | published
  published_at TIMESTAMP WITH TIME ZONE,
  approved_by UUID REFERENCES users(id),

  generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(vertical, week_start_date)
);

CREATE INDEX idx_index_snapshots_vertical_week ON index_snapshots(vertical, week_start_date DESC);
CREATE INDEX idx_index_snapshots_status ON index_snapshots(status);
CREATE INDEX idx_index_snapshots_published ON index_snapshots(published_at DESC) WHERE published_at IS NOT NULL;

-- ─────────────────────────────────────────────────────────────
-- SEED BASELINES
-- Three per vertical. Drawn from GENLENS_SPEC_v2 + industry estimates.
-- Conservative numbers — easier to revise up than down.
-- ─────────────────────────────────────────────────────────────
INSERT INTO baseline_workflows
  (workflow_stage, vertical, product_category, traditional_time_hours, traditional_cost_dollars,
   ai_accelerated_time_hours, ai_accelerated_cost_dollars, ai_accelerated_tool_slug,
   baseline_year, source, notes)
VALUES
  -- Product Photography
  ('rendering', 'product_photography', 'hard_goods',
   14, 1200, 4, 100, 'keyshot',
   2026, 'GENLENS_SPEC_v2',
   'Outsourced render farm baseline. AI-accelerated assumes KeyShot 2026 with denoise + upscale.'),

  ('compositing', 'product_photography', 'lifestyle',
   6, 400, 1, 30, 'photoroom',
   2026, 'GENLENS_SPEC_v2',
   'Photographer + retoucher baseline. AI assumes background gen + auto-mask.'),

  ('pattern_design', 'product_photography', 'soft_goods',
   20, 800, 6, 150, 'clo3d',
   2026, 'GENLENS_SPEC_v2',
   '3D garment pattern baseline. AI assumes CLO3D + AI fabric simulation.'),

  -- Commercial Filmmaking
  ('vfx_shot', 'filmmaking', 'commercial',
   24, 2000, 6, 200, 'runway',
   2026, 'GENLENS_SPEC_v2',
   '30-second commercial VFX shot baseline. AI assumes Runway Gen-3 + manual cleanup.'),

  ('color_grade', 'filmmaking', 'commercial',
   8, 600, 2, 80, 'davinci_resolve',
   2026, 'GENLENS_SPEC_v2',
   'Colorist baseline for 60-second spot. AI assumes Resolve Neural Engine.'),

  ('motion_design', 'filmmaking', 'commercial',
   12, 900, 3, 100, 'after_effects',
   2026, 'GENLENS_SPEC_v2',
   '15-second motion graphics baseline. AI assumes AE + AI plugins (Astra, etc.).'),

  -- Digital Humans
  ('voice_gen', 'digital_humans', 'talking_head',
   6, 400, 0.5, 20, 'elevenlabs',
   2026, 'GENLENS_SPEC_v2',
   'VO booking + recording baseline. AI assumes ElevenLabs cloned voice + light editing.'),

  ('avatar_render', 'digital_humans', 'talking_head',
   12, 800, 1, 30, 'heygen',
   2026, 'GENLENS_SPEC_v2',
   'Talking-head avatar baseline (3-min explainer). AI assumes HeyGen template + script.'),

  ('lip_sync', 'digital_humans', 'full_animation',
   8, 500, 0.5, 20, 'synthesia',
   2026, 'GENLENS_SPEC_v2',
   'Manual lip-sync animation baseline. AI assumes Synthesia automated phoneme matching.')
ON CONFLICT (workflow_stage, vertical, product_category, baseline_year) DO NOTHING;
