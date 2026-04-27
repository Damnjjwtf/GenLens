-- ═══════════════════════════════════════════════════════════
-- MIGRATION 005: Social Posting Agent — post_results
-- Tracks every platform post made from the growth_agent_queue.
-- Discord is webhook-based (no token storage needed).
-- X / LinkedIn will need platform_tokens later (migration 006).
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS post_results (
  id SERIAL PRIMARY KEY,
  queue_item_id INT REFERENCES growth_agent_queue(id) ON DELETE CASCADE,

  platform VARCHAR NOT NULL,            -- discord | x | linkedin
  channel TEXT,                         -- For discord: which channel webhook (pp | fm | dh | general | tool_releases | legal_alerts | hiring | templates | announcements)

  platform_post_id TEXT,                -- ID returned by platform API (Discord message id, tweet id, etc.)
  platform_post_url TEXT,               -- Direct URL to the published post

  status VARCHAR NOT NULL DEFAULT 'posted', -- posted | failed | deleted
  error_message TEXT,

  -- Metrics (filled in later for platforms that support readback)
  impressions INT DEFAULT 0,
  engagements INT DEFAULT 0,
  clicks INT DEFAULT 0,

  posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_post_results_queue ON post_results(queue_item_id);
CREATE INDEX idx_post_results_platform ON post_results(platform);
CREATE INDEX idx_post_results_posted ON post_results(posted_at DESC);
