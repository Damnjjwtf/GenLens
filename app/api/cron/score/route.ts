/**
 * app/api/cron/score/route.ts
 *
 * Vercel Cron entry for the Score compute job.
 * Runs nightly. Reads classified signals from the last 30 days,
 * groups by (tool, vertical), computes a Score per pair, and writes
 * to tool_scores with snapshot_date = today.
 *
 * One row per (tool_slug, vertical, snapshot_date). Re-running on the
 * same day overwrites (UNIQUE constraint + ON CONFLICT).
 *
 * Auth: Bearer ${CRON_SECRET}.
 */

import { NextRequest, NextResponse } from 'next/server'
import { neon } from '@neondatabase/serverless'
import {
  computeScore,
  pickBaseline,
  type ScoreSignal,
  type ScoreBaseline,
} from '@/lib/score/compute'

export const maxDuration = 120

const sql = neon(process.env.DATABASE_URL!)

const LOOKBACK_DAYS = 30

interface SignalRow extends ScoreSignal {
  vertical: string
  tool_names: string[] | null
}

interface ToolRow {
  slug: string
  canonical_name: string
  aliases: string[] | null
  verticals: string[]
  workflow_stages: string[] | null
}

interface BaselineRow extends ScoreBaseline {
  vertical: string
  workflow_stage: string
}

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get('authorization')
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const startedAt = Date.now()
  const today = new Date().toISOString().slice(0, 10)

  try {
    // Pull tools, baselines, and lookback signals in parallel.
    const [tools, baselines, signals] = await Promise.all([
      sql`
        SELECT slug, canonical_name, aliases, verticals, workflow_stages
        FROM tools
        WHERE is_public = true
      ` as Promise<ToolRow[]>,
      sql`
        SELECT id, vertical, workflow_stage,
               traditional_time_hours, traditional_cost_dollars
        FROM baseline_workflows
        WHERE is_active = true
      ` as Promise<BaselineRow[]>,
      sql`
        SELECT id, vertical, tool_names, signal_type,
               time_saved_hours, cost_saved_dollars,
               quality_improvement_percent, trending_score
        FROM signals
        WHERE status = 'classified'
          AND created_at >= NOW() - (${LOOKBACK_DAYS} * INTERVAL '1 day')
      ` as Promise<SignalRow[]>,
    ])

    // Build a name → slug lookup. The classifier emits canonical-ish names
    // ("ComfyUI", "Adobe Photoshop"), not slugs. We match against the tool's
    // canonical_name AND its aliases, all lowercased for fuzziness.
    const nameToSlug = new Map<string, string>()
    for (const tool of tools) {
      nameToSlug.set(tool.canonical_name.toLowerCase(), tool.slug)
      nameToSlug.set(tool.slug.toLowerCase(), tool.slug)
      for (const alias of tool.aliases ?? []) {
        nameToSlug.set(alias.toLowerCase(), tool.slug)
      }
    }

    // Group signals by (tool_slug, vertical). One signal can mention several
    // tools, so it lands in multiple buckets.
    const buckets = new Map<string, SignalRow[]>()
    for (const s of signals) {
      const seen = new Set<string>()
      for (const name of s.tool_names ?? []) {
        const slug = nameToSlug.get(name.toLowerCase())
        if (!slug || seen.has(slug)) continue
        seen.add(slug)
        const key = `${slug}::${s.vertical}`
        const arr = buckets.get(key) ?? []
        arr.push(s)
        buckets.set(key, arr)
      }
    }

    // For each tool × vertical, compute and insert.
    const writes: Array<{
      tool_slug: string
      vertical: string
      score: number
      signal_count: number
    }> = []
    let skipped = 0

    for (const tool of tools) {
      for (const vertical of tool.verticals) {
        const key = `${tool.slug}::${vertical}`
        const bucket = buckets.get(key)
        if (!bucket || bucket.length === 0) {
          skipped++
          continue
        }

        const baseline = pickBaseline(tool.workflow_stages, vertical, baselines)
        const result = computeScore(bucket, baseline)

        await sql`
          INSERT INTO tool_scores (
            tool_slug, vertical, score,
            speed_score, cost_score, quality_score, adoption_score,
            signal_ids, baseline_id, signal_count,
            snapshot_date, notes
          ) VALUES (
            ${tool.slug}, ${vertical}, ${result.score},
            ${result.speed_score}, ${result.cost_score},
            ${result.quality_score}, ${result.adoption_score},
            ${result.signal_ids}, ${result.baseline_id}, ${result.signal_count},
            ${today}, ${result.notes || null}
          )
          ON CONFLICT (tool_slug, vertical, snapshot_date) DO UPDATE SET
            score = EXCLUDED.score,
            speed_score = EXCLUDED.speed_score,
            cost_score = EXCLUDED.cost_score,
            quality_score = EXCLUDED.quality_score,
            adoption_score = EXCLUDED.adoption_score,
            signal_ids = EXCLUDED.signal_ids,
            baseline_id = EXCLUDED.baseline_id,
            signal_count = EXCLUDED.signal_count,
            notes = EXCLUDED.notes,
            computed_at = NOW()
        `

        writes.push({
          tool_slug: tool.slug,
          vertical,
          score: result.score,
          signal_count: result.signal_count,
        })
      }
    }

    // Mirror the latest score onto the tools table for cheap reads.
    // Aggregate: max score across verticals (the tool's "best" score).
    if (writes.length > 0) {
      await sql`
        UPDATE tools t SET
          current_score = sub.max_score,
          updated_at = NOW()
        FROM (
          SELECT tool_slug, MAX(score)::int AS max_score
          FROM tool_scores
          WHERE snapshot_date = ${today}
          GROUP BY tool_slug
        ) sub
        WHERE t.slug = sub.tool_slug
      `
    }

    return NextResponse.json({
      success: true,
      snapshot_date: today,
      tools_scored: writes.length,
      tools_skipped_no_signals: skipped,
      lookback_days: LOOKBACK_DAYS,
      duration_ms: Date.now() - startedAt,
      top: writes.sort((a, b) => b.score - a.score).slice(0, 10),
    })
  } catch (err) {
    console.error('[cron/score]', err)
    return NextResponse.json(
      {
        success: false,
        error: err instanceof Error ? err.message : 'Unknown error',
      },
      { status: 500 },
    )
  }
}
