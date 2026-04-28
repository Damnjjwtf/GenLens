/**
 * app/index/[date]/page.tsx
 *
 * Public Index page for a specific week.
 * Renders: headline, lede, top 10 tools, movers, new/exits per vertical.
 * No auth required. Shareable via OG tags.
 *
 * genlens.app/index/2026-04-28  (or /index/filmmaking-2026-04-28)
 */

import { neon } from '@neondatabase/serverless'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { breadcrumbLD, SITE_URL } from '@/lib/schema/jsonld'

const sql = neon(process.env.DATABASE_URL!)

interface Params { params: { date: string } }

// Parse date from slug: either YYYY-MM-DD or vertical-YYYY-MM-DD
function parseIndexSlug(slug: string): { vertical?: string; date: string } {
  const parts = slug.split('-')
  if (parts.length === 3) {
    // YYYY-MM-DD
    return { date: slug, vertical: undefined }
  }
  // vertical-YYYY-MM-DD (last 3 parts are the date)
  const date = parts.slice(-3).join('-')
  const vertical = parts.slice(0, -3).join('-')
  return { date, vertical }
}

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { vertical, date } = parseIndexSlug(params.date)

  let snapshot: any
  if (vertical) {
    [snapshot] = await sql`SELECT * FROM index_snapshots WHERE vertical = ${vertical} AND week_start_date = ${date} AND status = 'published' LIMIT 1`
  } else {
    [snapshot] = await sql`SELECT * FROM index_snapshots WHERE week_start_date = ${date} AND status = 'published' LIMIT 1`
  }

  if (!snapshot) {
    return { title: 'Index not found — GenLens' }
  }

  const verticalLabel = snapshot.vertical === 'all' ? 'GenLens' : snapshot.vertical.replace(/_/g, ' ')
  const title = snapshot.headline || `GenLens Index for week of ${snapshot.week_start_date}`

  return {
    title: `${title} — GenLens Index`,
    description: snapshot.lede || `This week's top AI creative tools and movers.`,
    openGraph: {
      title,
      description: snapshot.lede || `This week's top AI creative tools and movers.`,
      url: `https://genlens.app/index/${params.date}`,
      siteName: 'GenLens',
      type: 'article',
      images: [`https://genlens.app/api/og/index/${params.date}`],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description: snapshot.lede || `This week's top AI creative tools and movers.`,
      images: [`https://genlens.app/api/og/index/${params.date}`],
    },
    alternates: { canonical: `https://genlens.app/index/${params.date}` },
  }
}

const VERTICAL_LABELS: Record<string, string> = {
  product_photography: 'Product Photography',
  filmmaking: 'Filmmaking',
  digital_humans: 'Digital Humans',
  all: 'All Verticals',
}

const VERTICAL_ACCENT: Record<string, string> = {
  product_photography: '#c8f04a',
  filmmaking: '#f0a83c',
  digital_humans: '#b07af0',
  all: '#c8f04a',
}

export default async function IndexPage({ params }: Params) {
  const { vertical, date } = parseIndexSlug(params.date)

  // Fetch the snapshot
  let snapshot: any
  if (vertical) {
    [snapshot] = await sql`SELECT * FROM index_snapshots WHERE vertical = ${vertical} AND week_start_date = ${date} AND status = 'published' LIMIT 1`
  } else {
    [snapshot] = await sql`SELECT * FROM index_snapshots WHERE week_start_date = ${date} AND status = 'published' LIMIT 1`
  }

  if (!snapshot) notFound()

  // Fetch tool details for all tools in the snapshot
  const allToolSlugs = [
    ...(snapshot.top_tools || []).map((t: any) => t.tool_slug),
    ...(snapshot.biggest_movers_up || []).map((t: any) => t.tool_slug),
    ...(snapshot.biggest_movers_down || []).map((t: any) => t.tool_slug),
    ...(snapshot.new_entries || []).map((t: any) => t.tool_slug),
    ...(snapshot.notable_exits || []).map((t: any) => t.tool_slug),
  ].filter((v, i, a) => a.indexOf(v) === i)

  const tools = allToolSlugs.length > 0
    ? await sql`SELECT id, slug, canonical_name, affiliate_url, current_score FROM tools WHERE slug = ANY(${allToolSlugs})`
    : []

  const toolMap = new Map(tools.map((t: any) => [t.slug, t]))

  const accent = VERTICAL_ACCENT[snapshot.vertical] ?? '#c8f04a'
  const verticalLabel = VERTICAL_LABELS[snapshot.vertical] ?? snapshot.vertical
  const indexUrl = `${SITE_URL}/index/${params.date}`

  const jsonLd: object[] = [
    {
      '@context': 'https://schema.org',
      '@type': 'NewsArticle',
      headline: snapshot.headline || `GenLens Index — Week of ${snapshot.week_start_date}`,
      description: snapshot.lede,
      datePublished: snapshot.published_at,
      url: indexUrl,
      publisher: {
        '@type': 'Organization',
        name: 'GenLens',
        url: SITE_URL,
      },
    },
    breadcrumbLD([
      { name: 'GenLens', url: SITE_URL },
      { name: 'Index', url: `${SITE_URL}/index` },
      { name: verticalLabel, url: indexUrl },
    ]),
  ]

  return (
    <article style={{ ...styles.page, '--accent': accent } as React.CSSProperties}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <nav aria-label="Breadcrumb" style={styles.breadcrumb}>
        <a href="/" style={{ ...styles.link, color: accent }}>GenLens</a>
        <span style={styles.sep}>/</span>
        <a href="/index" style={{ ...styles.link, color: accent }}>Index</a>
        <span style={styles.sep}>/</span>
        <span style={styles.muted}>{verticalLabel}</span>
      </nav>

      <header style={styles.header}>
        <div style={styles.indexMeta}>
          <span style={{ ...styles.verticalBadge, borderColor: accent + '44', color: accent, background: accent + '10' }}>
            {verticalLabel}
          </span>
          <time style={styles.dateMuted}>
            Week of {new Date(snapshot.week_start_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </time>
        </div>

        <h1 style={styles.title}>
          {snapshot.headline || `GenLens Index`}
        </h1>

        {snapshot.lede && (
          <p style={styles.lede}>{snapshot.lede}</p>
        )}
      </header>

      <div style={styles.body}>
        {/* Top 10 Tools */}
        {snapshot.top_tools && snapshot.top_tools.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: accent }}>Top 10 Tools</h2>
            <div style={styles.toolGrid}>
              {snapshot.top_tools.map((tool: any, i: number) => {
                const details = toolMap.get(tool.tool_slug)
                return (
                  <a
                    key={tool.tool_slug}
                    href={`/tools/${tool.tool_slug}`}
                    style={{
                      ...styles.toolCard,
                      borderColor: accent + '44',
                      background: accent + '06',
                    }}
                  >
                    <div style={styles.toolRank}>{i + 1}</div>
                    <div style={styles.toolName}>{details?.canonical_name || tool.tool_slug}</div>
                    <div style={styles.toolScore}>{tool.score}</div>
                    {tool.score_delta != null && (
                      <div style={{ ...styles.toolDelta, color: tool.score_delta > 0 ? '#4ae60b' : '#ff6b6b' }}>
                        {tool.score_delta > 0 ? '+' : ''}{tool.score_delta}
                      </div>
                    )}
                  </a>
                )
              })}
            </div>
          </section>
        )}

        {/* Biggest Movers Up */}
        {snapshot.biggest_movers_up && snapshot.biggest_movers_up.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: '#4ae60b' }}>Rising</h2>
            <div style={styles.moversGrid}>
              {snapshot.biggest_movers_up.map((tool: any) => {
                const details = toolMap.get(tool.tool_slug)
                return (
                  <a key={tool.tool_slug} href={`/tools/${tool.tool_slug}`} style={styles.moverCard}>
                    <div style={styles.moverName}>{details?.canonical_name || tool.tool_slug}</div>
                    <div style={styles.moverDelta} style={{ color: '#4ae60b' }}>
                      ↑ {tool.delta > 0 ? '+' : ''}{tool.delta}
                    </div>
                    <div style={styles.moverScore}>
                      {tool.prev_score} → {tool.score}
                    </div>
                  </a>
                )
              })}
            </div>
          </section>
        )}

        {/* Biggest Movers Down */}
        {snapshot.biggest_movers_down && snapshot.biggest_movers_down.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: '#ff6b6b' }}>Falling</h2>
            <div style={styles.moversGrid}>
              {snapshot.biggest_movers_down.map((tool: any) => {
                const details = toolMap.get(tool.tool_slug)
                return (
                  <a key={tool.tool_slug} href={`/tools/${tool.tool_slug}`} style={styles.moverCard}>
                    <div style={styles.moverName}>{details?.canonical_name || tool.tool_slug}</div>
                    <div style={styles.moverDelta} style={{ color: '#ff6b6b' }}>
                      ↓ {tool.delta}
                    </div>
                    <div style={styles.moverScore}>
                      {tool.prev_score} → {tool.score}
                    </div>
                  </a>
                )
              })}
            </div>
          </section>
        )}

        {/* New Entries */}
        {snapshot.new_entries && snapshot.new_entries.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: accent }}>New This Week</h2>
            <div style={styles.entriesGrid}>
              {snapshot.new_entries.map((tool: any) => {
                const details = toolMap.get(tool.tool_slug)
                return (
                  <a key={tool.tool_slug} href={`/tools/${tool.tool_slug}`} style={styles.entryCard}>
                    <div style={styles.entryName}>{details?.canonical_name || tool.tool_slug}</div>
                    <div style={{ ...styles.entryScore, color: accent }}>Score {tool.score}</div>
                  </a>
                )
              })}
            </div>
          </section>
        )}

        {/* Notable Exits */}
        {snapshot.notable_exits && snapshot.notable_exits.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: 'rgba(255,255,255,0.4)' }}>Dropped Below Threshold</h2>
            <div style={styles.entriesGrid}>
              {snapshot.notable_exits.map((tool: any) => {
                const details = toolMap.get(tool.tool_slug)
                return (
                  <a key={tool.tool_slug} href={`/tools/${tool.tool_slug}`} style={styles.exitCard}>
                    <div style={styles.exitName}>{details?.canonical_name || tool.tool_slug}</div>
                    <div style={styles.exitScore}>{tool.prev_score} → {tool.score}</div>
                  </a>
                )
              })}
            </div>
          </section>
        )}
      </div>

      {snapshot.published_at && (
        <footer style={styles.footer}>
          <time style={styles.muted}>
            Published {new Date(snapshot.published_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </time>
        </footer>
      )}
    </article>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { maxWidth: 900, margin: '0 auto', padding: '24px 20px 80px', fontFamily: '"IBM Plex Mono", monospace' },
  breadcrumb: { display: 'flex', gap: 6, alignItems: 'center', fontSize: 11, marginBottom: 24, color: 'rgba(255,255,255,0.3)' },
  link: { color: '#c8f04a', textDecoration: 'none' },
  sep: { color: 'rgba(255,255,255,0.15)' },
  muted: { color: 'rgba(255,255,255,0.3)' },
  header: { marginBottom: 48 },
  indexMeta: { display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 16 },
  verticalBadge: { fontSize: 10, padding: '3px 8px', borderRadius: 2, border: '0.5px solid', letterSpacing: '0.06em', textTransform: 'uppercase' },
  dateMuted: { fontSize: 10, color: 'rgba(255,255,255,0.25)' },
  title: { fontSize: 32, fontFamily: '"Playfair Display", serif', fontWeight: 700, color: '#fff', lineHeight: 1.3, marginBottom: 16, margin: '0 0 16px' },
  lede: { fontSize: 15, color: 'rgba(255,255,255,0.7)', lineHeight: 1.8, margin: '0 0 0 0', maxWidth: 600 },
  body: { display: 'flex', flexDirection: 'column', gap: 48 },

  section: { display: 'flex', flexDirection: 'column', gap: 16 },
  sectionTitle: { fontSize: 13, fontWeight: 700, letterSpacing: '0.05em', margin: 0, textTransform: 'uppercase' },

  toolGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 },
  toolCard: {
    padding: '16px 12px',
    border: '0.5px solid',
    borderRadius: 4,
    textDecoration: 'none',
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    transition: 'background 200ms',
  },
  toolRank: { fontSize: 10, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.06em', textTransform: 'uppercase' },
  toolName: { fontSize: 12, fontWeight: 500, color: '#fff' },
  toolScore: { fontSize: 14, fontWeight: 700, color: 'rgba(255,255,255,0.9)' },
  toolDelta: { fontSize: 11, fontWeight: 600 },

  moversGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 },
  moverCard: {
    padding: '12px',
    border: '0.5px solid rgba(255,255,255,0.1)',
    borderRadius: 4,
    textDecoration: 'none',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  moverName: { fontSize: 12, fontWeight: 500, color: '#fff' },
  moverDelta: { fontSize: 13, fontWeight: 700 },
  moverScore: { fontSize: 10, color: 'rgba(255,255,255,0.4)' },

  entriesGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 },
  entryCard: {
    padding: '12px',
    border: '0.5px solid rgba(255,255,255,0.1)',
    borderRadius: 4,
    textDecoration: 'none',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  entryName: { fontSize: 12, fontWeight: 500, color: '#fff' },
  entryScore: { fontSize: 11, fontWeight: 600 },

  exitCard: {
    padding: '12px',
    border: '0.5px solid rgba(255,255,255,0.08)',
    borderRadius: 4,
    textDecoration: 'none',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    opacity: 0.65,
  },
  exitName: { fontSize: 12, color: 'rgba(255,255,255,0.7)' },
  exitScore: { fontSize: 10, color: 'rgba(255,255,255,0.3)' },

  footer: { marginTop: 48, paddingTop: 24, borderTop: '0.5px solid rgba(255,255,255,0.08)', fontSize: 10 },
}
