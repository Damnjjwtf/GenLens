/**
 * lib/scraper/orchestrator.ts
 *
 * Coordinates the full scrape pipeline:
 *   1. Iterate sources from registry, fetch in batches of 5 with 1s delay
 *   2. Per-source: parse → dedup → collect raw signals
 *   3. Classify all new raw signals via Claude (batched 10/call)
 *   4. Insert into signals table with status='classified'
 *   5. Log per-source results to scrape_log
 *
 * Concurrency: 5 parallel scrapes, Promise.allSettled, 1s delay between batches.
 * One source failing does not abort the run.
 */

import { neon } from '@neondatabase/serverless'
import { SOURCES, type Source } from './sources'
import { parseRssSource } from './parsers/rss'
import { parseHtmlSource } from './parsers/html'
import { filterNewSignals } from './dedup'
import { classifySignals } from './classify'
import type { RawSignal, ScrapeResult, Classification } from './types'

const sql = neon(process.env.DATABASE_URL!)

const CONCURRENCY = 5
const BATCH_DELAY_MS = 1000

export interface OrchestratorReport {
  sources_total: number
  sources_ok: number
  sources_error: number
  signals_found: number
  signals_new: number
  signals_classified: number
  signals_inserted: number
  duration_ms: number
  per_source: ScrapeResult[]
}

export async function runScraper(opts: { sourceFilter?: (s: Source) => boolean } = {}): Promise<OrchestratorReport> {
  const startedAt = Date.now()
  const sources = (opts.sourceFilter ? SOURCES.filter(opts.sourceFilter) : SOURCES)

  const allRawSignals: RawSignal[] = []
  const perSource: ScrapeResult[] = []

  // Stage 1: parallel scrape in batches of CONCURRENCY
  for (let i = 0; i < sources.length; i += CONCURRENCY) {
    const batch = sources.slice(i, i + CONCURRENCY)
    const results = await Promise.allSettled(batch.map(scrapeOneSource))

    for (let j = 0; j < results.length; j++) {
      const source = batch[j]
      const r = results[j]
      if (r.status === 'fulfilled') {
        perSource.push(r.value.result)
        allRawSignals.push(...r.value.signals)
      } else {
        const err = r.reason instanceof Error ? r.reason.message : String(r.reason)
        perSource.push({
          source_name: source.name,
          source_url: source.url,
          signals_found: 0,
          signals_new: 0,
          duration_ms: 0,
          status: 'error',
          error_message: err.slice(0, 500),
        })
      }
    }

    if (i + CONCURRENCY < sources.length) {
      await sleep(BATCH_DELAY_MS)
    }
  }

  // Stage 2: dedup against signals table
  const newSignals = await filterNewSignals(allRawSignals)

  // Stage 3: classify via Claude
  const classifications = await classifySignals(newSignals)

  // Stage 4: insert classified signals
  let inserted = 0
  for (let k = 0; k < newSignals.length; k++) {
    const raw = newSignals[k]
    const cls = classifications[k]
    if (!cls) continue
    try {
      await insertSignal(raw, cls)
      inserted++
    } catch (err) {
      console.error('[orchestrator] insert failed for', raw.source_url, err instanceof Error ? err.message : err)
    }
  }

  // Stage 5: persist per-source log
  for (const r of perSource) {
    try {
      await sql`
        INSERT INTO scrape_log (source_name, source_url, status, signals_found, signals_new, error_message, duration_ms)
        VALUES (${r.source_name}, ${r.source_url}, ${r.status}, ${r.signals_found}, ${r.signals_new}, ${r.error_message ?? null}, ${r.duration_ms})
      `
    } catch (err) {
      console.error('[orchestrator] scrape_log write failed:', err instanceof Error ? err.message : err)
    }
  }

  const durationMs = Date.now() - startedAt
  return {
    sources_total: sources.length,
    sources_ok: perSource.filter(r => r.status === 'ok').length,
    sources_error: perSource.filter(r => r.status === 'error').length,
    signals_found: allRawSignals.length,
    signals_new: newSignals.length,
    signals_classified: classifications.filter(c => c !== null).length,
    signals_inserted: inserted,
    duration_ms: durationMs,
    per_source: perSource,
  }
}

// ─── Per-source scrape ────────────────────────────────────────

async function scrapeOneSource(source: Source): Promise<{ result: ScrapeResult; signals: RawSignal[] }> {
  const t0 = Date.now()
  try {
    let parsed: RawSignal[]
    switch (source.type) {
      case 'rss':
        parsed = await parseRssSource(source)
        break
      case 'html':
        parsed = await parseHtmlSource(source)
        break
      case 'discord':
      case 'conference':
        // Manual / annual sources, skipped in the daily pipeline
        parsed = []
        break
      default:
        parsed = []
    }

    // Source-level dedup (in case the feed itself duplicates an item)
    const seen = new Set<string>()
    const unique = parsed.filter(s => {
      if (seen.has(s.content_hash)) return false
      seen.add(s.content_hash)
      return true
    })

    // We don't filter against DB here — orchestrator does that across the full set
    return {
      signals: unique,
      result: {
        source_name: source.name,
        source_url: source.url,
        signals_found: unique.length,
        signals_new: 0,           // filled in later if needed
        duration_ms: Date.now() - t0,
        status: 'ok',
      },
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    return {
      signals: [],
      result: {
        source_name: source.name,
        source_url: source.url,
        signals_found: 0,
        signals_new: 0,
        duration_ms: Date.now() - t0,
        status: 'error',
        error_message: msg.slice(0, 500),
      },
    }
  }
}

// ─── Insert classified signal ─────────────────────────────────

async function insertSignal(raw: RawSignal, cls: Classification): Promise<void> {
  await sql`
    INSERT INTO signals (
      vertical, dimension, signal_type, title, description, summary, raw_content,
      workflow_stages, product_categories, tool_names, tool_ids,
      time_saved_hours, cost_saved_dollars, quality_improvement_percent,
      source_url, source_platform, source_name,
      trending_score, content_hash, published_at, status
    ) VALUES (
      ${cls.vertical}, ${cls.dimension}, ${cls.signal_type}, ${raw.title}, ${raw.description}, ${cls.summary}, ${raw.raw_content},
      ${cls.workflow_stages}, ${cls.product_categories}, ${cls.tool_names}, ${cls.tool_ids ?? null},
      ${cls.time_saved_hours}, ${cls.cost_saved_dollars}, ${cls.quality_improvement_percent},
      ${raw.source_url}, ${raw.source_platform}, ${raw.source_name},
      ${cls.trending_score}, ${raw.content_hash}, ${raw.published_at?.toISOString() ?? null}, 'classified'
    )
    ON CONFLICT (content_hash) DO NOTHING
  `
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
