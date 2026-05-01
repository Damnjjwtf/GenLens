/**
 * app/tools/page.tsx
 *
 * Public tool directory.
 * Lists all tools with current scores, grouped by vertical.
 *
 * genlens.app/tools
 */

import { db as sql } from '@/lib/db'
import type { Metadata } from 'next'
import { breadcrumbLD, SITE_URL } from '@/lib/schema/jsonld'

export const metadata: Metadata = {
  title: 'Tool Directory — GenLens Ratings & Scores',
  description: 'AI creative tools rated by speed, cost, quality, and adoption velocity. Product photography, filmmaking, digital humans.',
  openGraph: {
    title: 'Tool Directory',
    description: 'AI creative tools rated and ranked by GenLens Score.',
    url: `${SITE_URL}/tools`,
    siteName: 'GenLens',
    type: 'website',
  },
  alternates: { canonical: `${SITE_URL}/tools` },
}

const VERTICAL_LABELS: Record<string, string> = {
  product_photography: 'Product Photography',
  filmmaking: 'Filmmaking',
  digital_humans: 'Digital Humans',
}

const VERTICAL_ACCENT: Record<string, string> = {
  product_photography: '#c8f04a',
  filmmaking: '#f0a83c',
  digital_humans: '#b07af0',
}

export default async function ToolsPage() {
  const tools = await sql`
    SELECT
      id, slug, canonical_name, website_url, affiliate_url,
      verticals, current_score, signal_count, affiliate_program, affiliate_commission_pct
    FROM tools
    ORDER BY current_score DESC NULLS LAST, canonical_name ASC
  `

  // Group by vertical
  const grouped = new Map<string, typeof tools>()
  for (const tool of tools) {
    const toolVerticals = tool.verticals as string[] || []
    for (const v of toolVerticals) {
      if (!grouped.has(v)) grouped.set(v, [])
      grouped.get(v)!.push(tool)
    }
  }

  // Sort each group by score
  for (const [, group] of grouped) {
    group.sort((a, b) => ((b.current_score ?? 0) - (a.current_score ?? 0)))
  }

  const jsonLd = breadcrumbLD([
    { name: 'GenLens', url: SITE_URL },
    { name: 'Tools', url: `${SITE_URL}/tools` },
  ])

  const verticalOrder = ['product_photography', 'filmmaking', 'digital_humans']

  return (
    <main style={styles.page}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <nav aria-label="Breadcrumb" style={styles.breadcrumb}>
        <a href="/" style={{ ...styles.link, color: '#c8f04a' }}>GenLens</a>
        <span style={styles.sep}>/</span>
        <span style={styles.muted}>Tools</span>
      </nav>

      <header style={styles.header}>
        <h1 style={styles.title}>Tool Directory</h1>
        <p style={styles.subtitle}>
          {tools.length} AI creative tools, rated by speed, cost, quality, and adoption velocity.
        </p>
      </header>

      <div style={styles.sections}>
        {verticalOrder.map(vertical => {
          const toolsInVertical = grouped.get(vertical) || []
          if (toolsInVertical.length === 0) return null

          const accent = VERTICAL_ACCENT[vertical] ?? '#c8f04a'
          const label = VERTICAL_LABELS[vertical] ?? vertical

          return (
            <section key={vertical} style={styles.section}>
              <h2 style={{ ...styles.verticalTitle, color: accent }}>{label}</h2>
              <div style={styles.toolGrid}>
                {toolsInVertical.map((tool: any) => (
                  <a
                    key={tool.id}
                    href={`/tools/${tool.slug}`}
                    style={{
                      ...styles.toolCard,
                      borderColor: accent + '44',
                      background: accent + '06',
                    }}
                  >
                    <div style={styles.toolNameRow}>
                      <h3 style={styles.toolName}>{tool.canonical_name}</h3>
                      {tool.affiliate_program && (
                        <div style={{ ...styles.affiliateBadge, color: accent }}>
                          +{tool.affiliate_commission_pct}%
                        </div>
                      )}
                    </div>

                    {tool.current_score != null && (
                      <div style={styles.scoreRow}>
                        <div style={{ ...styles.score, color: accent }}>
                          {tool.current_score}
                        </div>
                        <div style={styles.scoreLabel}>Score</div>
                      </div>
                    )}

                    {tool.signal_count > 0 && (
                      <div style={styles.signalCount}>
                        {tool.signal_count} signal{tool.signal_count === 1 ? '' : 's'}
                      </div>
                    )}

                    <div style={styles.cardMeta}>
                      {tool.website_url ? (
                        <a href={tool.website_url} target="_blank" rel="noopener" style={styles.linkSmall}>
                          Visit →
                        </a>
                      ) : (
                        <span style={styles.muted}>No website</span>
                      )}
                    </div>
                  </a>
                ))}
              </div>
            </section>
          )
        })}
      </div>

      <footer style={styles.footer}>
        <p style={styles.footerText}>
          Score updates daily based on production workflow impact. See an issue? <a href="/" style={styles.link}>Get in touch</a>.
        </p>
      </footer>
    </main>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { maxWidth: 1000, margin: '0 auto', padding: '24px 20px 80px', fontFamily: '"IBM Plex Mono", monospace' },
  breadcrumb: { display: 'flex', gap: 6, alignItems: 'center', fontSize: 11, marginBottom: 24, color: 'rgba(255,255,255,0.3)' },
  link: { color: '#c8f04a', textDecoration: 'none' },
  sep: { color: 'rgba(255,255,255,0.15)' },
  muted: { color: 'rgba(255,255,255,0.3)' },

  header: { marginBottom: 48, textAlign: 'center' as const },
  title: { fontSize: 32, fontFamily: '"Playfair Display", serif', fontWeight: 700, color: '#fff', margin: '0 0 16px', lineHeight: 1.3 },
  subtitle: { fontSize: 14, color: 'rgba(255,255,255,0.6)', lineHeight: 1.8, maxWidth: 500, margin: '0 auto' },

  sections: { display: 'flex', flexDirection: 'column' as const, gap: 48 },
  section: { display: 'flex', flexDirection: 'column' as const, gap: 16 },
  verticalTitle: { fontSize: 13, fontWeight: 700, letterSpacing: '0.05em', textTransform: 'uppercase', margin: 0 },

  toolGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 },
  toolCard: {
    padding: '16px',
    border: '0.5px solid',
    borderRadius: 4,
    textDecoration: 'none',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: 12,
    transition: 'background 200ms',
  },
  toolNameRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: 8 },
  toolName: { fontSize: 13, fontWeight: 600, color: '#fff', margin: 0, flex: 1 },
  affiliateBadge: { fontSize: 9, fontWeight: 700, padding: '2px 6px', border: '0.5px solid currentColor', borderRadius: 2, whiteSpace: 'nowrap' },

  scoreRow: { display: 'flex', alignItems: 'baseline', gap: 6 },
  score: { fontSize: 18, fontWeight: 700 },
  scoreLabel: { fontSize: 9, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.04em' },

  signalCount: { fontSize: 10, color: 'rgba(255,255,255,0.4)' },

  cardMeta: { marginTop: 'auto', paddingTop: 8, borderTop: '0.5px solid rgba(255,255,255,0.06)' },
  linkSmall: { fontSize: 10, color: '#c8f04a', textDecoration: 'none', fontWeight: 600 },

  footer: { marginTop: 60, paddingTop: 32, borderTop: '0.5px solid rgba(255,255,255,0.08)', textAlign: 'center' as const },
  footerText: { fontSize: 11, color: 'rgba(255,255,255,0.4)', lineHeight: 1.7, margin: 0 },
}
