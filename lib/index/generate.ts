/**
 * lib/index/generate.ts
 *
 * Pure functions that turn two weeks of tool_scores into an Index snapshot.
 *
 * The weekly Index publishes:
 *   - Top 10 tools by current score (per vertical)
 *   - Biggest movers up (top 5 by score delta, week-over-week)
 *   - Biggest movers down (top 5)
 *   - New entries (tools crossing the threshold this week)
 *   - Notable exits (tools dropping below the threshold)
 *
 * "This week" = the most recent snapshot_date per (tool, vertical).
 * "Last week" = the closest snapshot_date ≥ 7 days older than this week's.
 *
 * Threshold for entries/exits: SCORE_THRESHOLD (currently 10). Tools below
 * this don't count as meaningfully present in the Index.
 *
 * Pure: no I/O. The cron route does the SELECTs and INSERTs.
 */

export const SCORE_THRESHOLD = 10
export const TOP_N = 10
export const MOVERS_N = 5

export interface ScoreSnapshot {
  tool_slug: string
  vertical: string
  score: number
  snapshot_date: string // ISO date
}

export interface TopEntry {
  rank: number
  tool_slug: string
  score: number
  score_delta: number | null // vs. last week, null if not present last week
}

export interface MoverEntry {
  tool_slug: string
  score: number
  prev_score: number
  delta: number
}

export interface ChangeEntry {
  tool_slug: string
  score: number
  prev_score: number | null
}

export interface IndexResult {
  vertical: string
  top_tools: TopEntry[]
  biggest_movers_up: MoverEntry[]
  biggest_movers_down: MoverEntry[]
  new_entries: ChangeEntry[]
  notable_exits: ChangeEntry[]
}

/**
 * Builds the Index payload for a single vertical from two latest snapshots
 * per tool. Caller passes:
 *   - current: latest snapshot per tool in this vertical
 *   - previous: snapshot from ≥7 days earlier per tool (may be missing)
 */
export function buildIndex(
  vertical: string,
  current: ScoreSnapshot[],
  previous: ScoreSnapshot[],
): IndexResult {
  const prevMap = new Map(previous.map(s => [s.tool_slug, s.score]))

  // Sort current high → low for top tools
  const sorted = [...current].sort((a, b) => b.score - a.score)

  const top_tools: TopEntry[] = sorted.slice(0, TOP_N).map((s, i) => {
    const prev = prevMap.get(s.tool_slug)
    return {
      rank: i + 1,
      tool_slug: s.tool_slug,
      score: s.score,
      score_delta: prev != null ? s.score - prev : null,
    }
  })

  // Movers — only tools present in BOTH weeks (so the delta is meaningful)
  const movers: MoverEntry[] = []
  for (const s of current) {
    const prev = prevMap.get(s.tool_slug)
    if (prev == null) continue
    movers.push({
      tool_slug: s.tool_slug,
      score: s.score,
      prev_score: prev,
      delta: s.score - prev,
    })
  }

  const biggest_movers_up = [...movers]
    .filter(m => m.delta > 0)
    .sort((a, b) => b.delta - a.delta)
    .slice(0, MOVERS_N)

  const biggest_movers_down = [...movers]
    .filter(m => m.delta < 0)
    .sort((a, b) => a.delta - b.delta)
    .slice(0, MOVERS_N)

  // New entries: above threshold this week, below threshold (or absent) last week
  const new_entries: ChangeEntry[] = current
    .filter(s => {
      if (s.score < SCORE_THRESHOLD) return false
      const prev = prevMap.get(s.tool_slug)
      return prev == null || prev < SCORE_THRESHOLD
    })
    .map(s => ({
      tool_slug: s.tool_slug,
      score: s.score,
      prev_score: prevMap.get(s.tool_slug) ?? null,
    }))
    .sort((a, b) => b.score - a.score)

  // Notable exits: above threshold last week, below (or absent) this week
  const currentMap = new Map(current.map(s => [s.tool_slug, s.score]))
  const notable_exits: ChangeEntry[] = previous
    .filter(s => {
      if (s.score < SCORE_THRESHOLD) return false
      const cur = currentMap.get(s.tool_slug)
      return cur == null || cur < SCORE_THRESHOLD
    })
    .map(s => ({
      tool_slug: s.tool_slug,
      score: currentMap.get(s.tool_slug) ?? 0,
      prev_score: s.score,
    }))
    .sort((a, b) => b.prev_score - a.prev_score)

  return {
    vertical,
    top_tools,
    biggest_movers_up,
    biggest_movers_down,
    new_entries,
    notable_exits,
  }
}

/**
 * Builds the human-readable summary input that goes to Claude for editorial.
 * Kept here so the prompt logic stays close to the data shape.
 */
export function summarizeForEditorial(result: IndexResult): string {
  const lines: string[] = []
  lines.push(`Vertical: ${result.vertical}`)
  lines.push(`Top tools (rank, slug, score, Δ vs last week):`)
  for (const t of result.top_tools) {
    const d = t.score_delta == null ? 'new' : (t.score_delta > 0 ? `+${t.score_delta}` : `${t.score_delta}`)
    lines.push(`  ${t.rank}. ${t.tool_slug} — ${t.score} (${d})`)
  }
  if (result.biggest_movers_up.length > 0) {
    lines.push(`Biggest movers up: ${result.biggest_movers_up.map(m => `${m.tool_slug} +${m.delta}`).join(', ')}`)
  }
  if (result.biggest_movers_down.length > 0) {
    lines.push(`Biggest movers down: ${result.biggest_movers_down.map(m => `${m.tool_slug} ${m.delta}`).join(', ')}`)
  }
  if (result.new_entries.length > 0) {
    lines.push(`New entries: ${result.new_entries.map(e => `${e.tool_slug} (${e.score})`).join(', ')}`)
  }
  if (result.notable_exits.length > 0) {
    lines.push(`Notable exits: ${result.notable_exits.map(e => `${e.tool_slug} (was ${e.prev_score})`).join(', ')}`)
  }
  return lines.join('\n')
}
