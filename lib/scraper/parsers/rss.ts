/**
 * lib/scraper/parsers/rss.ts
 *
 * RSS / Atom parser. Covers ~85% of sources (blogs, Reddit, GitHub release feeds,
 * YouTube channel feeds, arXiv categories, Substacks, trade press).
 *
 * Returns RawSignal[] — pre-tagged with source metadata, ready for dedup + classification.
 */

import Parser from 'rss-parser'
import crypto from 'node:crypto'
import type { Source } from '../sources'
import type { RawSignal } from '../types'

const parser: Parser = new Parser({
  timeout: 10_000, // 10s per source
  headers: {
    'User-Agent': 'GenLens/1.0 (+https://genlens.app)',
  },
})

const MAX_ITEMS_PER_SOURCE = 20

export async function parseRssSource(source: Source): Promise<RawSignal[]> {
  const feed = await parser.parseURL(source.url)
  const items = (feed.items ?? []).slice(0, MAX_ITEMS_PER_SOURCE)

  return items.flatMap(item => {
    const title = (item.title ?? '').trim()
    const link = (item.link ?? '').trim()
    if (!title || !link) return []

    const description = (item.contentSnippet ?? item.summary ?? '').trim()
    const raw_content = (item.content ?? item['content:encoded'] ?? description).trim()
    const published_at = item.isoDate ? new Date(item.isoDate) : item.pubDate ? new Date(item.pubDate) : null

    const content_hash = crypto
      .createHash('sha256')
      .update(`${title}\n${link}`)
      .digest('hex')

    const signal: RawSignal = {
      title,
      description: description.slice(0, 2000),
      raw_content: raw_content.slice(0, 8000),
      source_url: link,
      source_name: source.name,
      source_platform: source.type,
      published_at,
      candidate_verticals: source.verticals,
      candidate_dimensions: source.dimensions,
      content_hash,
    }
    return [signal]
  })
}
