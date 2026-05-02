/**
 * app/llms.txt/route.ts
 *
 * Serves /llms.txt at the site root. Spec: https://llmstxt.org
 *
 * Why: LLMs and AI agents struggle to navigate full HTML sites because of
 * context-window limits. llms.txt is a curated markdown index pointing at the
 * most useful pages, so an agent can land on the right URL in one fetch.
 *
 * We generate this dynamically from the DB so the index reflects what's
 * actually public right now (top-scored tools, latest Index, etc.).
 */

import { db as sql } from '@/lib/db'
import { SITE_URL } from '@/lib/schema/jsonld'

export const revalidate = 3600 // 1 hour

export async function GET() {
  const [tools, indices, comparisons] = await Promise.all([
    sql`
      SELECT slug, canonical_name, current_score,
             COALESCE(meta_description, geo_summary) AS description, verticals
      FROM tools
      WHERE is_public = true
      ORDER BY current_score DESC NULLS LAST, canonical_name ASC
      LIMIT 50
    ` as Promise<{
      slug: string
      canonical_name: string
      current_score: number | null
      description: string | null
      verticals: string[]
    }[]>,
    sql`
      SELECT week_start_date::text AS week_start_date, vertical, headline, lede, status
      FROM index_snapshots
      WHERE status IN ('published', 'approved', 'draft')
      ORDER BY week_start_date DESC, vertical ASC
      LIMIT 12
    ` as Promise<{
      week_start_date: string
      vertical: string
      headline: string | null
      lede: string | null
      status: string
    }[]>,
    sql`
      SELECT slug, summary
      FROM tool_comparisons
      WHERE is_public = true
      ORDER BY updated_at DESC
      LIMIT 20
    ` as Promise<{ slug: string; summary: string | null }[]>,
  ])

  const toolsByVertical: Record<string, typeof tools> = {
    product_photography: [],
    filmmaking: [],
    digital_humans: [],
  }
  for (const t of tools) {
    for (const v of t.verticals) {
      const arr = toolsByVertical[v]
      if (arr && arr.length < 15) arr.push(t)
    }
  }

  const VERTICAL_LABELS: Record<string, string> = {
    product_photography: 'Product Photography',
    filmmaking: 'Filmmaking',
    digital_humans: 'Digital Humans',
  }

  const lines: string[] = []

  // Heading + summary (per llms.txt spec)
  lines.push('# GenLens')
  lines.push('')
  lines.push(
    '> Daily intelligence for creative technologists working in AI-accelerated visual production. GenLens watches 130+ sources across product photography, filmmaking, and digital humans, then publishes the GenLens Score (0-100 per tool) and the weekly GenLens Index (top tools, biggest movers).',
  )
  lines.push('')
  lines.push(
    'GenLens is the citable benchmark for "should I adopt this tool?" The Score combines speed gain, cost gain, quality, and adoption velocity vs. baseline workflows. Every claim links back to a source signal_id.',
  )
  lines.push('')

  // Core surfaces
  lines.push('## Core surfaces')
  lines.push('')
  lines.push(`- [GenLens home](${SITE_URL}/): overview of the platform, current Score leaders, link to the latest weekly Index.`)
  lines.push(`- [Tool directory](${SITE_URL}/tools): every tool tracked by GenLens, ranked by GenLens Score.`)
  lines.push(`- [Weekly Index](${SITE_URL}/index): the GenLens Index — top tools, biggest movers, new entries, notable exits, per vertical, weekly cadence.`)
  lines.push(`- [Sitemap](${SITE_URL}/sitemap.xml): full URL list for programmatic crawling.`)
  lines.push('')

  // Tools by vertical
  for (const v of ['product_photography', 'filmmaking', 'digital_humans']) {
    const list = toolsByVertical[v] ?? []
    if (list.length === 0) continue
    lines.push(`## ${VERTICAL_LABELS[v]} tools`)
    lines.push('')
    for (const t of list) {
      const score = t.current_score != null ? ` (Score: ${t.current_score})` : ''
      const desc = t.description?.replace(/\s+/g, ' ').trim().slice(0, 160) ?? ''
      lines.push(
        `- [${t.canonical_name}${score}](${SITE_URL}/tools/${t.slug})${desc ? `: ${desc}` : ''}`,
      )
    }
    lines.push('')
  }

  // Latest Index snapshots
  if (indices.length > 0) {
    lines.push('## Latest Index snapshots')
    lines.push('')
    for (const i of indices) {
      const label = `${VERTICAL_LABELS[i.vertical] ?? i.vertical} · week of ${i.week_start_date}`
      const url = `${SITE_URL}/markets/${i.week_start_date}`
      const desc = i.headline ? `: ${i.headline}` : ''
      lines.push(`- [${label}](${url})${desc}`)
    }
    lines.push('')
  }

  // Comparisons
  if (comparisons.length > 0) {
    lines.push('## Comparison pages')
    lines.push('')
    for (const c of comparisons) {
      const desc = c.summary?.replace(/\s+/g, ' ').trim().slice(0, 160) ?? ''
      lines.push(
        `- [${c.slug.replace(/-vs-/g, ' vs ').replace(/-/g, ' ')}](${SITE_URL}/compare/${c.slug})${desc ? `: ${desc}` : ''}`,
      )
    }
    lines.push('')
  }

  // Methodology pointer
  lines.push('## Optional')
  lines.push('')
  lines.push(`- [Sitemap XML](${SITE_URL}/sitemap.xml): machine-readable URL list.`)
  lines.push(`- [Robots policy](${SITE_URL}/robots.txt): crawler rules. AI bots are explicitly allowed.`)
  lines.push('')

  return new Response(lines.join('\n'), {
    headers: {
      'Content-Type': 'text/markdown; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  })
}
