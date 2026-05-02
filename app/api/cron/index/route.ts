/**
 * app/api/cron/index/route.ts
 *
 * Vercel Cron entry for the weekly Index generator.
 * Schedule: 0 7 * * 1 (Monday 07:00 UTC), defined in vercel.json.
 *
 * For each active vertical:
 *   1. Pull latest tool_scores per tool (this week's snapshot)
 *   2. Pull tool_scores from ≥7 days earlier (last week's snapshot)
 *   3. Compute top 10, movers, new entries, notable exits
 *   4. Ask Claude for a headline + lede
 *   5. UPSERT into index_snapshots with status = 'draft'
 *
 * Drafts wait for human approval (admin UI) before being marked 'published'.
 *
 * Auth: Bearer ${CRON_SECRET}.
 */

import { NextRequest, NextResponse } from 'next/server'
import { db as sql } from '@/lib/db'
import Anthropic from '@anthropic-ai/sdk'
import { ANTHROPIC_MODEL_AGENT, VERTICALS } from '@/lib/constants'
import {
  buildIndex,
  summarizeForEditorial,
  type ScoreSnapshot,
  type IndexResult,
} from '@/lib/index/generate'

export const maxDuration = 120

const claude = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY! })

interface ScoreRow {
  tool_slug: string
  vertical: string
  score: number
  snapshot_date: string
}

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get('authorization')
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const startedAt = Date.now()

  try {
    // Week-start: Monday of the current week (UTC). Used as the canonical
    // index key. Two runs in the same week overwrite via UPSERT.
    const now = new Date()
    const weekStart = mondayOf(now)
    const weekStartIso = weekStart.toISOString().slice(0, 10)
    const prevWeekCutoff = new Date(weekStart.getTime() - 14 * 86400_000)
      .toISOString()
      .slice(0, 10)

    // Latest snapshot per (tool_slug, vertical) — DISTINCT ON sorts by date desc.
    const currentRows = (await sql`
      SELECT DISTINCT ON (tool_slug, vertical)
        tool_slug, vertical, score, snapshot_date::text AS snapshot_date
      FROM tool_scores
      WHERE snapshot_date >= ${prevWeekCutoff}
      ORDER BY tool_slug, vertical, snapshot_date DESC
    `) as unknown as ScoreRow[]

    // Snapshot from ≥7 days before the latest per (tool, vertical).
    // Cap on prev_week_cutoff prevents reaching back forever and dragging
    // in noise from old data.
    const previousRows = (await sql`
      SELECT DISTINCT ON (tool_slug, vertical)
        tool_slug, vertical, score, snapshot_date::text AS snapshot_date
      FROM tool_scores
      WHERE snapshot_date <= ${weekStartIso}::date - INTERVAL '7 days'
        AND snapshot_date >= ${prevWeekCutoff}
      ORDER BY tool_slug, vertical, snapshot_date DESC
    `) as unknown as ScoreRow[]

    // Group by vertical for buildIndex
    const byVerticalCurrent = new Map<string, ScoreSnapshot[]>()
    const byVerticalPrev = new Map<string, ScoreSnapshot[]>()
    for (const r of currentRows) {
      const arr = byVerticalCurrent.get(r.vertical) ?? []
      arr.push(r)
      byVerticalCurrent.set(r.vertical, arr)
    }
    for (const r of previousRows) {
      const arr = byVerticalPrev.get(r.vertical) ?? []
      arr.push(r)
      byVerticalPrev.set(r.vertical, arr)
    }

    const written: Array<{ vertical: string; top: number; movers_up: number; movers_down: number }> = []

    for (const vertical of VERTICALS) {
      const current = byVerticalCurrent.get(vertical) ?? []
      const previous = byVerticalPrev.get(vertical) ?? []

      if (current.length === 0) continue

      const result = buildIndex(vertical, current, previous)
      const editorial = await generateEditorial(result, weekStartIso)

      await sql`
        INSERT INTO index_snapshots (
          vertical, week_start_date,
          top_tools, biggest_movers_up, biggest_movers_down,
          new_entries, notable_exits,
          headline, lede,
          status, generated_at, updated_at
        ) VALUES (
          ${vertical}, ${weekStartIso},
          ${JSON.stringify(result.top_tools)},
          ${JSON.stringify(result.biggest_movers_up)},
          ${JSON.stringify(result.biggest_movers_down)},
          ${JSON.stringify(result.new_entries)},
          ${JSON.stringify(result.notable_exits)},
          ${editorial.headline},
          ${editorial.lede},
          'draft', NOW(), NOW()
        )
        ON CONFLICT (vertical, week_start_date) DO UPDATE SET
          top_tools = EXCLUDED.top_tools,
          biggest_movers_up = EXCLUDED.biggest_movers_up,
          biggest_movers_down = EXCLUDED.biggest_movers_down,
          new_entries = EXCLUDED.new_entries,
          notable_exits = EXCLUDED.notable_exits,
          headline = COALESCE(index_snapshots.headline, EXCLUDED.headline),
          lede = COALESCE(index_snapshots.lede, EXCLUDED.lede),
          updated_at = NOW()
      `

      written.push({
        vertical,
        top: result.top_tools.length,
        movers_up: result.biggest_movers_up.length,
        movers_down: result.biggest_movers_down.length,
      })
    }

    return NextResponse.json({
      success: true,
      week_start_date: weekStartIso,
      verticals_written: written,
      duration_ms: Date.now() - startedAt,
    })
  } catch (err) {
    console.error('[cron/index]', err)
    return NextResponse.json(
      { success: false, error: err instanceof Error ? err.message : 'Unknown error' },
      { status: 500 },
    )
  }
}

/**
 * Asks Claude for a tight headline + 2-sentence lede. Voice: Bloomberg
 * Terminal meets creative studio. Confident, terse, data-anchored.
 *
 * Returns conservative fallbacks if Claude fails — the snapshot is still
 * publishable; an editor can rewrite from the admin UI.
 */
async function generateEditorial(
  result: IndexResult,
  weekStart: string,
): Promise<{ headline: string; lede: string }> {
  const summary = summarizeForEditorial(result)
  const verticalLabel = result.vertical.replace(/_/g, ' ')

  try {
    const response = await claude.messages.create({
      model: ANTHROPIC_MODEL_AGENT,
      max_tokens: 400,
      messages: [
        {
          role: 'user',
          content: `You are the editor for the GenLens Index, a weekly snapshot of which AI creative tools are winning. Voice: Bloomberg Terminal meets creative studio. Confident, terse, data-anchored. Never hype without numbers behind it.

This week's data for ${verticalLabel} (week of ${weekStart}):

${summary}

Write:
1. headline — under 80 chars. Declarative. Lead with the most interesting movement (top mover, top entry, or the leader's lead).
2. lede — 2 sentences, max 280 chars total. Sentence one: what mattered. Sentence two: what it means for creators.

Output JSON only, no markdown:
{"headline": "...", "lede": "..."}`,
        },
      ],
    })

    const text = response.content[0].type === 'text' ? response.content[0].text : ''
    const parsed = JSON.parse(text.replace(/```json|```/g, '').trim()) as {
      headline?: string
      lede?: string
    }
    if (parsed.headline && parsed.lede) {
      return { headline: parsed.headline, lede: parsed.lede }
    }
  } catch (err) {
    console.error('[cron/index] editorial generation failed:', err)
  }

  // Fallback: deterministic headline from the data so the snapshot is still useful.
  const top = result.top_tools[0]
  const upMover = result.biggest_movers_up[0]
  const headline =
    upMover && upMover.delta > 0
      ? `${upMover.tool_slug} jumps ${upMover.delta} points in ${verticalLabel}`
      : top
        ? `${top.tool_slug} leads ${verticalLabel} at ${top.score}`
        : `${verticalLabel} index — ${weekStart}`
  return {
    headline,
    lede: `Top tools across ${verticalLabel} this week, ranked by GenLens Score. ${result.top_tools.length} tools tracked.`,
  }
}

function mondayOf(d: Date): Date {
  const utc = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()))
  const day = utc.getUTCDay() // 0 = Sun, 1 = Mon, ...
  const diff = day === 0 ? -6 : 1 - day
  utc.setUTCDate(utc.getUTCDate() + diff)
  return utc
}
