#!/usr/bin/env tsx
import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

async function main() {
  try {
    console.log('Running migration 007: Add updated_at to signals table...')

    const result = await sql`
      ALTER TABLE signals
      ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()
    `

    console.log('Added updated_at column to signals:', result)

    const index = await sql`
      CREATE INDEX IF NOT EXISTS idx_signals_updated ON signals(updated_at DESC)
    `

    console.log('Created index on updated_at:', index)
    console.log('Migration 007 completed successfully!')
  } catch (err) {
    console.error('Migration failed:', err)
    process.exit(1)
  }
}

main()
