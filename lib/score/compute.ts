/**
 * lib/score/compute.ts
 *
 * GenLens Score computation.
 * Formula: (speed * 0.40) + (cost * 0.30) + (quality * 0.20) + (adoption * 0.10)
 *
 * All component scores are 0-100 scale.
 */

export interface ScoreSignal {
  id: number
  signal_type: string
  time_saved_hours: number | null
  cost_saved_dollars: number | null
  quality_improvement_percent: number | null
  trending_score: number | null
}

export interface ScoreBaseline {
  id: number
  traditional_time_hours: number
  traditional_cost_dollars: number
}

export interface ComputeResult {
  score: number
  speed_score: number
  cost_score: number
  quality_score: number
  adoption_score: number
  signal_ids: number[]
  baseline_id: number | null
  signal_count: number
  notes: string | null
}

/**
 * Normalize value to 0-100 with slight curve for granularity
 */
function normalizeScore(value: number): number {
  if (value < 0) return 0
  if (value >= 100) return 100
  return Math.min(100, value * 1.2)
}

/**
 * Calculate speed score from time savings vs baseline
 * Baseline = 2 hours average improvement
 */
function speedScoreFromSignals(signals: ScoreSignal[], baseline: ScoreBaseline | null): number {
  const withTime = signals.filter(s => s.time_saved_hours && s.time_saved_hours > 0)
  if (withTime.length === 0) return 50

  const avgTime = withTime.reduce((sum, s) => sum + (s.time_saved_hours || 0), 0) / withTime.length
  const improvement = (avgTime / 2) * 100
  return normalizeScore(improvement)
}

/**
 * Calculate cost score from cost savings vs baseline
 * Baseline = $150 average improvement
 */
function costScoreFromSignals(signals: ScoreSignal[], baseline: ScoreBaseline | null): number {
  const withCost = signals.filter(s => s.cost_saved_dollars && s.cost_saved_dollars > 0)
  if (withCost.length === 0) return 50

  const avgCost = withCost.reduce((sum, s) => sum + (s.cost_saved_dollars || 0), 0) / withCost.length
  const improvement = (avgCost / 150) * 100
  return normalizeScore(improvement)
}

/**
 * Quality score from signal classification (0-100)
 */
function qualityScoreFromSignals(signals: ScoreSignal[]): number {
  const withQuality = signals.filter(s => s.quality_improvement_percent != null)
  if (withQuality.length === 0) return 50

  const avgQuality = withQuality.reduce((sum, s) => sum + (s.quality_improvement_percent || 0), 0) / withQuality.length
  return Math.max(0, Math.min(100, avgQuality))
}

/**
 * Adoption score from trending_score (0-100)
 */
function adoptionScoreFromSignals(signals: ScoreSignal[]): number {
  const withTrending = signals.filter(s => s.trending_score != null)
  if (withTrending.length === 0) return 50

  const avgTrending = withTrending.reduce((sum, s) => sum + (s.trending_score || 0), 0) / withTrending.length
  return Math.max(0, Math.min(100, avgTrending))
}

/**
 * Compute composite score from signals and baseline
 */
export function computeScore(signals: ScoreSignal[], baseline: ScoreBaseline | null): ComputeResult {
  const speedScore = speedScoreFromSignals(signals, baseline)
  const costScore = costScoreFromSignals(signals, baseline)
  const qualityScore = qualityScoreFromSignals(signals)
  const adoptionScore = adoptionScoreFromSignals(signals)

  const composite = Math.round(speedScore * 0.4 + costScore * 0.3 + qualityScore * 0.2 + adoptionScore * 0.1)

  return {
    score: composite,
    speed_score: Math.round(speedScore),
    cost_score: Math.round(costScore),
    quality_score: Math.round(qualityScore),
    adoption_score: Math.round(adoptionScore),
    signal_ids: signals.map(s => s.id),
    baseline_id: baseline?.id || null,
    signal_count: signals.length,
    notes: null,
  }
}

/**
 * Pick best baseline for a tool given its workflow stages and vertical
 */
export function pickBaseline(
  workflowStages: string[] | null,
  vertical: string,
  baselines: Array<{ id: number; vertical: string; workflow_stage: string }>,
): { id: number; vertical: string; workflow_stage: string } | null {
  if (!workflowStages || workflowStages.length === 0) return null

  // Find baseline matching vertical and one of the tool's workflow stages
  for (const stage of workflowStages) {
    const match = baselines.find(b => b.vertical === vertical && b.workflow_stage === stage)
    if (match) return match
  }

  // Fallback: any baseline for this vertical
  return baselines.find(b => b.vertical === vertical) || null
}
