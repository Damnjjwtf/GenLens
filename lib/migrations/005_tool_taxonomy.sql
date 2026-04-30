-- Migration 005: Tool Taxonomy
-- Canonical tool IDs, aliases, and dedup mapping

CREATE TABLE IF NOT EXISTS tools (
  id SERIAL PRIMARY KEY,
  canonical_name VARCHAR NOT NULL UNIQUE,
  aliases TEXT[] DEFAULT ARRAY[]::TEXT[],
  category VARCHAR,
  vendor_name VARCHAR,
  website TEXT,
  logo_url TEXT,
  pricing_tier VARCHAR DEFAULT 'freemium',
  verticals TEXT[] DEFAULT ARRAY[]::TEXT[],
  dimensions INT[] DEFAULT ARRAY[]::INT[],
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tools_canonical ON tools(canonical_name);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category);
CREATE INDEX IF NOT EXISTS idx_tools_vendor ON tools(vendor_name);

-- Alias mapping table for fast lookups
CREATE TABLE IF NOT EXISTS tool_aliases (
  id SERIAL PRIMARY KEY,
  alias VARCHAR NOT NULL UNIQUE,
  tool_id INT NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alias_lookup ON tool_aliases(alias);

-- Update signals table to reference tools by ID (future migration)
-- For now, keep tool_names TEXT[] but will migrate to tool_ids INT[]
ALTER TABLE signals ADD COLUMN IF NOT EXISTS tool_ids INT[];

-- Track which tool names have been normalized
CREATE TABLE IF NOT EXISTS tool_normalization_log (
  id SERIAL PRIMARY KEY,
  signal_id INT REFERENCES signals(id) ON DELETE CASCADE,
  raw_tool_name VARCHAR,
  normalized_tool_id INT REFERENCES tools(id),
  confidence DECIMAL DEFAULT 1.0,
  normalized_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_norm_signal ON tool_normalization_log(signal_id);
CREATE INDEX IF NOT EXISTS idx_norm_tool ON tool_normalization_log(normalized_tool_id);
