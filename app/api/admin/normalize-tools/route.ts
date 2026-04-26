/**
 * app/api/admin/normalize-tools/route.ts
 *
 * Admin endpoint to trigger tool ID normalization.
 * Manual trigger first; can be automated via cron later.
 */

import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/auth'
import { neon } from '@neondatabase/serverless'
import { resolveToolIds, invalidateCache } from '@/lib/tools/normalize'

const sql = neon(process.env.DATABASE_URL!)

interface Signal {
  id: number
  tool_names: string[] | null
}

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user || (session.user as { role?: string }).role !== 'admin') {
    return NextResponse.json({ error: 'Admin only' }, { status: 403 })
  }

  const body = await req.json().catch(() => ({}))
  const limit = Math.min(body?.limit ?? 500, 5000) // Cap at 5000
  const dryRun = body?.dryRun ?? false
  const shouldInvalidateCache = body?.invalidateCache ?? false

  try {
    if (shouldInvalidateCache) {
      invalidateCache()
    }

    const signals = (await sql`
      SELECT id, tool_names FROM signals
      WHERE tool_names IS NOT NULL
        AND tool_names != '{}'
        AND (tool_ids IS NULL OR tool_ids = '{}')
      ORDER BY created_at DESC
      LIMIT ${limit}
    `) as Signal[]

    let normalized = 0
    let skipped = 0
    let errors = 0
    const failedSignals: { id: number; error: string }[] = []

    for (const signal of signals) {
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

        if (!dryRun) {
          await sql`UPDATE signals SET tool_ids = ${toolIds} WHERE id = ${signal.id}`
        }

        normalized++
      } catch (err) {
        errors++
        failedSignals.push({
          id: signal.id,
          error: err instanceof Error ? err.message : 'Unknown error',
        })
      }
    }

    return NextResponse.json({
      success: true,
      normalized,
      skipped,
      errors,
      total: signals.length,
      dryRun,
      failedSignals: errors > 0 ? failedSignals.slice(0, 10) : undefined,
      timestamp: new Date().toISOString(),
    })
  } catch (err) {
    console.error('[admin/normalize-tools]', err)
    return NextResponse.json(
      { success: false, error: err instanceof Error ? err.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
