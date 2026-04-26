/**
 * lib/scraper/parsers/html.ts
 *
 * Generic HTML scraper for sources without RSS feeds.
 * Heuristic article extraction: looks for h1/h2/h3 nodes wrapping anchor tags,
 * pairs each with the nearest paragraph or article excerpt.
 *
 * Per-source overrides can extend this later by adding a selectors map keyed by source.url.
 * For now: best-effort generic extraction across the 7 HTML sources in the registry.
 */

import * as cheerio from 'cheerio'
import crypto from 'node:crypto'
import type { Source } from '../sources'
import type { RawSignal } from '../types'

const MAX_ITEMS_PER_SOURCE = 15
const MAX_TITLE_LENGTH = 220
const MIN_TITLE_LENGTH = 12
const FETCH_TIMEOUT_MS = 12_000

export async function parseHtmlSource(source: Source): Promise<RawSignal[]> {
  const html = await fetchWithTimeout(source.url, FETCH_TIMEOUT_MS)
  const $ = cheerio.load(html)
  const baseUrl = new URL(source.url)

  const candidates: Array<{ title: string; href: string; excerpt: string }> = []

  // Strategy: find anchors inside heading tags, or anchors with role="article".
  // Filter to those whose href looks like an article (not nav, not anchor, not external nav).
  $('h1 a, h2 a, h3 a, article a, [role="article"] a').each((_, el) => {
    const $el = $(el)
    const title = $el.text().trim().replace(/\s+/g, ' ')
    const href = $el.attr('href')
    if (!title || !href) return
    if (title.length < MIN_TITLE_LENGTH || title.length > MAX_TITLE_LENGTH) return

    const absoluteUrl = resolveUrl(href, baseUrl)
    if (!absoluteUrl) return
    if (!isLikelyArticleUrl(absoluteUrl, baseUrl)) return

    // Find nearest paragraph as excerpt
    const $card = $el.closest('article, li, div, section').first()
    const excerpt = ($card.find('p').first().text() || $card.text() || '')
      .trim()
      .replace(/\s+/g, ' ')
      .slice(0, 600)

    candidates.push({ title, href: absoluteUrl, excerpt })
  })

  // Dedup by URL within this scrape, take top N
  const seen = new Set<string>()
  const unique = candidates.filter(c => {
    if (seen.has(c.href)) return false
    seen.add(c.href)
    return true
  }).slice(0, MAX_ITEMS_PER_SOURCE)

  return unique.map(c => {
    const content_hash = crypto
      .createHash('sha256')
      .update(`${c.title}\n${c.href}`)
      .digest('hex')

    const signal: RawSignal = {
      title: c.title,
      description: c.excerpt.slice(0, 2000),
      raw_content: c.excerpt.slice(0, 8000),
      source_url: c.href,
      source_name: source.name,
      source_platform: source.type,
      published_at: null,
      candidate_verticals: source.verticals,
      candidate_dimensions: source.dimensions,
      content_hash,
    }
    return signal
  })
}

// ─── Helpers ──────────────────────────────────────────────────

async function fetchWithTimeout(url: string, ms: number): Promise<string> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), ms)
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { 'User-Agent': 'GenLens/1.0 (+https://genlens.app)' },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`)
    return await res.text()
  } finally {
    clearTimeout(timer)
  }
}

function resolveUrl(href: string, base: URL): string | null {
  try {
    return new URL(href, base).toString()
  } catch {
    return null
  }
}

function isLikelyArticleUrl(url: string, base: URL): boolean {
  const u = new URL(url)
  if (u.hostname !== base.hostname) return false      // skip external links
  if (u.pathname === base.pathname) return false      // skip same page
  if (u.pathname === '/' || u.pathname.length < 4) return false // skip homepages
  if (/\.(jpg|png|gif|svg|pdf|zip|mp4)$/i.test(u.pathname)) return false
  if (/^#/.test(u.hash) && u.pathname === base.pathname) return false
  return true
}
