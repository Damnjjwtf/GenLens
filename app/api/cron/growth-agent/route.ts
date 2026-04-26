/**
 * app/api/cron/growth-agent/route.ts
 *
 * Vercel Cron job: runs Growth Agent nightly at 3am UTC,
 * after the scraper + synthesis cron has completed.
 *
 * Configured in vercel.json:
 * { "crons": [{ "path": "/api/cron/growth-agent", "schedule": "0 3 * * *" }] }
 *
 * Also callable manually from the admin panel via POST.
 */

import { NextRequest, NextResponse } from 'next/server'
import { runGrowthAgent } from '@/lib/agent/growth-agent'
import { auth } from '@/auth'

export const maxDuration = 300 // 5 min — agent needs time to run

export async function GET(req: NextRequest) {
  // Verify this is a legitimate Vercel Cron call
  const authHeader = req.headers.get('authorization')
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const result = await runGrowthAgent('daily')
    return NextResponse.json({
      success: true,
      outputs: result.outputs,
      timestamp: new Date().toISOString(),
    })
  } catch (err) {
    console.error('[growth-agent cron]', err)
    return NextResponse.json(
      { success: false, error: err instanceof Error ? err.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

export async function POST(req: NextRequest) {
  // Admin-triggered run — requires auth
  const session = await auth()
  if (!session?.user || (session.user as { role?: string }).role !== 'admin') {
    return NextResponse.json({ error: 'Admin only' }, { status: 403 })
  }

  const body = await req.json().catch(() => ({}))
  const runType = body.runType ?? 'on_demand'

  try {
    const result = await runGrowthAgent(runType)
    return NextResponse.json({
      success: true,
      outputs: result.outputs,
      runType,
      timestamp: new Date().toISOString(),
    })
  } catch (err) {
    console.error('[growth-agent manual]', err)
    return NextResponse.json(
      { success: false, error: err instanceof Error ? err.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
