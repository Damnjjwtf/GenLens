-- 009: verified signal store. Separate from the raw scraper's signals table.
CREATE TABLE IF NOT EXISTS ledger_signal_events (
  event_id TEXT PRIMARY KEY CHECK (event_id ~ '^evt_[a-f0-9]{24}$'),
  idempotency_key TEXT NOT NULL UNIQUE,
  signal_id TEXT NOT NULL CHECK (signal_id ~ '^sig_[a-f0-9]{20}$'),
  actor_id TEXT NOT NULL CHECK (actor_id IN ('genny', 'marti', 'unified')),
  content_hash TEXT NOT NULL CHECK (content_hash ~ '^[a-f0-9]{64}$'),
  record JSONB NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ledger_events_signal
  ON ledger_signal_events (signal_id, received_at DESC);

CREATE TABLE IF NOT EXISTS ledger_signals (
  signal_id TEXT PRIMARY KEY CHECK (signal_id ~ '^sig_[a-f0-9]{20}$'),
  actor_id TEXT NOT NULL CHECK (actor_id IN ('genny', 'marti', 'unified')),
  status TEXT NOT NULL CHECK (status IN ('published', 'qualified', 'rejected')),
  lenses TEXT[] NOT NULL,
  verticals TEXT[] NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  canonical_url TEXT NOT NULL,
  change TEXT NOT NULL,
  mechanism TEXT,
  use_case TEXT,
  impact TEXT,
  recommended_action TEXT,
  confidence TEXT NOT NULL,
  evidence JSONB NOT NULL,
  record JSONB NOT NULL,
  first_observed_at TIMESTAMPTZ NOT NULL,
  last_observed_at TIMESTAMPTZ NOT NULL,
  observation_count INTEGER NOT NULL CHECK (observation_count > 0),
  last_event_id TEXT NOT NULL REFERENCES ledger_signal_events(event_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ledger_signals_status_recent
  ON ledger_signals (status, last_observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_signals_lenses
  ON ledger_signals USING GIN (lenses);

-- Agent selection status is not independent human approval.
-- Never expose Marti/unified publicly without their promotion gates.