/**
 * scripts/normalize-signals.ts
 *
 * Batch normalization job: resolves tool_names to tool_ids for signals.
 * Usage:
 *   npx tsx scripts/normalize-signals.ts [--limit 1000] [--dry-run] [--invalid-cache]
 */

import { neon } from '@neondatabase/serverless'
import { resolveToolIds, invalidateCache } from '@/lib/tools/normalize'

const sql = neon(process.env.DATABASE_URL!)

interface Signal {
  id: number
  tool_names: string[] | null
  tool_ids: number[] | null
}

async function normalizeSignals(opts: {
  limit: number
  dryRun: boolean
  invalidateCache: boolean
}): Promise<{ normalized: number; skipped: number; errors: number }> {
  if (opts.invalidateCache) {
    invalidateCache()
    console.log('[normalize] cache invalidated')
  }

  console.log(`Fetching signals with tool_names but no tool_ids (limit: ${opts.limit})...`)

  const signals = (await sql`
    SELECT id, tool_names, tool_ids FROM signals
    WHERE tool_names IS NOT NULL
      AND tool_names != '{}'
      AND (tool_ids IS NULL OR tool_ids = '{}')
    ORDER BY created_at DESC
    LIMIT ${opts.limit}
  `) as Signal[]

  console.log(`Found ${signals.length} signals to normalize`)

  let normalized = 0
  let skipped = 0
  let errors = 0

  for (let i = 0; i < signals.length; i++) {
    const signal = signals[i]

    try {
      if (!signal.tool_names || signal.tool_names.length === 0) {
        skipped++
        continue
      }

      const toolIds = await resolveToolIds(signal.tool_names)

      if (toolIds.length === 0) {
        skipped++
        continue
      }

      if (!opts.dryRun) {
        await sql`UPDATE signals SET tool_ids = ${toolIds} WHERE id = ${signal.id}`
      }

      normalized++

      if ((i + 1) % 50 === 0) {
        console.log(`  [${i + 1}/${signals.length}] ${normalized} normalized, ${skipped} skipped, ${errors} errors`)
      }
    } catch (err) {
      errors++
      console.error(`  [signal ${signal.id}] error:`, err instanceof Error ? err.message : err)
    }
  }

  console.log(`\nDone. ${normalized} normalized, ${skipped} skipped, ${errors} errors.`)

  if (opts.dryRun) {
    console.log('(dry-run mode — no database changes made)')
  }

  return { normalized, skipped, errors }
}

const args = process.argv.slice(2)
const limit = parseInt(args.find(a => a.startsWith('--limit='))?.split('=')[1] ?? '1000')
const dryRun = args.includes('--dry-run')
const shouldInvalidateCache = args.includes('--invalid-cache')

console.log(`Starting signal normalization...`)
console.log(`  Limit: ${limit}`)
console.log(`  Dry-run: ${dryRun}`)
console.log(`  Invalidate cache: ${shouldInvalidateCache}`)
console.log()

normalizeSignals({ limit, dryRun, invalidateCache: shouldInvalidateCache }).catch(console.error)
