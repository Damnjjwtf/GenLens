#!/usr/bin/env tsx
/**
 * Publish approved queue items (for debugging/testing).
 * Simpl simplified version: just updates status to published.
 * Discord posting requires API call from Next.js context, so it's skipped here.
 */

import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

async function publishGeoBlock(item: any): Promise<void> {
  if (!item.tool_slug) return
  const content = JSON.parse(item.content as string)

  await sql`
    UPDATE tools SET
      geo_summary = ${content.geo_summary || null},
      geo_qa_blocks = ${content.qa_blocks ? JSON.stringify(content.qa_blocks) : null},
      updated_at = NOW()
    WHERE slug = ${item.tool_slug}
  `
  console.log(`Published GEO block for ${item.tool_slug}`)
}

async function publishSignalPage(item: any): Promise<void> {
  const signalIds = item.signal_ids as number[] | null
  if (!signalIds?.length) return

  const content = JSON.parse(item.content as string)

  await sql`
    UPDATE signals SET
      geo_summary = ${content.geo_summary || null},
      hook_sentence = ${content.hook_sentence || null},
      is_public = true,
      updated_at = NOW()
    WHERE id = ${signalIds[0]}
  `
  console.log(`Published signal page for signal ${signalIds[0]}`)
}

async function main() {
  try {
    console.log('Publishing approved queue items...')

    const items = await sql`
      SELECT * FROM growth_agent_queue
      WHERE status = 'approved'
      ORDER BY created_at ASC
    `

    console.log(`Found ${items.length} items to publish`)

    for (const item of items) {
      try {
        switch (item.output_type) {
          case 'geo_block':
            await publishGeoBlock(item)
            break
          case 'signal_page':
            await publishSignalPage(item)
            break
          case 'social_discord':
            console.log(`Discord post (ID ${item.id}) - requires Next.js API context`)
            break
          default:
            console.log(`${item.output_type} (ID ${item.id}) - no auto-publish`)
        }

        // Mark as published
        await sql`
          UPDATE growth_agent_queue SET
            status = 'published',
            published_at = NOW(),
            updated_at = NOW()
          WHERE id = ${item.id}
        `
      } catch (err) {
        console.error(`Error publishing item ${item.id}:`, err instanceof Error ? err.message : err)
      }
    }

    console.log('Publishing complete!')
  } catch (err) {
    console.error('Fatal error:', err)
    process.exit(1)
  }
}

main()
