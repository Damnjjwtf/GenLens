/**
 * lib/schema/jsonld.ts
 *
 * Pure builders for schema.org JSON-LD payloads. Each function returns a
 * plain object that the page renders inside <script type="application/ld+json">.
 *
 * Goal: every public page emits enough structured data for AI engines
 * (ChatGPT, Perplexity, Gemini, Claude) to cite GenLens cleanly when users
 * ask about a tool, comparison, signal, or index.
 *
 * Reference: https://schema.org, https://developers.google.com/search/docs/appearance/structured-data
 */

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, '') || 'https://genlens.app'

export const SITE_NAME = 'GenLens'

/** WebSite schema with site-search action — enables Sitelinks Search Box. */
export function websiteLD() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    '@id': `${SITE_URL}#website`,
    url: SITE_URL,
    name: SITE_NAME,
    description:
      'Daily intelligence for creative technologists working in AI-accelerated visual production. Tracks 130+ sources across product photography, filmmaking, and digital humans.',
    publisher: { '@id': `${SITE_URL}#org` },
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${SITE_URL}/search?q={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  }
}

/** Organization schema — GenLens itself. */
export function organizationLD() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    '@id': `${SITE_URL}#org`,
    name: SITE_NAME,
    url: SITE_URL,
    description:
      'GenLens publishes the GenLens Score and the weekly GenLens Index — citable benchmarks for AI-accelerated visual production tools.',
    sameAs: [
      // Add social profiles as they go live.
    ],
  }
}

/** Breadcrumb list. Pass items as [{name, url}, ...] in order. */
export function breadcrumbLD(items: { name: string; url: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.name,
      item: it.url,
    })),
  }
}

interface ToolForLD {
  slug: string
  canonical_name: string
  geo_summary: string | null
  meta_description: string | null
  website_url: string | null
  current_score: number | null
  verticals: string[]
  categories: string[] | null
  signal_count: number | null
}

/**
 * SoftwareApplication is the most accurate schema.org type for AI creative tools.
 * The aggregateRating uses the GenLens Score (0-100) normalized to 0-5 with at
 * least signal_count as ratingCount when present.
 */
export function softwareApplicationLD(tool: ToolForLD) {
  const url = `${SITE_URL}/tools/${tool.slug}`
  const description =
    tool.geo_summary ||
    tool.meta_description ||
    `${tool.canonical_name}: GenLens intelligence on signals, score, and workflow templates.`

  const base: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    '@id': `${url}#tool`,
    name: tool.canonical_name,
    url,
    applicationCategory: pickAppCategory(tool.categories, tool.verticals),
    operatingSystem: 'Web',
    description,
  }
  if (tool.website_url) base.sameAs = [tool.website_url]
  if (typeof tool.current_score === 'number' && tool.current_score > 0) {
    base.aggregateRating = {
      '@type': 'AggregateRating',
      ratingValue: (tool.current_score / 20).toFixed(1), // 0-100 → 0-5
      bestRating: 5,
      worstRating: 0,
      ratingCount: Math.max(tool.signal_count ?? 1, 1),
      // Disambiguate that this is the GenLens Score, not user reviews.
      reviewAspect: 'GenLens Score (composite of speed, cost, quality, adoption)',
    }
  }
  return base
}

function pickAppCategory(
  categories: string[] | null,
  verticals: string[],
): string {
  if (categories?.includes('voice_synthesis')) return 'MultimediaApplication'
  if (categories?.includes('avatar')) return 'MultimediaApplication'
  if (verticals.includes('digital_humans')) return 'MultimediaApplication'
  if (verticals.includes('filmmaking')) return 'MultimediaApplication'
  if (verticals.includes('product_photography')) return 'DesignApplication'
  return 'DesignApplication'
}

/** FAQPage from Q&A blocks. */
export function faqLD(
  qa: { q: string; a: string }[],
  pageUrl?: string,
) {
  if (qa.length === 0) return null
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    ...(pageUrl ? { '@id': `${pageUrl}#faq` } : {}),
    mainEntity: qa.map(p => ({
      '@type': 'Question',
      name: p.q,
      acceptedAnswer: { '@type': 'Answer', text: p.a },
    })),
  }
}

interface SignalForLD {
  id: number
  title: string
  geo_summary: string | null
  hook_sentence: string | null
  description: string | null
  source_name: string
  source_url: string
  created_at: string
  vertical: string
  tool_names: string[] | null
}

/** NewsArticle for signal pages — surfaces well in news/research panels. */
export function articleLD(signal: SignalForLD) {
  const url = `${SITE_URL}/signals/${signal.id}`
  const body =
    signal.geo_summary || signal.hook_sentence || signal.description || signal.title
  return {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    '@id': `${url}#article`,
    headline: signal.title,
    description: body.slice(0, 280),
    url,
    mainEntityOfPage: url,
    datePublished: signal.created_at,
    dateModified: signal.created_at,
    isBasedOn: signal.source_url,
    author: { '@type': 'Organization', name: signal.source_name },
    publisher: { '@id': `${SITE_URL}#org` },
    about: signal.tool_names?.length
      ? signal.tool_names.map(n => ({ '@type': 'Thing', name: n }))
      : undefined,
    articleSection: signal.vertical.replace(/_/g, ' '),
  }
}

interface IndexForLD {
  vertical: string
  week_start_date: string
  headline: string | null
  lede: string | null
  top_tools: { rank: number; tool_slug: string; score: number }[]
}

/**
 * Dataset schema for Index pages. The Index is structured ranking data, so
 * Dataset is more honest than Article — and AI engines treat datasets as
 * citable sources of truth.
 */
export function indexDatasetLD(snapshot: IndexForLD) {
  const url = `${SITE_URL}/index/${snapshot.week_start_date}`
  const verticalLabel = snapshot.vertical.replace(/_/g, ' ')
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    '@id': `${url}#dataset-${snapshot.vertical}`,
    name: snapshot.headline || `GenLens Index — ${verticalLabel} — ${snapshot.week_start_date}`,
    description:
      snapshot.lede ||
      `Weekly GenLens Index for ${verticalLabel}: top tools by GenLens Score, biggest movers, new entries, notable exits.`,
    url,
    datePublished: snapshot.week_start_date,
    creator: { '@id': `${SITE_URL}#org` },
    keywords: [
      'AI creative tools',
      verticalLabel,
      'GenLens Score',
      'tool ranking',
      'weekly index',
    ],
    variableMeasured: 'GenLens Score (0-100)',
    measurementTechnique:
      'Composite of speed gain, cost gain, quality, and adoption velocity vs. baseline workflows',
  }
}
