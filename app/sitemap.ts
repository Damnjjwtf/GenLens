/**
 * app/sitemap.ts
 *
 * Generates /sitemap.xml at request time. Lists every public URL the site
 * exposes so crawlers (and AI agents that respect sitemaps) can discover
 * tool pages, signal pages, comparison pages, and Index snapshots.
 *
 * Source of truth is the DB — no hard-coded slugs.
 */

import type { MetadataRoute } from 'next'
import { neon } from '@neondatabase/serverless'
import { SITE_URL } from '@/lib/schema/jsonld'

const sql = neon(process.env.DATABASE_URL!)

export const revalidate = 3600 // 1 hour — sitemap can be slightly stale

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date()

  // Static routes
  const staticEntries: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, lastModified: now, changeFrequency: 'daily', priority: 1.0 },
    { url: `${SITE_URL}/tools`, lastModified: now, changeFrequency: 'daily', priority: 0.9 },
    { url: `${SITE_URL}/index`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
  ]

  // Dynamic: tools, signals, comparisons, indices
  const [tools, signals, comparisons, indices] = await Promise.all([
    sql`
      SELECT slug, updated_at FROM tools
      WHERE is_public = true
    ` as Promise<{ slug: string; updated_at: string }[]>,
    sql`
      SELECT id, COALESCE(published_at, created_at) AS updated_at FROM signals
      WHERE is_public = true
    ` as Promise<{ id: number; updated_at: string }[]>,
    sql`
      SELECT slug, updated_at FROM tool_comparisons
      WHERE is_public = true
    ` as Promise<{ slug: string; updated_at: string }[]>,
    sql`
      SELECT week_start_date::text AS week_start_date, vertical, updated_at
      FROM index_snapshots
      WHERE status = 'published'
    ` as Promise<{ week_start_date: string; vertical: string; updated_at: string }[]>,
  ])

  const toolEntries: MetadataRoute.Sitemap = tools.map(t => ({
    url: `${SITE_URL}/tools/${t.slug}`,
    lastModified: new Date(t.updated_at),
    changeFrequency: 'weekly',
    priority: 0.8,
  }))

  const signalEntries: MetadataRoute.Sitemap = signals.map(s => ({
    url: `${SITE_URL}/signals/${s.id}`,
    lastModified: new Date(s.updated_at),
    changeFrequency: 'monthly',
    priority: 0.6,
  }))

  const compareEntries: MetadataRoute.Sitemap = comparisons.map(c => ({
    url: `${SITE_URL}/compare/${c.slug}`,
    lastModified: new Date(c.updated_at),
    changeFrequency: 'monthly',
    priority: 0.7,
  }))

  const indexEntries: MetadataRoute.Sitemap = indices.map(i => ({
    url: `${SITE_URL}/index/${i.week_start_date}`,
    lastModified: new Date(i.updated_at),
    changeFrequency: 'monthly',
    priority: 0.85,
  }))

  return [
    ...staticEntries,
    ...toolEntries,
    ...indexEntries,
    ...compareEntries,
    ...signalEntries,
  ]
}
