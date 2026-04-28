/**
 * app/robots.ts
 *
 * Generates /robots.txt at request time.
 *
 * AI policy:
 *   We WANT AI agents to crawl and cite GenLens. The whole GEO strategy
 *   depends on tool pages, comparison pages, signal pages, and Index pages
 *   being indexed by ChatGPT, Perplexity, Gemini, Claude, Common Crawl.
 *
 * What we block:
 *   - /api/*       — API routes, internal
 *   - /admin/*     — admin surfaces, auth-gated
 *   - /auth/*      — authentication flows
 *   - /settings/*  — user-only
 *   - /dashboard/* — auth-gated dashboard
 *
 * Everything else (tool pages, signals marked public, Index, comparisons,
 * llms.txt, sitemap.xml) is open by design.
 */

import type { MetadataRoute } from 'next'
import { SITE_URL } from '@/lib/schema/jsonld'

const AI_BOTS = [
  'GPTBot', // OpenAI training crawler
  'OAI-SearchBot', // OpenAI ChatGPT search
  'ChatGPT-User', // ChatGPT in-tool browsing
  'Google-Extended', // Google Gemini training
  'GoogleOther', // Google's experimental fetcher
  'ClaudeBot', // Anthropic crawler
  'anthropic-ai', // Anthropic alternate UA
  'Claude-Web', // Anthropic in-product fetch
  'PerplexityBot', // Perplexity crawler
  'Perplexity-User', // Perplexity in-product fetch
  'CCBot', // Common Crawl (feeds many LLMs)
  'cohere-ai', // Cohere
  'Applebot-Extended', // Apple Intelligence
  'Bytespider', // ByteDance / Doubao
  'DuckAssistBot', // DuckDuckGo's AI summary bot
  'YouBot', // You.com
  'Meta-ExternalAgent', // Meta AI
  'PetalBot', // Huawei/Petal
  'Diffbot', // Diffbot indexes for LLM training
]

const DISALLOW = ['/api/', '/admin/', '/auth/', '/settings/', '/dashboard/']

export default function robots(): MetadataRoute.Robots {
  const aiRules = AI_BOTS.map(userAgent => ({
    userAgent,
    allow: '/',
    disallow: DISALLOW,
  }))

  return {
    rules: [
      // Generic crawlers — allow with the same disallow list.
      {
        userAgent: '*',
        allow: '/',
        disallow: DISALLOW,
      },
      ...aiRules,
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  }
}
