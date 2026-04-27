/**
 * app/api/agent/queue/route.ts
 *
 * CRUD for the growth_agent_queue.
 * GET  /api/agent/queue          — list queue items (with filters)
 * POST /api/agent/queue/:id/approve  — approve + optionally publish
 * POST /api/agent/queue/:id/reject   — reject with reason
 * POST /api/agent/queue/:id/publish  — manually trigger publish
 */

import { NextRequest, NextResponse } from 'next/server'
import { neon } from '@neondatabase/serverless'
import { auth } from '@/auth'
import { postToDiscord } from '@/lib/social/discord'

const sql = neon(process.env.DATABASE_URL!)

// GET — list queue items
export async function GET(req: NextRequest) {
  const session = await auth()
  if (!session?.user || (session.user as { role?: string }).role !== 'admin') {
    return NextResponse.json({ error: 'Admin only' }, { status: 403 })
  }

  const { searchParams } = new URL(req.url)
  const status = searchParams.get('status') ?? 'draft'
  const output_type = searchParams.get('type')
  const vertical = searchParams.get('vertical')
  const limit = Math.min(parseInt(searchParams.get('limit') ?? '50'), 100)
  const offset = parseInt(searchParams.get('offset') ?? '0')

  let query = sql`
    SELECT
      gaq.*,
      u.email as approved_by_email
    FROM growth_agent_queue gaq
    LEFT JOIN users u ON u.id = gaq.approved_by
    WHERE gaq.status = ${status}
  `

  // Note: Neon serverless doesn't support dynamic query building cleanly,
  // so we fetch and filter in JS for the optional params.
  // For production, use a query builder like Drizzle or Kysely.
  const rows = await sql`
    SELECT
      gaq.*,
      u.email as approved_by_email
    FROM growth_agent_queue gaq
    LEFT JOIN users u ON u.id = gaq.approved_by
    WHERE gaq.status = ${status}
      AND (${output_type}::text IS NULL OR gaq.output_type = ${output_type})
      AND (${vertical}::text IS NULL OR gaq.vertical = ${vertical})
    ORDER BY gaq.created_at DESC
    LIMIT ${limit} OFFSET ${offset}
  `

  const [{ count }] = await sql`
    SELECT COUNT(*) FROM growth_agent_queue
    WHERE status = ${status}
      AND (${output_type}::text IS NULL OR output_type = ${output_type})
      AND (${vertical}::text IS NULL OR vertical = ${vertical})
  `

  return NextResponse.json({ items: rows, total: Number(count), offset, limit })
}

// PATCH — approve or reject a queue item
export async function PATCH(req: NextRequest) {
  const session = await auth()
  if (!session?.user || (session.user as { role?: string }).role !== 'admin') {
    return NextResponse.json({ error: 'Admin only' }, { status: 403 })
  }

  const body = await req.json()
  const { id, action, review_notes, rejection_reason, content, scheduled_for } = body

  if (!id || !action) {
    return NextResponse.json({ error: 'Missing id or action' }, { status: 400 })
  }

  if (action === 'approve') {
    const [updated] = await sql`
      UPDATE growth_agent_queue SET
        status = 'approved',
        review_notes = ${review_notes ?? null},
        content = COALESCE(${content ?? null}, content), -- allow edit on approve
        scheduled_for = ${scheduled_for ?? null},
        approved_by = ${(session.user as { id: string }).id},
        updated_at = NOW()
      WHERE id = ${id}
      RETURNING *
    `
    // If no scheduled_for, publish immediately
    if (!updated.scheduled_for) {
      await publishQueueItem(updated)
    }
    return NextResponse.json({ success: true, item: updated })
  }

  if (action === 'reject') {
    const [updated] = await sql`
      UPDATE growth_agent_queue SET
        status = 'rejected',
        rejection_reason = ${rejection_reason ?? null},
        review_notes = ${review_notes ?? null},
        updated_at = NOW()
      WHERE id = ${id}
      RETURNING *
    `
    return NextResponse.json({ success: true, item: updated })
  }

  if (action === 'edit') {
    // Save edits without changing status
    const [updated] = await sql`
      UPDATE growth_agent_queue SET
        content = ${content},
        review_notes = ${review_notes ?? null},
        updated_at = NOW()
      WHERE id = ${id}
      RETURNING *
    `
    return NextResponse.json({ success: true, item: updated })
  }

  return NextResponse.json({ error: 'Unknown action' }, { status: 400 })
}

// ─── Publish logic (per output type) ─────────────────────────

async function publishQueueItem(item: Record<string, unknown>): Promise<void> {
  switch (item.output_type) {
    case 'geo_block':
      await publishGeoBlock(item)
      break
    case 'signal_page':
      await publishSignalPage(item)
      break
    case 'comparison_page':
      await publishComparisonPage(item)
      break
    case 'social_discord':
      await publishDiscordPost(item)
      break
    // social_x, social_linkedin, index_post:
    // These are copied to clipboard / posted via social API
    // For now: mark published and notify admin via email
    default:
      break
  }

  await sql`
    UPDATE growth_agent_queue SET
      status = 'published',
      published_at = NOW(),
      updated_at = NOW()
    WHERE id = ${item.id as number}
  `
}

async function publishDiscordPost(item: Record<string, unknown>): Promise<void> {
  const rawContent = item.content as string
  let text = rawContent
  try {
    const parsed = JSON.parse(rawContent)
    if (typeof parsed === 'string') text = parsed
    else if (parsed && typeof parsed === 'object') {
      const o = parsed as Record<string, unknown>
      text =
        (o.post_text as string) ??
        (o.hook_sentence as string) ??
        (o.summary as string) ??
        (o.geo_summary as string) ??
        rawContent
    }
  } catch {
    /* keep raw */
  }

  let signalType: string | null = null
  const signalIds = item.signal_ids as number[] | null
  if (signalIds?.length) {
    const rows = (await sql`
      SELECT signal_type FROM signals WHERE id = ${signalIds[0]}
    `) as unknown as { signal_type: string | null }[]
    signalType = rows[0]?.signal_type ?? null
  }

  const out = await postToDiscord({
    content: text,
    title: (item.title as string | null) ?? null,
    target_url: (item.target_url as string | null) ?? null,
    vertical: (item.vertical as string | null) ?? null,
    signal_type: signalType,
    output_type: item.output_type as string,
  })

  await sql`
    INSERT INTO post_results (
      queue_item_id, platform, channel,
      platform_post_id, platform_post_url,
      status, error_message
    )
    VALUES (
      ${item.id as number}, 'discord', ${out.webhook_resolved_to ?? out.channel ?? null},
      ${out.message_id ?? null}, ${out.message_url ?? null},
      ${out.ok ? 'posted' : 'failed'}, ${out.error ?? null}
    )
  `
}

async function publishGeoBlock(item: Record<string, unknown>): Promise<void> {
  if (!item.tool_slug) return
  const content = JSON.parse(item.content as string)

  await sql`
    UPDATE tools SET
      geo_summary = ${content.geo_summary},
      geo_qa_blocks = ${JSON.stringify(content.qa_blocks)},
      faq_schema = ${item.faq_schema ? JSON.stringify(item.faq_schema) : null},
      meta_description = ${(item.meta_description as string) ?? null},
      updated_at = NOW()
    WHERE slug = ${item.tool_slug as string}
  `
}

async function publishSignalPage(item: Record<string, unknown>): Promise<void> {
  if (!item.signal_ids || !(item.signal_ids as number[]).length) return
  const signalId = (item.signal_ids as number[])[0]
  const content = JSON.parse(item.content as string)

  await sql`
    UPDATE signals SET
      geo_summary = ${content.geo_summary},
      hook_sentence = ${content.hook_sentence},
      is_public = true,
      updated_at = NOW()
    WHERE id = ${signalId}
  `
}

async function publishComparisonPage(item: Record<string, unknown>): Promise<void> {
  const content = JSON.parse(item.content as string)
  const targetUrl = item.target_url as string
  const slug = targetUrl?.split('/compare/')?.[1]
  if (!slug) return

  const [toolA, toolB] = slug.split('-vs-')

  await sql`
    INSERT INTO tool_comparisons (slug, tool_a_slug, tool_b_slug, summary, geo_qa_blocks, faq_schema, is_public)
    VALUES (
      ${slug},
      ${toolA},
      ${toolB},
      ${content.summary},
      ${JSON.stringify(content.qa_blocks)},
      ${item.faq_schema ? JSON.stringify(item.faq_schema) : null},
      true
    )
    ON CONFLICT (slug) DO UPDATE SET
      summary = EXCLUDED.summary,
      geo_qa_blocks = EXCLUDED.geo_qa_blocks,
      faq_schema = EXCLUDED.faq_schema,
      updated_at = NOW()
  `
}
