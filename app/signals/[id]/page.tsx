/**
 * app/signals/[id]/page.tsx
 *
 * Public signal page — no auth required.
 * Shows: headline, geo_summary, creative_implication.
 * Gates: action_item behind signup (freemium hook).
 * OG tags for social sharing.
 *
 * genlens.app/signals/1234
 */

import { db as sql } from '@/lib/db'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { articleLD, breadcrumbLD, SITE_URL } from '@/lib/schema/jsonld'

interface Params { params: { id: string } }

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const [signal] = await sql`
    SELECT * FROM signals WHERE id = ${parseInt(params.id)} AND is_public = true LIMIT 1
  `
  if (!signal) return { title: 'Signal not found — GenLens' }

  return {
    title: `${signal.title} — GenLens`,
    description: signal.geo_summary || signal.summary,
    openGraph: {
      title: signal.hook_sentence || signal.title,
      description: signal.geo_summary || signal.summary,
      url: `https://genlens.app/signals/${signal.id}`,
      siteName: 'GenLens',
      type: 'article',
      // OG image generated dynamically via /api/og/signal/[id]
      images: [`https://genlens.app/api/og/signal/${signal.id}`],
    },
    twitter: {
      card: 'summary_large_image',
      title: signal.hook_sentence || signal.title,
      description: signal.geo_summary || signal.summary,
      images: [`https://genlens.app/api/og/signal/${signal.id}`],
    },
    alternates: { canonical: `https://genlens.app/signals/${signal.id}` },
  }
}

const DIMENSION_LABELS: Record<number, string> = {
  1: 'Workflow Stage', 2: 'Category Deep Dive', 3: 'Competitive Intel',
  4: 'Workflow Templates', 5: 'Cost & Time', 6: 'Legal & Ethical',
  7: 'Talent & Hiring', 8: 'Integration', 9: 'Cultural Trends', 10: 'Leaderboard',
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

export default async function SignalPage({ params }: Params) {
  const signalId = parseInt(params.id)
  if (isNaN(signalId)) notFound()

  const [signal] = await sql`
    SELECT
      id, title, description, summary, geo_summary, hook_sentence,
      vertical, dimension, signal_type, tool_names, workflow_stages,
      time_saved_hours, cost_saved_dollars, quality_improvement_percent,
      source_url, source_name, source_platform, trending_score,
      created_at, published_at, is_public, public_views
    FROM signals
    WHERE id = ${signalId} AND is_public = true
    LIMIT 1
  `
  if (!signal) notFound()

  // Increment view count (fire and forget)
  sql`UPDATE signals SET public_views = public_views + 1 WHERE id = ${signalId}`.catch(() => {})

  // Related signals (same vertical + dimension)
  const related = await sql`
    SELECT id, title, geo_summary, dimension, vertical, created_at
    FROM signals
    WHERE vertical = ${signal.vertical}
      AND dimension = ${signal.dimension}
      AND id != ${signalId}
      AND is_public = true
    ORDER BY created_at DESC
    LIMIT 4
  `

  const accent = VERTICAL_ACCENT[signal.vertical] ?? '#c8f04a'
  const toolNames: string[] = Array.isArray(signal.tool_names) ? signal.tool_names : []
  const signalUrl = `${SITE_URL}/signals/${signal.id}`

  const jsonLd: object[] = [
    articleLD({
      id: signal.id as number,
      title: signal.title as string,
      geo_summary: (signal.geo_summary as string | null) ?? null,
      hook_sentence: (signal.hook_sentence as string | null) ?? null,
      description: (signal.description as string | null) ?? null,
      source_name: (signal.source_name as string) ?? (signal.source_platform as string) ?? 'Unknown',
      source_url: (signal.source_url as string) ?? signalUrl,
      created_at: new Date(signal.created_at as string).toISOString(),
      vertical: signal.vertical as string,
      tool_names: (signal.tool_names as string[] | null) ?? null,
    }),
    breadcrumbLD([
      { name: 'GenLens', url: SITE_URL },
      { name: VERTICAL_LABELS[signal.vertical as string] ?? (signal.vertical as string), url: SITE_URL },
      { name: signal.title as string, url: signalUrl },
    ]),
  ]

  return (
    <article style={{ ...styles.page, '--accent': accent } as React.CSSProperties} itemScope itemType="https://schema.org/NewsArticle">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <link itemProp="mainEntityOfPage" href={signalUrl} />

      <nav aria-label="Breadcrumb" style={styles.breadcrumb}>
        <a href="/" style={{ ...styles.link, color: accent }}>GenLens</a>
        <span style={styles.sep}>/</span>
        <span style={styles.muted}>{VERTICAL_LABELS[signal.vertical] ?? signal.vertical}</span>
        <span style={styles.sep}>/</span>
        <span style={styles.muted}>{DIMENSION_LABELS[signal.dimension] ?? `Dim ${signal.dimension}`}</span>
      </nav>

      <header style={styles.header}>
        <div style={styles.signalMeta}>
          <span style={{ ...styles.verticalBadge, borderColor: accent + '44', color: accent, background: accent + '10' }}>
            {VERTICAL_LABELS[signal.vertical] ?? signal.vertical}
          </span>
          <span style={styles.dimensionBadge}>
            {DIMENSION_LABELS[signal.dimension]}
          </span>
          <time dateTime={new Date(signal.created_at).toISOString()} itemProp="datePublished" style={styles.dateMuted}>
            {new Date(signal.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </time>
        </div>

        <h1 style={styles.title} itemProp="headline">{signal.title}</h1>

        {signal.hook_sentence && (
          <p style={{ ...styles.hook, borderColor: accent + '30' }} itemProp="description">{signal.hook_sentence}</p>
        )}

        {/* Delta chips */}
        {(signal.time_saved_hours || signal.cost_saved_dollars) && (
          <div style={styles.deltas}>
            {signal.time_saved_hours && (
              <div style={{ ...styles.deltaChip, borderColor: accent + '44', color: accent }}>
                −{signal.time_saved_hours}h per project
              </div>
            )}
            {signal.cost_saved_dollars && (
              <div style={{ ...styles.deltaChip, borderColor: accent + '44', color: accent }}>
                −${signal.cost_saved_dollars.toLocaleString()}
              </div>
            )}
            {signal.quality_improvement_percent && (
              <div style={{ ...styles.deltaChip, borderColor: accent + '44', color: accent }}>
                +{signal.quality_improvement_percent}% quality
              </div>
            )}
          </div>
        )}
      </header>

      <div style={styles.body} itemProp="articleBody">
        {/* GEO summary (visible) */}
        {signal.geo_summary && (
          <div style={styles.summaryBlock}>
            <div style={styles.summaryLabel}>Summary</div>
            <p style={styles.summaryText}>{signal.geo_summary}</p>
          </div>
        )}

        {/* Creative implication (visible) */}
        {signal.description && (
          <div style={styles.summaryBlock}>
            <div style={styles.summaryLabel}>What this means for your craft</div>
            <p style={styles.summaryText}>{signal.description}</p>
          </div>
        )}

        {/* Action item — GATED */}
        <div style={styles.gateBlock}>
          <div style={styles.gateOverlay}>
            <div style={styles.gateContent}>
              <div style={styles.gateTitle}>Action item + full signal context</div>
              <p style={styles.gateText}>
                GenLens members get the action item, all 10 intelligence dimensions, and a daily briefing across 130+ sources.
              </p>
              <a href="/auth/invite" style={{ ...styles.gateBtn, background: accent, color: '#0e0e0e' }}>
                Get early access →
              </a>
              <div style={styles.gateNote}>Invite-only beta. Free to join.</div>
            </div>
          </div>
          <div style={styles.gateBlurred}>
            <p>Immediately update your rendering pipeline. Switch to the new batch mode — it requires no config change if you're already on the current stable release. Run a single product through first to validate output quality before enabling for your full queue.</p>
            <p>Block 2 hours this week to test the integration. The time-to-value is the fastest you'll see this quarter.</p>
          </div>
        </div>

        {/* Tools */}
        {toolNames.length > 0 && (
          <div style={styles.toolList}>
            <div style={styles.toolListLabel}>Tools in this signal</div>
            <div style={styles.toolChips}>
              {toolNames.map(t => (
                <a key={t} href={`/tools/${t}`} style={styles.toolChip}>{t}</a>
              ))}
            </div>
          </div>
        )}

        {/* Source */}
        {signal.source_url && (
          <div style={styles.sourceRow}>
            <span style={styles.muted}>Source:</span>
            <a href={signal.source_url} target="_blank" rel="noopener" style={styles.link}>
              {signal.source_name || signal.source_platform} →
            </a>
          </div>
        )}
      </div>

      {related.length > 0 && (
        <aside style={styles.related} aria-labelledby="related-label">
          <h2 id="related-label" style={styles.relatedLabel}>Related signals</h2>
          <div style={styles.relatedGrid}>
            {related.map((r: { id: number; title: string; geo_summary: string; dimension: number; created_at: string }) => (
              <a href={`/signals/${r.id}`} key={r.id} style={styles.relatedItem}>
                <article>
                  <div style={styles.relatedDimension}>{DIMENSION_LABELS[r.dimension]}</div>
                  <h3 style={styles.relatedTitle}>{r.title}</h3>
                  {r.geo_summary && (
                    <p style={styles.relatedSummary}>{r.geo_summary.slice(0, 100)}…</p>
                  )}
                </article>
              </a>
            ))}
          </div>
        </aside>
      )}
    </article>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: { maxWidth: 740, margin: '0 auto', padding: '24px 20px 80px', fontFamily: '"IBM Plex Mono", monospace' },
  breadcrumb: { display: 'flex', gap: 6, alignItems: 'center', fontSize: 11, marginBottom: 24, color: 'rgba(255,255,255,0.3)' },
  link: { color: '#c8f04a', textDecoration: 'none' },
  sep: { color: 'rgba(255,255,255,0.15)' },
  muted: { color: 'rgba(255,255,255,0.3)' },
  header: { marginBottom: 32 },
  signalMeta: { display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 16 },
  verticalBadge: { fontSize: 10, padding: '3px 8px', borderRadius: 2, border: '0.5px solid', letterSpacing: '0.06em', textTransform: 'uppercase' },
  dimensionBadge: { fontSize: 10, padding: '3px 8px', border: '0.5px solid rgba(255,255,255,0.12)', color: 'rgba(255,255,255,0.45)', borderRadius: 2 },
  dateMuted: { fontSize: 10, color: 'rgba(255,255,255,0.25)', marginLeft: 'auto' },
  title: { fontSize: 26, fontFamily: '"Playfair Display", serif', fontWeight: 700, color: '#fff', lineHeight: 1.35, marginBottom: 16, margin: '0 0 16px' },
  hook: { fontSize: 14, color: 'rgba(255,255,255,0.65)', lineHeight: 1.7, borderLeft: '3px solid', paddingLeft: 14, margin: '0 0 20px', fontStyle: 'italic' },
  deltas: { display: 'flex', gap: 8, flexWrap: 'wrap' },
  deltaChip: { fontSize: 11, padding: '4px 10px', border: '0.5px solid', borderRadius: 2, fontWeight: 600 },
  body: { display: 'flex', flexDirection: 'column', gap: 24 },
  summaryBlock: { paddingBottom: 24, borderBottom: '0.5px solid rgba(255,255,255,0.06)' },
  summaryLabel: { fontSize: 9, letterSpacing: '0.1em', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', marginBottom: 10 },
  summaryText: { fontSize: 13, lineHeight: 1.8, color: 'rgba(255,255,255,0.75)', margin: 0 },
  gateBlock: { position: 'relative', borderRadius: 6, overflow: 'hidden', border: '0.5px solid rgba(255,255,255,0.1)' },
  gateOverlay: {
    position: 'absolute', inset: 0, zIndex: 2,
    background: 'linear-gradient(to bottom, rgba(14,14,14,0.3) 0%, rgba(14,14,14,0.98) 40%)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  gateContent: { textAlign: 'center', padding: '20px 32px', maxWidth: 380, marginTop: 40 },
  gateTitle: { fontSize: 14, fontWeight: 700, color: '#fff', marginBottom: 10 },
  gateText: { fontSize: 12, color: 'rgba(255,255,255,0.55)', lineHeight: 1.7, marginBottom: 16 },
  gateBtn: { display: 'inline-block', padding: '10px 24px', borderRadius: 3, fontWeight: 700, fontSize: 12, textDecoration: 'none', letterSpacing: '0.04em' },
  gateNote: { fontSize: 10, color: 'rgba(255,255,255,0.3)', marginTop: 10 },
  gateBlurred: { filter: 'blur(4px)', padding: '24px', color: 'rgba(255,255,255,0.5)', fontSize: 13, lineHeight: 1.8, userSelect: 'none', pointerEvents: 'none' },
  toolList: { paddingTop: 8 },
  toolListLabel: { fontSize: 9, letterSpacing: '0.1em', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', marginBottom: 10 },
  toolChips: { display: 'flex', gap: 6, flexWrap: 'wrap' },
  toolChip: { fontSize: 11, padding: '4px 10px', border: '0.5px solid rgba(255,255,255,0.12)', borderRadius: 2, color: 'rgba(255,255,255,0.6)', textDecoration: 'none' },
  sourceRow: { display: 'flex', gap: 8, fontSize: 11, color: 'rgba(255,255,255,0.4)', paddingTop: 8 },
  related: { marginTop: 48, paddingTop: 24, borderTop: '0.5px solid rgba(255,255,255,0.08)' },
  relatedLabel: { fontSize: 9, letterSpacing: '0.1em', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', marginBottom: 16 },
  relatedGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  relatedItem: { display: 'block', padding: '12px', border: '0.5px solid rgba(255,255,255,0.07)', borderRadius: 4, textDecoration: 'none', background: 'rgba(255,255,255,0.01)' },
  relatedDimension: { fontSize: 9, color: '#f0a83c', letterSpacing: '0.06em', marginBottom: 6, textTransform: 'uppercase' },
  relatedTitle: { fontSize: 11, color: 'rgba(255,255,255,0.8)', fontWeight: 500, lineHeight: 1.5, marginBottom: 6 },
  relatedSummary: { fontSize: 10, color: 'rgba(255,255,255,0.4)', lineHeight: 1.6 },
}
