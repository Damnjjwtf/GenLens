/**
 * lib/score/compute.ts
 *
 * GenLens Score formula. Single 0-100 number per (tool, vertical).
 *
 * Composite weights (v1, tunable):
 *   speed     30%  — time saved vs. baseline_workflows.traditional_time_hours
 *   cost      30%  — cost saved vs. baseline_workflows.traditional_cost_dollars
 *   quality   15%  — proxy: density of benchmark/workflow_template signals
 *   adoption  25%  — averaged trending_score from input signals
 *
 * Defensibility:
 *   - Every output references signal_ids[] (the signals that drove the score)
 *   - When a baseline matches the tool's vertical + workflow_stage, baseline_id
 *     is stored. Otherwise the score still computes but flags missing baseline.
 *   - Stable: per-component clamping prevents one outlier signal from moving
 *     the composite by more than its weighted ceiling.
 *
 * Pure functions only. The cron route does the DB I/O.
 */

export interface ScoreSignal {
  id: number
  time_saved_hours: number | null
  cost_saved_dollars: number | null
  quality_improvement_percent: number | null
  trending_score: number | null
  signal_type: string
}

export interface ScoreBaseline {
  id: number
  traditional_time_hours: number
  traditional_cost_dollars: number
}

export interface ScoreOutput {
  score: number
  speed_score: number
  cost_score: number
  quality_score: number
  adoption_score: number
  signal_ids: number[]
  baseline_id: number | null
  signal_count: number
  notes: string
}

const WEIGHTS = {
  speed: 0.30,
  cost: 0.30,
  quality: 0.15,
  adoption: 0.25,
} as const

// Quality proxy: how many of these "high-trust" signal types appear?
const QUALITY_TYPES = new Set(['benchmark', 'workflow_template'])

// Without a baseline, fall back to absolute scaling. 20h saved = full speed score.
const FALLBACK_SPEED_CAP_HOURS = 20
const FALLBACK_COST_CAP_DOLLARS = 2000

// Quality proxy saturates at 5 high-trust signals = 100.
const QUALITY_CAP = 5

const clamp = (n: number, lo = 0, hi = 100): number =>
  Math.max(lo, Math.min(hi, n))

const median = (xs: number[]): number => {
  if (xs.length === 0) return 0
  const sorted = [...xs].sort((a, b) => a - b)
  const m = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[m] : (sorted[m - 1] + sorted[m]) / 2
}

const mean = (xs: number[]): number =>
  xs.length === 0 ? 0 : xs.reduce((a, b) => a + b, 0) / xs.length

export function computeScore(
  signals: ScoreSignal[],
  baseline: ScoreBaseline | null,
): ScoreOutput {
  const notes: string[] = []

  // ─── Speed component ───────────────────────────────────────
  // Median time_saved_hours across signals, anchored to baseline if we have one.
  const timeSavings = signals
    .map(s => s.time_saved_hours)
    .filter((x): x is number => typeof x === 'number' && x > 0)

  let speed_score = 0
  if (timeSavings.length > 0) {
    const med = median(timeSavings)
    if (baseline && baseline.traditional_time_hours > 0) {
      // Δ as a fraction of baseline. 14h saved against 14h baseline = 100.
      speed_score = clamp((med / baseline.traditional_time_hours) * 100)
    } else {
      // Absolute scaling fallback — 20h saved = 100, linear below.
      speed_score = clamp((med / FALLBACK_SPEED_CAP_HOURS) * 100)
      notes.push('speed:no-baseline-fallback')
    }
  }

  // ─── Cost component ────────────────────────────────────────
  const costSavings = signals
    .map(s => s.cost_saved_dollars)
    .filter((x): x is number => typeof x === 'number' && x > 0)

  let cost_score = 0
  if (costSavings.length > 0) {
    const med = median(costSavings)
    if (baseline && baseline.traditional_cost_dollars > 0) {
      cost_score = clamp((med / baseline.traditional_cost_dollars) * 100)
    } else {
      cost_score = clamp((med / FALLBACK_COST_CAP_DOLLARS) * 100)
      notes.push('cost:no-baseline-fallback')
    }
  }

  // ─── Quality component (proxy) ─────────────────────────────
  // Until we have real quality_improvement_percent at scale, count
  // benchmark + workflow_template signals as a high-trust proxy. The
  // assumption: tools that show up in benchmarks and template guides
  // tend to be the ones that pass quality bars.
  const qualitySignals = signals.filter(s => QUALITY_TYPES.has(s.signal_type))
  const realQuality = signals
    .map(s => s.quality_improvement_percent)
    .filter((x): x is number => typeof x === 'number' && x > 0)

  let quality_score = 0
  if (realQuality.length > 0) {
    quality_score = clamp(mean(realQuality))
  } else if (qualitySignals.length > 0) {
    quality_score = clamp((qualitySignals.length / QUALITY_CAP) * 100)
    notes.push('quality:proxy')
  }

  // ─── Adoption component ────────────────────────────────────
  // Averaged trending_score across the contributing signals, capped at 100.
  const trends = signals
    .map(s => s.trending_score)
    .filter((x): x is number => typeof x === 'number')
  const adoption_score = trends.length > 0 ? clamp(mean(trends)) : 0

  // ─── Composite ─────────────────────────────────────────────
  const score = Math.round(
    speed_score * WEIGHTS.speed +
      cost_score * WEIGHTS.cost +
      quality_score * WEIGHTS.quality +
      adoption_score * WEIGHTS.adoption,
  )

  return {
    score,
    speed_score: Math.round(speed_score),
    cost_score: Math.round(cost_score),
    quality_score: Math.round(quality_score),
    adoption_score: Math.round(adoption_score),
    signal_ids: signals.map(s => s.id),
    baseline_id: baseline?.id ?? null,
    signal_count: signals.length,
    notes: notes.join(' '),
  }
}

/**
 * Picks the best baseline match for a tool in a given vertical.
 *
 * Strategy:
 *   1. If the tool has workflow_stages[], find the baseline whose
 *      workflow_stage matches the tool's first stage.
 *   2. Otherwise, return null and let the formula use absolute fallback.
 *
 * We deliberately do NOT pick "any baseline in the vertical" as a fallback —
 * a wrong baseline produces worse scores than no baseline.
 */
export function pickBaseline(
  toolStages: string[] | null,
  vertical: string,
  baselines: Array<ScoreBaseline & { vertical: string; workflow_stage: string }>,
): ScoreBaseline | null {
  if (!toolStages || toolStages.length === 0) return null
  for (const stage of toolStages) {
    const match = baselines.find(
      b => b.vertical === vertical && b.workflow_stage === stage,
    )
    if (match) return match
  }
  return null
}
