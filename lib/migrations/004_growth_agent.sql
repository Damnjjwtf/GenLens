-- ═══════════════════════════════════════════════════════════
-- MIGRATION 004: Growth Agent Queue + GEO Content Tables
-- Run after existing schema migrations 001-003
-- ═══════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────
-- GROWTH AGENT QUEUE
-- All agent outputs land here. Human reviews before publish.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS growth_agent_queue (
  id SERIAL PRIMARY KEY,

  -- What kind of output this is
  output_type VARCHAR NOT NULL,
  -- social_x | social_linkedin | geo_block | index_post
  -- signal_page | hiring_report | comparison_page | template_geo

  -- Core content
  content TEXT NOT NULL,              -- The actual draft text / HTML / markdown
  title TEXT,                         -- Display title for admin review UI
  target_url TEXT,                    -- Where it will publish (genlens.app/...)
  meta_description TEXT,              -- For GEO pages: meta description
  faq_schema JSONB,                   -- JSON-LD FAQ schema for GEO pages

  -- Source traceability
  signal_ids INT[],                   -- Which signals drove this output
  tool_slug TEXT,                     -- Tool this relates to (if tool page)
  vertical VARCHAR,                   -- product_photography | filmmaking | digital_humans
  briefing_date DATE,                 -- Which day's briefing this came from

  -- Review workflow
  status VARCHAR NOT NULL DEFAULT 'draft',
  -- draft | approved | rejected | published | archived

  review_notes TEXT,                  -- Human reviewer notes
  rejection_reason TEXT,              -- Why it was rejected (for agent learning)
  approved_by UUID REFERENCES users(id),
  published_at TIMESTAMP WITH TIME ZONE,

  -- Scheduling
  scheduled_for TIMESTAMP WITH TIME ZONE, -- When to publish (null = publish immediately on approve)

  -- Metrics (filled in after publish)
  impressions INT DEFAULT 0,
  clicks INT DEFAULT 0,
  conversions INT DEFAULT 0,         -- Signups attributed to this content

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_gaq_status ON growth_agent_queue(status);
CREATE INDEX idx_gaq_output_type ON growth_agent_queue(output_type);
CREATE INDEX idx_gaq_created ON growth_agent_queue(created_at DESC);
CREATE INDEX idx_gaq_scheduled ON growth_agent_queue(scheduled_for) WHERE scheduled_for IS NOT NULL;
CREATE INDEX idx_gaq_tool_slug ON growth_agent_queue(tool_slug) WHERE tool_slug IS NOT NULL;

-- ─────────────────────────────────────────────────────────────
-- TOOL DIRECTORY (public, no auth)
-- Canonical tool records with GEO content
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tools (
  id SERIAL PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,          -- 'elevenlabs', 'keyshot', 'runway'
  canonical_name TEXT NOT NULL,       -- 'ElevenLabs'
  aliases TEXT[],                     -- ['eleven labs', 'Eleven Labs', '11labs']

  -- Classification
  verticals TEXT[] NOT NULL,          -- ['digital_humans', 'filmmaking']
  categories TEXT[],                  -- ['voice_synthesis', 'avatar']
  workflow_stages TEXT[],             -- ['voice_gen', 'lip_sync']

  -- Discovery
  website_url TEXT,
  affiliate_url TEXT,                 -- Affiliate/referral link (earns commission)
  affiliate_program TEXT,             -- Program name for disclosure
  affiliate_commission_pct DECIMAL,   -- Approx commission % (display only)

  -- GenLens intelligence
  current_score INT,                  -- 0-100, updated nightly
  score_history JSONB,                -- [{date, score, reason}]
  signal_count INT DEFAULT 0,         -- How many signals reference this tool
  last_signal_at TIMESTAMP WITH TIME ZONE,

  -- GEO content (written by Growth Agent)
  geo_summary TEXT,                   -- 2-3 sentence structured summary for AI engines
  geo_qa_blocks JSONB,                -- [{q, a, confidence, source_url, updated_at}]
  faq_schema JSONB,                   -- JSON-LD FAQ markup, auto-generated
  meta_description TEXT,              -- For <meta name="description">

  -- Page state
  is_public BOOLEAN DEFAULT true,
  is_featured BOOLEAN DEFAULT false,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tools_slug ON tools(slug);
CREATE INDEX idx_tools_verticals ON tools USING GIN(verticals);
CREATE INDEX idx_tools_score ON tools(current_score DESC NULLS LAST);

-- ─────────────────────────────────────────────────────────────
-- TOOL COMPARISONS (public GEO pages)
-- genlens.app/compare/[tool-a]-vs-[tool-b]
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tool_comparisons (
  id SERIAL PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,          -- 'elevenlabs-vs-heygen'
  tool_a_slug TEXT REFERENCES tools(slug),
  tool_b_slug TEXT REFERENCES tools(slug),

  -- GEO content
  summary TEXT,                       -- Agent-written comparison summary
  geo_qa_blocks JSONB,                -- Q&A pairs about the comparison
  faq_schema JSONB,                   -- JSON-LD

  -- Which vertical this comparison is most relevant for
  primary_vertical VARCHAR,

  is_public BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- SIGNAL PUBLIC PAGES
-- genlens.app/signals/[id] — each signal gets a shareable URL
-- ─────────────────────────────────────────────────────────────
-- Extend existing signals table (add columns if not present)
ALTER TABLE signals
  ADD COLUMN IF NOT EXISTS geo_summary TEXT,        -- Agent-written GEO summary
  ADD COLUMN IF NOT EXISTS hook_sentence TEXT,      -- Social OG card hook
  ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS public_views INT DEFAULT 0;

-- ─────────────────────────────────────────────────────────────
-- AGENT RUN LOG
-- Tracks every agent execution for debugging + auditing
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_runs (
  id SERIAL PRIMARY KEY,
  run_type VARCHAR NOT NULL,          -- daily | weekly_index | on_demand
  triggered_by VARCHAR DEFAULT 'cron', -- cron | admin | api
  status VARCHAR DEFAULT 'running',   -- running | completed | failed

  -- Stats
  signals_processed INT DEFAULT 0,
  outputs_generated INT DEFAULT 0,
  geo_blocks_written INT DEFAULT 0,
  tools_updated INT DEFAULT 0,

  -- Timing
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  duration_ms INT,

  -- Debug
  error_message TEXT,
  run_log JSONB                        -- Structured log of what happened
);

CREATE INDEX idx_agent_runs_created ON agent_runs(started_at DESC);
