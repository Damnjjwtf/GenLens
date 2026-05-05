#!/usr/bin/env tsx
import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

async function main() {
  try {
    console.log('Running migration 008: Rename users.email_verified -> users."emailVerified" for NextAuth pg-adapter...')

    const cols = await sql`
      SELECT column_name FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'users'
        AND column_name IN ('email_verified', 'emailVerified')
    ` as { column_name: string }[]

    const has_old = cols.some(c => c.column_name === 'email_verified')
    const has_new = cols.some(c => c.column_name === 'emailVerified')

    if (has_new && !has_old) {
      console.log('Already migrated. Nothing to do.')
      return
    }
    if (!has_old) {
      console.log('Neither column present. users table may need full schema. Aborting.')
      process.exit(1)
    }

    await sql`ALTER TABLE users RENAME COLUMN email_verified TO "emailVerified"`
    console.log('Renamed users.email_verified -> users."emailVerified"')
    console.log('Migration 008 completed successfully!')
  } catch (err) {
    console.error('Migration failed:', err)
    process.exit(1)
  }
}

main()
