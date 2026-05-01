/**
 * lib/scraper/types.ts
 *
 * Shared types for the scraper pipeline.
 */

import type { Vertical, SourceType } from './sources'

/**
 * RawSignal — output of a parser, before classification.
 * Pre-tagged with source-level metadata. The classifier later refines
 * vertical, dimension, signal_type, tool_names, time/cost deltas.
 */
export interface RawSignal {
  title: string
  description: string
  raw_content: string
  source_url: string
  source_name: string
  source_platform: SourceType
  published_at: Date | null

  // From source registry — used as classifier hints
  candidate_verticals: Vertical[]
  candidate_dimensions: number[]

  // SHA-256(title + source_url)
  content_hash: string
}

/**
 * Classification — output of the Claude taxonomy pass.
 * Maps a RawSignal to the columns of the signals table.
 */
export interface Classification {
  vertical: Vertical
  dimension: number               // 1-10
  signal_type: SignalType
  summary: string                 // 1-2 sentence editorial summary
  tool_names: string[]
  tool_ids: number[] | null       // resolved tool IDs (populated by normalization)
  workflow_stages: string[]
  product_categories: string[]
  time_saved_hours: number | null
  cost_saved_dollars: number | null
  quality_improvement_percent: number | null
  trending_score: number          // 0-100
}

export type SignalType =
  | 'tool_release'        // new product, version, feature
  | 'workflow_template'   // someone documented a pipeline
  | 'cost_delta'          // pricing change, free tier shift
  | 'time_delta'          // workflow speedup quantified
  | 'legal_alert'         // SAG-AFTRA, copyright, deepfake regulation
  | 'hire_post'           // job listing, rate card
  | 'cultural_trend'      // aesthetic / market signal
  | 'integration'         // tool A now works with tool B
  | 'benchmark'           // leaderboard / comparison data
  | 'research'            // arXiv paper, academic finding
  | 'other'

export interface ScrapeResult {
  source_name: string
  source_url: string
  signals_found: number
  signals_new: number     // after dedup
  duration_ms: number
  status: 'ok' | 'error'
  error_message?: string
}
