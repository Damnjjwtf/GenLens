-- Add updated_at column to signals table for tracking agent modifications

ALTER TABLE signals
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create index on updated_at for efficient ordering
CREATE INDEX IF NOT EXISTS idx_signals_updated ON signals(updated_at DESC);
