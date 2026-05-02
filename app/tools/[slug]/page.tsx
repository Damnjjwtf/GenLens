/**
 * app/tools/[slug]/page.tsx
 *
 * Public tool page. No auth required.
 * SEO + GEO optimized: FAQ schema, meta description, structured Q&A.
 * Affiliate link on every page.
 *
 * genlens.app/tools/elevenlabs
 * genlens.app/tools/keyshot
 * genlens.app/tools/runway
 */

import { db as sql } from '@/lib/db'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import {
  softwareApplicationLD,
  breadcrumbLD,
  faqLD,
  SITE_URL,
} from '@/lib/schema/jsonld'

interface Params { params: { slug: string } }

// ─── Metadata (SEO + GEO) ──────────────────────────────────────

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const [tool] = await sql`SELECT * FROM tools WHERE slug = ${params.slug} AND is_public = true LIMIT 1`
  if (!tool) return { title: 'Tool not found — GenLens' }

  return {
    title: `${tool.canonical_name} — GenLens Intelligence`,
    description: tool.meta_description || `GenLens intelligence on ${tool.canonical_name}: signals, score, workflow templates, and more.`,
    openGraph: {
      title: `${tool.canonical_name} — GenLens`,
      description: tool.meta_description,
      url: `https://genlens.app/tools/${params.slug}`,
      siteName: 'GenLens',
      type: 'website',
    },
    alternates: {
      canonical: `https://genlens.app/tools/${params.slug}`,
    },
  }
}

// ─── Page ─────────────────────────────────────────────────────

export default async function ToolPage({ params }: Params) {
  const [tool] = await sql`SELECT * FROM tools WHERE slug = ${params.slug} AND is_public = true LIMIT 1`
  if (!tool) notFound()

  // Recent signals about this tool (last 10)
  const signals = await sql`
    SELECT id, title, summary, dimension, vertical, time_saved_hours, cost_saved_dollars, created_at, source_url, source_name
    FROM signals
    WHERE ${params.slug} = ANY(tool_names)
      AND is_public = true
    ORDER BY created_at DESC
    LIMIT 10
  `

  // Comparison pages featuring this tool
  const comparisons = await sql`
    SELECT slug, tool_a_slug, tool_b_slug, summary
    FROM tool_comparisons
    WHERE (tool_a_slug = ${params.slug} OR tool_b_slug = ${params.slug})
      AND is_public = true
    LIMIT 5
  `

  const qaBlocks = Array.isArray(tool.geo_qa_blocks) ? tool.geo_qa_blocks : []
  const verticals: string[] = Array.isArray(tool.verticals) ? tool.verticals : []

  const VERTICAL_LABELS: Record<string, string> = {
    product_photography: 'Product Photography',
    filmmaking: 'Filmmaking',
    digital_humans: 'Digital Humans',
  }

  const DIMENSION_LABELS: Record<number, string> = {
    1: 'Workflow', 2: 'Category', 3: 'Competitive', 4: 'Templates',
    5: 'Cost/Time', 6: 'Legal', 7: 'Talent', 8: 'Integration',
    9: 'Trends', 10: 'Leaderboard',
  }

  // ─── JSON-LD payloads ─────────────────────────────────────
  const toolUrl = `${SITE_URL}/tools/${params.slug}`
  const jsonLd: object[] = [
    softwareApplicationLD({
      slug: tool.slug as string,
      canonical_name: tool.canonical_name as string,
      geo_summary: (tool.geo_summary as string | null) ?? null,
      meta_description: (tool.meta_description as string | null) ?? null,
      website_url: (tool.website_url as string | null) ?? null,
      current_score: (tool.current_score as number | null) ?? null,
      verticals,
      categories: (tool.categories as string[] | null) ?? null,
      signal_count: (tool.signal_count as number | null) ?? null,
    }),
    breadcrumbLD([
      { name: 'GenLens', url: SITE_URL },
      { name: 'Tools', url: `${SITE_URL}/tools` },
      { name: tool.canonical_name as string, url: toolUrl },
    ]),
  ]
  const fa = faqLD(qaBlocks, toolUrl)
  if (fa) jsonLd.push(fa)
  // Existing per-tool faq_schema may also be present from the Growth Agent.
  if (tool.faq_schema && !fa) {
    jsonLd.push(tool.faq_schema as object)
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <article style={styles.page} itemScope itemType="https://schema.org/SoftwareApplication">
        <link itemProp="url" href={toolUrl} />

        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" style={styles.breadcrumb}>
          <a href="/tools" style={styles.breadcrumbLink}>Tools</a>
          <span style={styles.breadcrumbSep}>/</span>
          <span style={styles.breadcrumbCurrent}>{tool.canonical_name}</span>
        </nav>

        <header style={styles.toolHeader}>
          <div style={styles.toolHeaderLeft}>
            <h1 style={styles.toolName} itemProp="name">{tool.canonical_name}</h1>
            <div style={styles.toolMeta}>
              {verticals.map((v: string) => (
                <span key={v} style={styles.verticalTag}>
                  {VERTICAL_LABELS[v] ?? v}
                </span>
              ))}
              {tool.current_score ? (
                <span style={styles.scoreBadge}>
                  GenLens Score: <strong>{tool.current_score}</strong> / 100
                </span>
              ) : (
                <span style={styles.scorePending}>Score: coming soon</span>
              )}
            </div>
          </div>
          <div style={styles.toolHeaderRight}>
            {tool.affiliate_url && (
              <a href={tool.affiliate_url as string} target="_blank" rel="noopener nofollow sponsored" style={styles.affiliateBtn}>
                Try {tool.canonical_name} →
              </a>
            )}
            {tool.website_url && !tool.affiliate_url && (
              <a href={tool.website_url as string} target="_blank" rel="noopener" style={styles.websiteBtn} itemProp="sameAs">
                Visit site →
              </a>
            )}
          </div>
        </header>

        {tool.geo_summary && (
          <section style={styles.geoSummary} aria-labelledby="genlens-summary-label">
            <h2 id="genlens-summary-label" style={styles.geoSummaryLabel}>GenLens Summary</h2>
            <p style={styles.geoSummaryText} itemProp="description">{tool.geo_summary as string}</p>
          </section>
        )}

        {tool.affiliate_url && (
          <p style={styles.disclosure}>
            Disclosure: GenLens may earn a commission if you subscribe via the link above.
            {tool.affiliate_program ? ` (${tool.affiliate_program} affiliate program)` : ''}
          </p>
        )}

        <div style={styles.mainGrid}>
          <div style={styles.leftCol}>
            {qaBlocks.length > 0 && (
              <section style={styles.section} aria-labelledby="faq-heading">
                <h2 id="faq-heading" style={styles.sectionTitle}>Common questions</h2>
                <dl style={styles.qaList}>
                  {qaBlocks.map((qa: { q: string; a: string; confidence: string; source_url?: string }, i: number) => (
                    <div key={i} style={styles.qaItem}>
                      <dt style={styles.qaQuestion}>{qa.q}</dt>
                      <dd style={styles.qaAnswer}>
                        {qa.a}
                        {qa.source_url && (
                          <>
                            {' '}
                            <a href={qa.source_url} target="_blank" rel="noopener" style={styles.qaSource}>
                              Source →
                            </a>
                          </>
                        )}
                      </dd>
                    </div>
                  ))}
                </dl>
              </section>
            )}

            {signals.length > 0 && (
              <section style={styles.section} aria-labelledby="signals-heading">
                <h2 id="signals-heading" style={styles.sectionTitle}>Recent intelligence</h2>
                <ul style={{ ...styles.signalList, listStyle: 'none', padding: 0, margin: 0 }}>
                  {signals.map((s: {
                    id: number; title: string; summary: string; dimension: number;
                    vertical: string; time_saved_hours: number | null; cost_saved_dollars: number | null;
                    created_at: string; source_url: string; source_name: string;
                  }) => (
                    <li key={s.id}>
                      <a href={`/signals/${s.id}`} style={styles.signalItem}>
                        <article>
                          <div style={styles.signalTop}>
                            <span style={styles.signalDimension}>
                              {DIMENSION_LABELS[s.dimension] ?? `Dim ${s.dimension}`}
                            </span>
                            <time dateTime={new Date(s.created_at).toISOString()} style={styles.signalDate}>
                              {new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </time>
                          </div>
                          <h3 style={styles.signalTitle}>{s.title}</h3>
                          {s.summary && <p style={styles.signalSummary}>{s.summary.slice(0, 140)}…</p>}
                          {(s.time_saved_hours || s.cost_saved_dollars) && (
                            <div style={styles.signalDeltas}>
                              {s.time_saved_hours && <span style={styles.delta}>−{s.time_saved_hours}h</span>}
                              {s.cost_saved_dollars && <span style={styles.delta}>−${s.cost_saved_dollars.toLocaleString()}</span>}
                            </div>
                          )}
                        </article>
                      </a>
                    </li>
                  ))}
                </ul>
                <a href={`/signals?tool=${params.slug}`} style={styles.seeAllLink}>
                  See all {tool.canonical_name} signals →
                </a>
              </section>
            )}
          </div>

          <aside style={styles.rightCol}>
            {comparisons.length > 0 && (
              <nav style={styles.sidebar} aria-label="Tool comparisons">
                <h2 style={styles.sidebarLabel}>Compare</h2>
                {comparisons.map((c: { slug: string; tool_a_slug: string; tool_b_slug: string; summary: string }) => {
                  const other = c.tool_a_slug === params.slug ? c.tool_b_slug : c.tool_a_slug
                  return (
                    <a href={`/compare/${c.slug}`} key={c.slug} style={styles.comparisonLink}>
                      {tool.canonical_name} vs {other.replace(/-/g, ' ')} →
                    </a>
                  )
                })}
              </nav>
            )}

            {tool.score_history && Array.isArray(tool.score_history) && tool.score_history.length > 1 && (
              <section style={styles.sidebar} aria-labelledby="score-history-label">
                <h2 id="score-history-label" style={styles.sidebarLabel}>Score history</h2>
                {(tool.score_history as { date: string; score: number; reason?: string }[]).slice(-5).map((h, i: number) => (
                  <div key={i} style={styles.scoreHistoryRow}>
                    <time dateTime={h.date} style={styles.scoreHistoryDate}>{h.date}</time>
                    <span style={styles.scoreHistoryScore}>{h.score}</span>
                  </div>
                ))}
              </section>
            )}

            <aside style={styles.ctaCard} aria-labelledby="cta-title">
              <h2 id="cta-title" style={styles.ctaTitle}>Get daily intelligence on {tool.canonical_name}</h2>
              <p style={styles.ctaText}>
                GenLens watches 130+ sources and sends you what changed, what it means for your workflow, and what to do about it.
              </p>
              <a href={`/?next=${encodeURIComponent(`/tools/${params.slug}`)}#sign-in`} style={styles.ctaBtn}>
                Sign in →
              </a>
            </aside>
          </aside>
        </div>
      </article>
    </>
  )
}

// ─── Styles ───────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: { maxWidth: 1100, margin: '0 auto', padding: '24px 20px 60px', fontFamily: '"IBM Plex Mono", monospace' },
  breadcrumb: { fontSize: 11, marginBottom: 20, color: 'rgba(255,255,255,0.3)', display: 'flex', gap: 6, alignItems: 'center' },
  breadcrumbLink: { color: '#c8f04a', textDecoration: 'none' },
  breadcrumbSep: { color: 'rgba(255,255,255,0.15)' },
  breadcrumbCurrent: {},
  toolHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, gap: 20, flexWrap: 'wrap' },
  toolHeaderLeft: {},
  toolHeaderRight: {},
  toolName: { fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 10, fontFamily: '"Playfair Display", serif' },
  toolMeta: { display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' },
  verticalTag: { fontSize: 10, padding: '3px 8px', border: '0.5px solid rgba(200,240,74,0.3)', color: '#c8f04a', borderRadius: 2, letterSpacing: '0.05em' },
  scoreBadge: { fontSize: 11, color: '#f0a83c', padding: '3px 8px', border: '0.5px solid rgba(240,168,60,0.3)', borderRadius: 2 },
  scorePending: { fontSize: 10, color: 'rgba(255,255,255,0.25)', fontStyle: 'italic' },
  affiliateBtn: { display: 'inline-block', padding: '10px 20px', background: '#c8f04a', color: '#0e0e0e', borderRadius: 3, fontWeight: 700, fontSize: 12, textDecoration: 'none', letterSpacing: '0.04em' },
  websiteBtn: { display: 'inline-block', padding: '10px 20px', border: '0.5px solid rgba(255,255,255,0.2)', color: 'rgba(255,255,255,0.7)', borderRadius: 3, fontSize: 12, textDecoration: 'none' },
  geoSummary: { padding: '16px 20px', background: 'rgba(200,240,74,0.04)', border: '0.5px solid rgba(200,240,74,0.15)', borderRadius: 4, marginBottom: 12 },
  geoSummaryLabel: { fontSize: 9, letterSpacing: '0.1em', color: '#c8f04a', marginBottom: 8, textTransform: 'uppercase' },
  geoSummaryText: { fontSize: 13, lineHeight: 1.7, color: 'rgba(255,255,255,0.75)', margin: 0 },
  disclosure: { fontSize: 10, color: 'rgba(255,255,255,0.2)', marginBottom: 24, fontStyle: 'italic' },
  mainGrid: { display: 'grid', gridTemplateColumns: '1fr 300px', gap: 32, alignItems: 'start' },
  leftCol: {},
  rightCol: { display: 'flex', flexDirection: 'column', gap: 16 },
  section: { marginBottom: 32 },
  sectionTitle: { fontSize: 11, letterSpacing: '0.1em', color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', marginBottom: 14, fontWeight: 500 },
  qaList: { display: 'flex', flexDirection: 'column', gap: 0 },
  qaItem: { padding: '16px 0', borderBottom: '0.5px solid rgba(255,255,255,0.06)' },
  qaQuestion: { fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 8, lineHeight: 1.5 },
  qaAnswer: { fontSize: 12, color: 'rgba(255,255,255,0.65)', lineHeight: 1.7, marginBottom: 6 },
  qaSource: { fontSize: 10, color: '#4a90e2', textDecoration: 'none' },
  signalList: { display: 'flex', flexDirection: 'column', gap: 1 },
  signalItem: { display: 'block', padding: '12px 0', borderBottom: '0.5px solid rgba(255,255,255,0.05)', textDecoration: 'none', cursor: 'pointer' },
  signalTop: { display: 'flex', justifyContent: 'space-between', marginBottom: 5 },
  signalDimension: { fontSize: 9, color: '#f0a83c', letterSpacing: '0.06em', textTransform: 'uppercase' },
  signalDate: { fontSize: 9, color: 'rgba(255,255,255,0.25)' },
  signalTitle: { fontSize: 12, color: 'rgba(255,255,255,0.85)', fontWeight: 500, marginBottom: 4, lineHeight: 1.5 },
  signalSummary: { fontSize: 11, color: 'rgba(255,255,255,0.45)', lineHeight: 1.6 },
  signalDeltas: { display: 'flex', gap: 8, marginTop: 6 },
  delta: { fontSize: 10, color: '#c8f04a', padding: '2px 6px', border: '0.5px solid rgba(200,240,74,0.3)', borderRadius: 2 },
  seeAllLink: { display: 'inline-block', marginTop: 12, fontSize: 11, color: '#c8f04a', textDecoration: 'none' },
  sidebar: { padding: '14px', border: '0.5px solid rgba(255,255,255,0.08)', borderRadius: 4, display: 'flex', flexDirection: 'column', gap: 8 },
  sidebarLabel: { fontSize: 9, letterSpacing: '0.1em', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', marginBottom: 4 },
  comparisonLink: { fontSize: 11, color: '#4a90e2', textDecoration: 'none', lineHeight: 1.6 },
  scoreHistoryRow: { display: 'flex', justifyContent: 'space-between', fontSize: 11 },
  scoreHistoryDate: { color: 'rgba(255,255,255,0.35)' },
  scoreHistoryScore: { color: '#f0a83c', fontWeight: 600 },
  ctaCard: { padding: 16, background: 'rgba(200,240,74,0.06)', border: '0.5px solid rgba(200,240,74,0.2)', borderRadius: 4 },
  ctaTitle: { fontSize: 12, fontWeight: 700, color: '#fff', marginBottom: 8, lineHeight: 1.5 },
  ctaText: { fontSize: 11, color: 'rgba(255,255,255,0.5)', lineHeight: 1.7, marginBottom: 12 },
  ctaBtn: { display: 'inline-block', padding: '8px 16px', background: '#c8f04a', color: '#0e0e0e', borderRadius: 3, fontWeight: 700, fontSize: 11, textDecoration: 'none' },
}
