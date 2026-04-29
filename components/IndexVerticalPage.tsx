/**
 * components/IndexVerticalPage.tsx
 *
 * Shared render for per-vertical Index pages. Mirrors the visual design
 * of app/index/[date]/page.tsx — same inline styles, fonts, and section
 * structure. The only difference: this resolves the latest published
 * snapshot for a given vertical instead of looking up by date.
 *
 * Used by sibling static routes (product-photography, filmmaking,
 * digital-humans) so we avoid colliding with the [date] dynamic segment.
 */

import { neon } from '@neondatabase/serverless'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { breadcrumbLD, SITE_URL } from '@/lib/schema/jsonld'
import { VERTICAL_LABELS, type Vertical } from '@/lib/constants'

const sql = neon(process.env.DATABASE_URL!)

export const VERTICAL_SLUG: Record<Vertical, string> = {
  product_photography: 'product-photography',
  filmmaking: 'filmmaking',
  digital_humans: 'digital-humans',
}

const VERTICAL_ACCENT: Record<Vertical, string> = {
  product_photography: '#c8f04a',
  filmmaking: '#f0a83c',
  digital_humans: '#b07af0',
}

const VERTICAL_TICKER_SYMBOL: Record<Vertical, string> = {
  product_photography: 'GLI-PP',
  filmmaking: 'GLI-FM',
  digital_humans: 'GLI-DH',
}

export async function generateVerticalMetadata(vertical: Vertical): Promise<Metadata> {
  const slug = VERTICAL_SLUG[vertical]
  const [snapshot] = await sql`
    SELECT headline, lede, week_start_date
    FROM index_snapshots
    WHERE vertical = ${vertical} AND status = 'published'
    ORDER BY week_start_date DESC
    LIMIT 1
  `
  const label = VERTICAL_LABELS[vertical]
  const title = snapshot?.headline || `${label} Index — GenLens`
  const description = snapshot?.lede || `This week's top AI tools for ${label.toLowerCase()}.`
  const url = `${SITE_URL}/index/${slug}`

  return {
    title: `${title} — GenLens Index`,
    description,
    openGraph: {
      title, description, url, siteName: 'GenLens', type: 'article',
      images: [`${SITE_URL}/api/og/index/${slug}`],
    },
    twitter: { card: 'summary_large_image', title, description },
    alternates: { canonical: url },
  }
}

export async function renderVerticalIndex(vertical: Vertical) {
  const [snapshot] = await sql`
    SELECT *
    FROM index_snapshots
    WHERE vertical = ${vertical} AND status = 'published'
    ORDER BY week_start_date DESC
    LIMIT 1
  `
  if (!snapshot) notFound()

  // Issue # = count of published snapshots for this vertical up to and
  // including this week. Cheap query, deterministic.
  const [{ issue }] = await sql`
    SELECT COUNT(*)::int AS issue
    FROM index_snapshots
    WHERE vertical = ${vertical}
      AND status = 'published'
      AND week_start_date <= ${snapshot.week_start_date}
  `

  // Movers feed for ticker, ordered by absolute delta size.
  const tickerItems: { slug: string; delta: number }[] = [
    ...(snapshot.biggest_movers_up || []),
    ...(snapshot.biggest_movers_down || []),
  ]
    .map((t: { tool_slug: string; delta: number }) => ({ slug: t.tool_slug, delta: t.delta }))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))

  const allToolSlugs = [
    ...(snapshot.top_tools || []).map((t: { tool_slug: string }) => t.tool_slug),
    ...(snapshot.biggest_movers_up || []).map((t: { tool_slug: string }) => t.tool_slug),
    ...(snapshot.biggest_movers_down || []).map((t: { tool_slug: string }) => t.tool_slug),
    ...(snapshot.new_entries || []).map((t: { tool_slug: string }) => t.tool_slug),
    ...(snapshot.notable_exits || []).map((t: { tool_slug: string }) => t.tool_slug),
  ].filter((v, i, a) => a.indexOf(v) === i)

  const tools = allToolSlugs.length > 0
    ? await sql`SELECT id, slug, canonical_name, affiliate_url, current_score FROM tools WHERE slug = ANY(${allToolSlugs})`
    : []
  const toolMap = new Map(tools.map((t: { slug: string }) => [t.slug, t]))

  const accent = VERTICAL_ACCENT[vertical]
  const verticalLabel = VERTICAL_LABELS[vertical]
  const slug = VERTICAL_SLUG[vertical]
  const tickerSymbol = VERTICAL_TICKER_SYMBOL[vertical]
  const indexUrl = `${SITE_URL}/index/${slug}`
  const toolName = (s: string) => {
    const t = toolMap.get(s) as { canonical_name?: string } | undefined
    return t?.canonical_name || s
  }

  const jsonLd: object[] = [
    {
      '@context': 'https://schema.org',
      '@type': 'NewsArticle',
      headline: snapshot.headline || `${verticalLabel} Index — Week of ${snapshot.week_start_date}`,
      description: snapshot.lede,
      datePublished: snapshot.published_at,
      url: indexUrl,
      publisher: { '@type': 'Organization', name: 'GenLens', url: SITE_URL },
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
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes gli-ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
      ` }} />

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
          <span style={{ ...styles.tickerSymbol, color: accent }}>{tickerSymbol}</span>
          <time style={styles.dateMuted}>
            Week of {new Date(snapshot.week_start_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            {' · '}
            Issue #{issue}
          </time>
        </div>

        <h1 style={styles.title}>
          {snapshot.headline || `${verticalLabel} Index`}
        </h1>

        {snapshot.lede && (
          <p style={styles.lede}>{snapshot.lede}</p>
        )}
      </header>

      {tickerItems.length > 0 && (
        <div style={styles.ticker} aria-label="Biggest score movers this week">
          <div style={styles.tickerInner}>
            {tickerItems.concat(tickerItems).map((t, i) => (
              <span key={i} style={styles.tickerItem}>
                <span style={styles.tickerName}>{toolName(t.slug).toUpperCase()}</span>
                {' '}
                <span style={{ color: t.delta >= 0 ? '#4ae60b' : '#ff6b6b' }}>
                  {t.delta >= 0 ? '+' : ''}{t.delta}
                </span>
                <span style={{ ...styles.tickerSep, color: accent }}> · </span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div style={styles.body}>
        {snapshot.top_tools && snapshot.top_tools.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: accent }}>Top 10 Tools</h2>
            <div style={styles.toolGrid}>
              {snapshot.top_tools.map((tool: { tool_slug: string; score: number; score_delta: number | null }, i: number) => {
                const details = toolMap.get(tool.tool_slug) as { canonical_name?: string } | undefined
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

        {snapshot.biggest_movers_up && snapshot.biggest_movers_up.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: '#4ae60b' }}>Rising</h2>
            <div style={styles.moversGrid}>
              {snapshot.biggest_movers_up.map((tool: { tool_slug: string; score: number; delta: number; prev_score: number }) => {
                const details = toolMap.get(tool.tool_slug) as { canonical_name?: string } | undefined
                return (
                  <a key={tool.tool_slug} href={`/tools/${tool.tool_slug}`} style={styles.moverCard}>
                    <div style={styles.moverName}>{details?.canonical_name || tool.tool_slug}</div>
                    <div style={{ ...styles.moverDelta, color: '#4ae60b' }}>
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

        {snapshot.biggest_movers_down && snapshot.biggest_movers_down.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: '#ff6b6b' }}>Falling</h2>
            <div style={styles.moversGrid}>
              {snapshot.biggest_movers_down.map((tool: { tool_slug: string; score: number; delta: number; prev_score: number }) => {
                const details = toolMap.get(tool.tool_slug) as { canonical_name?: string } | undefined
                return (
                  <a key={tool.tool_slug} href={`/tools/${tool.tool_slug}`} style={styles.moverCard}>
                    <div style={styles.moverName}>{details?.canonical_name || tool.tool_slug}</div>
                    <div style={{ ...styles.moverDelta, color: '#ff6b6b' }}>
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

        {snapshot.new_entries && snapshot.new_entries.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: accent }}>New This Week</h2>
            <div style={styles.entriesGrid}>
              {snapshot.new_entries.map((tool: { tool_slug: string; score: number }) => {
                const details = toolMap.get(tool.tool_slug) as { canonical_name?: string } | undefined
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

        {snapshot.notable_exits && snapshot.notable_exits.length > 0 && (
          <section style={styles.section}>
            <h2 style={{ ...styles.sectionTitle, color: 'rgba(255,255,255,0.4)' }}>Dropped Below Threshold</h2>
            <div style={styles.entriesGrid}>
              {snapshot.notable_exits.map((tool: { tool_slug: string; score: number; prev_score: number }) => {
                const details = toolMap.get(tool.tool_slug) as { canonical_name?: string } | undefined
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
  header: { marginBottom: 32 },
  indexMeta: { display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 16 },
  verticalBadge: { fontSize: 10, padding: '3px 8px', borderRadius: 2, border: '0.5px solid', letterSpacing: '0.06em', textTransform: 'uppercase' },
  tickerSymbol: { fontSize: 10, fontWeight: 600, letterSpacing: '0.18em', textTransform: 'uppercase' },
  dateMuted: { fontSize: 10, color: 'rgba(255,255,255,0.25)' },

  ticker: {
    borderTop: '0.5px solid rgba(255,255,255,0.1)',
    borderBottom: '0.5px solid rgba(255,255,255,0.1)',
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    padding: '7px 0',
    marginBottom: 32,
  },
  tickerInner: {
    display: 'inline-block',
    animation: 'gli-ticker 90s linear infinite',
    fontSize: 10,
    letterSpacing: '0.04em',
  },
  tickerItem: { color: 'rgba(255,255,255,0.7)' },
  tickerName: { color: '#fff', fontWeight: 500 },
  tickerSep: { margin: '0 6px', fontWeight: 600 },
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
