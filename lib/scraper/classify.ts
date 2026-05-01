/**
 * lib/scraper/classify.ts
 *
 * Claude taxonomy classifier. Takes RawSignals, returns full Classifications:
 * vertical, dimension, signal_type, tool_names, time/cost/quality deltas, summary.
 *
 * Batch size: 10 signals per Claude call (per CLAUDE.md convention).
 * Cost: ~$0.001 per signal at claude-sonnet-4-20250514 rates.
 */

import Anthropic from '@anthropic-ai/sdk'
import { ANTHROPIC_MODEL, VERTICALS } from '@/lib/constants'
import { resolveToolIds } from '@/lib/tools/normalize'
import type { RawSignal, Classification, SignalType } from './types'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY! })

const BATCH_SIZE = 10
const MAX_TOKENS = 4000

const SIGNAL_TYPES: SignalType[] = [
  'tool_release',
  'workflow_template',
  'cost_delta',
  'time_delta',
  'legal_alert',
  'hire_post',
  'cultural_trend',
  'integration',
  'benchmark',
  'research',
  'other',
]

/**
 * Classifies a list of raw signals via Claude.
 * Returns the same length as input, with null entries for signals that failed classification.
 */
export async function classifySignals(
  signals: RawSignal[]
): Promise<(Classification | null)[]> {
  if (signals.length === 0) return []

  const results: (Classification | null)[] = []

  for (let i = 0; i < signals.length; i += BATCH_SIZE) {
    const batch = signals.slice(i, i + BATCH_SIZE)
    const batchResults = await classifyBatch(batch)
    results.push(...batchResults)
  }

  return results
}

async function classifyBatch(batch: RawSignal[]): Promise<(Classification | null)[]> {
  const prompt = buildPrompt(batch)

  try {
    const response = await anthropic.messages.create({
      model: ANTHROPIC_MODEL,
      max_tokens: MAX_TOKENS,
      messages: [{ role: 'user', content: prompt }],
    })

    const text = response.content[0]?.type === 'text' ? response.content[0].text : ''
    const cleaned = text.replace(/```json|```/g, '').trim()
    const parsed = JSON.parse(cleaned) as { classifications: Array<Record<string, unknown>> }

    if (!Array.isArray(parsed.classifications)) {
      console.error('[classifier] missing classifications array')
      return batch.map(() => null)
    }

    const normalized: (Classification | null)[] = []
    for (let idx = 0; idx < batch.length; idx++) {
      const c = parsed.classifications[idx]
      if (!c) {
        normalized.push(null)
      } else {
        normalized.push(await normalize(c))
      }
    }
    return normalized
  } catch (err) {
    console.error('[classifier] batch failed:', err instanceof Error ? err.message : err)
    return batch.map(() => null)
  }
}

function buildPrompt(batch: RawSignal[]): string {
  const items = batch.map((s, i) => `
SIGNAL ${i}:
  source: ${s.source_name} (${s.source_platform})
  candidate verticals: ${s.candidate_verticals.join(', ')}
  candidate dimensions: ${s.candidate_dimensions.join(', ')}
  title: ${s.title}
  description: ${(s.description || s.raw_content).slice(0, 500)}
`).join('\n')

  return `You are GenLens's signal classifier. Map each scraped signal to GenLens's taxonomy.

${items}

For each signal, return JSON with these fields. Use the candidate hints when ambiguous, but override if the content clearly fits a different vertical/dimension.

Verticals: ${VERTICALS.join(' | ')}
Dimensions (1-10):
  1 = workflow_stage_signal (what changed in a bottleneck)
  2 = product_category (hard goods, soft goods, film types)
  3 = competitive_intelligence (what others are shipping)
  4 = workflow_template (proven method, time/cost breakdown)
  5 = cost_time_delta (quantified savings per release)
  6 = legal_ethical (see DIMENSION 6 GROUNDING below)
  7 = talent_hiring (see DIMENSION 7 GROUNDING below)
  8 = integration_compatibility (tool interop)
  9 = cultural_trend (aesthetic, market direction)
  10 = benchmark_leaderboard (rankings)

DIMENSION 6 GROUNDING (legal & ethical signals):
Classify under dimension 6 if the signal mentions any of:
  - SAG-AFTRA contracts (2024 Sound Recordings Code, 2025 Commercials Contract Digital Replica Rider)
  - Synthetic vocal performances, "Digital Voice Replicas", consent requirements
  - SRDF (Sound Recordings Distribution Fund) royalty pass-through to synthetic tracks
  - ELVIS Act (Tennessee voice/image/likeness)
  - NO FAKES Act (federal digital replica prohibition)
  - State digital replica laws (California, Illinois, New York)
  - RIAA litigation against AI music services (notably v. Suno and v. Udio)
  - Copyright infringement claims tied to AI training data
  - "Fair use" disputes over mass data ingestion
  - Deepfake legislation, disclosure requirements
  - Union contract riders covering AI / GAI / generative tools
Note: SAG-AFTRA's GAI definition explicitly EXCLUDES traditional CGI/VFX previs tools. A signal about standard CGI is not a Dimension 6 signal.

DIMENSION 7 GROUNDING (talent & hiring signals):
Classify under dimension 7 if the signal mentions any of:
  - Job listings, rate cards, salary ranges, hiring trends
  - Senior Gen AI Creative Engineers / Creative Technology Specialists ($112k–$280k+ range)
  - AI-pipeline Technical Director or applied generative technologist roles
  - Decline of generalist VFX hiring ("VFX puppy mill" model collapse, junior generalists automated out)
  - Required skills shifting toward Python scripting, API integration, bespoke AI tooling
  - Hiring boards: Motionographer Jobs, ShowbizJobs, VES Job Board
  - Studio rate cards, freelancer day rates, agency compensation benchmarks
  - "Architecting proprietary AI solutions" vs "operating consumer-grade interfaces"
Use signal_type='hire_post' for direct job listings, 'cost_delta' or 'cultural_trend' for compensation/market shifts.

Signal types: ${SIGNAL_TYPES.join(' | ')}

Numeric fields:
  time_saved_hours, cost_saved_dollars, quality_improvement_percent — extract ONLY if explicitly stated. Otherwise null.
  trending_score (0-100) — your judgment of how high-signal this is for working creatives. 70+ = unmissable, 40-69 = worth knowing, <40 = noise.

Output format (valid JSON, no markdown):
{
  "classifications": [
    {
      "vertical": "<one of verticals>",
      "dimension": <1-10>,
      "signal_type": "<one of signal types>",
      "summary": "1-2 sentence editorial summary. No em dashes. Cite the tool/company by name. End with confidence: (high), (medium), or (low).",
      "tool_names": ["KeyShot", "Runway", ...],
      "workflow_stages": ["render", "voice_gen", ...],
      "product_categories": ["hard_goods", ...],
      "time_saved_hours": <number or null>,
      "cost_saved_dollars": <number or null>,
      "quality_improvement_percent": <number or null>,
      "trending_score": <0-100>
    },
    ... (one per signal in order)
  ]
}

Constraints:
- Never fabricate numeric fields. Null if not stated.
- No em dashes anywhere.
- Confidence label required at the end of every summary.
`
}

async function normalize(c: Record<string, unknown>): Promise<Classification | null> {
  const vertical = c.vertical as Classification['vertical']
  if (!VERTICALS.includes(vertical as never)) return null

  const dimension = Number(c.dimension)
  if (!Number.isFinite(dimension) || dimension < 1 || dimension > 10) return null

  const signal_type = c.signal_type as SignalType
  if (!SIGNAL_TYPES.includes(signal_type)) return null

  const tool_names = Array.isArray(c.tool_names) ? (c.tool_names as string[]).slice(0, 10) : []
  let tool_ids: number[] | null = null

  if (tool_names.length > 0) {
    try {
      tool_ids = await resolveToolIds(tool_names)
    } catch (err) {
      console.warn('[classify] tool normalization failed:', err)
      tool_ids = null
    }
  }

  return {
    vertical,
    dimension,
    signal_type,
    summary: String(c.summary ?? '').slice(0, 1000),
    tool_names,
    tool_ids,
    workflow_stages: Array.isArray(c.workflow_stages) ? (c.workflow_stages as string[]).slice(0, 10) : [],
    product_categories: Array.isArray(c.product_categories) ? (c.product_categories as string[]).slice(0, 10) : [],
    time_saved_hours: typeof c.time_saved_hours === 'number' ? c.time_saved_hours : null,
    cost_saved_dollars: typeof c.cost_saved_dollars === 'number' ? c.cost_saved_dollars : null,
    quality_improvement_percent: typeof c.quality_improvement_percent === 'number' ? c.quality_improvement_percent : null,
    trending_score: clampInt(c.trending_score, 0, 100, 50),
  }
}

function clampInt(v: unknown, min: number, max: number, fallback: number): number {
  const n = Math.round(Number(v))
  if (!Number.isFinite(n)) return fallback
  return Math.max(min, Math.min(max, n))
}
