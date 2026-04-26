-- GenLens schema. Run against your Neon database before starting the app.
-- psql $DATABASE_URL -f lib/db/schema.sql

-- ═══════════════════════════════════════════════════════════
-- AUTH (NextAuth)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  email_verified TIMESTAMPTZ,
  name TEXT,
  image TEXT,
  role VARCHAR DEFAULT 'user',
  invite_code_used TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "userId" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR NOT NULL,
  provider VARCHAR NOT NULL,
  "providerAccountId" VARCHAR NOT NULL,
  refresh_token TEXT,
  access_token TEXT,
  expires_at INT,
  token_type VARCHAR,
  scope VARCHAR,
  id_token TEXT,
  session_state VARCHAR,
  UNIQUE(provider, "providerAccountId")
);

CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "sessionToken" TEXT UNIQUE NOT NULL,
  "userId" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS verification_token (
  identifier TEXT NOT NULL,
  token TEXT NOT NULL,
  expires TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (identifier, token)
);

CREATE TABLE IF NOT EXISTS invite_codes (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  max_uses INT DEFAULT 50,
  uses INT DEFAULT 0,
  created_by UUID REFERENCES users(id),
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- SIGNALS (unified intelligence table)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS signals (
  id SERIAL PRIMARY KEY,
  vertical VARCHAR NOT NULL,
  dimension INT NOT NULL,
  signal_type VARCHAR NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  summary TEXT,
  raw_content TEXT,
  workflow_stages TEXT[],
  product_categories TEXT[],
  tool_names TEXT[],
  time_saved_hours DECIMAL,
  cost_saved_dollars DECIMAL,
  quality_improvement_percent DECIMAL,
  learning_curve_hours DECIMAL,
  source_url TEXT,
  source_platform VARCHAR,
  source_name TEXT,
  trending_score INT DEFAULT 0,
  engagement_count INT DEFAULT 0,
  content_hash TEXT UNIQUE,
  published_at TIMESTAMPTZ,
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  status VARCHAR DEFAULT 'raw'
);

CREATE INDEX IF NOT EXISTS idx_signals_vertical ON signals(vertical);
CREATE INDEX IF NOT EXISTS idx_signals_dimension ON signals(dimension);
CREATE INDEX IF NOT EXISTS idx_signals_signal_type ON signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_hash ON signals(content_hash);

-- ═══════════════════════════════════════════════════════════
-- TEMPLATES, CREATORS, COMPETITORS
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS templates (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  vertical VARCHAR NOT NULL,
  product_category VARCHAR,
  workflow_stages TEXT[],
  tool_stack TEXT[],
  total_time_hours DECIMAL,
  estimated_cost_dollars DECIMAL,
  time_breakdown JSONB,
  quality_rating DECIMAL,
  source_platform VARCHAR,
  source_url TEXT,
  creator_name TEXT,
  creator_handle TEXT,
  creator_url TEXT,
  trending_score INT DEFAULT 0,
  community_engagement INT DEFAULT 0,
  adoption_count INT DEFAULT 0,
  content_hash TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS creators (
  id SERIAL PRIMARY KEY,
  handle TEXT NOT NULL,
  name TEXT,
  platform VARCHAR NOT NULL,
  profile_url TEXT,
  specialty TEXT,
  verticals TEXT[],
  tool_stack TEXT[],
  follower_count INT,
  engagement_rate DECIMAL,
  production_speed_hours DECIMAL,
  commercial_clients INT,
  leaderboard_score INT DEFAULT 0,
  leaderboard_rank INT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(handle, platform)
);

CREATE TABLE IF NOT EXISTS competitors (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  industry VARCHAR,
  website TEXT,
  product_categories TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS competitor_moves (
  id SERIAL PRIMARY KEY,
  competitor_id INT REFERENCES competitors(id),
  move_type VARCHAR,
  title TEXT NOT NULL,
  description TEXT,
  product_categories TEXT[],
  workflow_stages_affected TEXT[],
  source_url TEXT,
  relevance_score INT DEFAULT 50,
  announced_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- BRIEFINGS, PREFERENCES, SUBSCRIBERS
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS briefings (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  vertical VARCHAR,
  briefing_type VARCHAR DEFAULT 'daily',
  ticker TEXT,
  synthesis TEXT,
  signal_ids INT[],
  template_ids INT[],
  email_html TEXT,
  x_draft TEXT,
  linkedin_draft TEXT,
  keynote_notes TEXT,
  sent_at TIMESTAMPTZ,
  recipient_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_preferences (
  id SERIAL PRIMARY KEY,
  user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  active_verticals TEXT[] DEFAULT ARRAY['product_photography', 'filmmaking', 'digital_humans'],
  workflow_stage_focus TEXT[],
  product_categories_focus TEXT[],
  tools_tracking TEXT[],
  competitors_watching TEXT[],
  delivery_frequency VARCHAR DEFAULT 'daily',
  delivery_time TIME DEFAULT '08:00',
  delivery_timezone VARCHAR DEFAULT 'America/New_York',
  output_formats TEXT[] DEFAULT ARRAY['email', 'dashboard'],
  dimensions_visible INT[] DEFAULT ARRAY[1,2,3,4,5,6,7,8,9,10],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscribers (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  active BOOLEAN DEFAULT true,
  user_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- OPERATIONAL
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS scrape_log (
  id SERIAL PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_url TEXT,
  status VARCHAR,
  signals_found INT DEFAULT 0,
  signals_new INT DEFAULT 0,
  error_message TEXT,
  duration_ms INT,
  scraped_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cache (
  source TEXT PRIMARY KEY,
  data TEXT NOT NULL,
  fetched_at TIMESTAMPTZ DEFAULT NOW()
);
