/**
 * app/api/cron/scrape/route.ts
 *
 * Vercel Cron entry for the scraper.
 * Schedule: 0 2 * * * (daily at 02:00 UTC), defined in vercel.json.
 *
 * Auth: Bearer ${CRON_SECRET}. Vercel Cron sends this automatically when
 * CRON_SECRET is configured as an env var.
 *
 * Returns a per-source report. Long-running jobs use maxDuration = 300s.
 */

import { NextRequest, NextResponse } from 'next/server'
import { runScraper } from '@/lib/scraper/orchestrator'
import { auth } from '@/auth'

export const maxDuration = 300

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get('authorization')
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const report = await runScraper()
    return NextResponse.json({ success: true, ...report, timestamp: new Date().toISOString() })
  } catch (err) {
    console.error('[cron/scrape]', err)
    return NextResponse.json(
      { success: false, error: err instanceof Error ? err.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

/**
 * POST — admin-triggered manual scrape (from a future admin panel).
 * Optional body: { vertical?: 'product_photography' | 'filmmaking' | 'digital_humans' }
 */
export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user || (session.user as { role?: string }).role !== 'admin') {
    return NextResponse.json({ error: 'Admin only' }, { status: 403 })
  }

  const body = await req.json().catch(() => ({}))
  const verticalFilter = body?.vertical as string | undefined

  try {
    const report = await runScraper({
      sourceFilter: verticalFilter
        ? (s) => s.verticals.includes(verticalFilter as never)
        : undefined,
    })
    return NextResponse.json({ success: true, ...report, timestamp: new Date().toISOString() })
  } catch (err) {
    console.error('[cron/scrape POST]', err)
    return NextResponse.json(
      { success: false, error: err instanceof Error ? err.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
