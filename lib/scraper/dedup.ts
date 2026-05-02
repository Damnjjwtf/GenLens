/**
 * lib/scraper/dedup.ts
 *
 * Hash-based deduplication. SHA-256(title + source_url) is computed by parsers.
 * This module checks which hashes already exist in the signals table.
 *
 * Semantic dedup (Claude embeddings + cosine similarity) is GAPS #5, not in scope here.
 */

import { db as sql } from '@/lib/db'
import type { RawSignal } from './types'

/**
 * Returns only signals whose content_hash isn't already in the signals table.
 * Empty input → empty output.
 */
export async function filterNewSignals(signals: RawSignal[]): Promise<RawSignal[]> {
  if (signals.length === 0) return []

  const hashes = signals.map(s => s.content_hash)
  const existing = await sql`
    SELECT content_hash FROM signals
    WHERE content_hash = ANY(${hashes})
  ` as { content_hash: string }[]

  const existingSet = new Set(existing.map(r => r.content_hash))
  return signals.filter(s => !existingSet.has(s.content_hash))
}
