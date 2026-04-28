/**
 * scripts/db.ts
 *
 * Tiny query runner. Reads DATABASE_URL from the env (load .env.local
 * before invoking — see usage below) and executes a single SQL string
 * via Neon's HTTPS driver. Prints rows as JSON or a compact table.
 *
 * Usage:
 *   set -a && source .env.local && set +a
 *   npx tsx scripts/db.ts "SELECT COUNT(*) FROM baseline_workflows"
 *   npx tsx scripts/db.ts --table "SELECT vertical, workflow_stage FROM baseline_workflows ORDER BY vertical"
 *
 * Flags:
 *   --table   Pretty-print as an aligned table (default: JSON)
 *   --json    Force JSON output
 */

import { neon } from '@neondatabase/serverless'

const args = process.argv.slice(2)
const wantTable = args.includes('--table')
const _wantJson = args.includes('--json')
const sqlArg = args.filter(a => !a.startsWith('--')).join(' ').trim()

if (!sqlArg) {
  console.error('Usage: tsx scripts/db.ts [--table|--json] "<SQL>"')
  process.exit(1)
}

if (!process.env.DATABASE_URL) {
  console.error('DATABASE_URL not set. Run: set -a && source .env.local && set +a')
  process.exit(1)
}

const sql = neon(process.env.DATABASE_URL)

const rows = (await sql.query(sqlArg)) as Record<string, unknown>[]

if (!Array.isArray(rows) || rows.length === 0) {
  console.log('(no rows)')
  process.exit(0)
}

if (wantTable) {
  const cols = Object.keys(rows[0])
  const widths = cols.map(c =>
    Math.max(c.length, ...rows.map(r => String(r[c] ?? '').length)),
  )
  const fmt = (vals: string[]) =>
    vals.map((v, i) => v.padEnd(widths[i])).join('  ')
  console.log(fmt(cols))
  console.log(widths.map(w => '─'.repeat(w)).join('  '))
  for (const r of rows) console.log(fmt(cols.map(c => String(r[c] ?? ''))))
  console.log(`\n(${rows.length} rows)`)
} else {
  console.log(JSON.stringify(rows, null, 2))
  console.error(`(${rows.length} rows)`)
}
