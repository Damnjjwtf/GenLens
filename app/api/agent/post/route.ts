/**
 * app/api/agent/post/route.ts
 *
 * Explicit posting endpoint. Takes an approved queue item id +
 * target platforms, posts to each, writes post_results, and updates
 * the queue item to 'published' on first success.
 *
 * POST body: { queueItemId: number, platforms: ('discord' | 'x' | 'linkedin')[], use_embed?: boolean }
 *
 * Discord is the only platform implemented in this pass. X and LinkedIn
 * return 'not_implemented' and skip without failing the whole request.
 */

import { NextRequest, NextResponse } from 'next/server'
import { neon } from '@neondatabase/serverless'
import { auth } from '@/auth'
import { postToDiscord } from '@/lib/social/discord'

const sql = neon(process.env.DATABASE_URL!)

type Platform = 'discord' | 'x' | 'linkedin'

interface QueueRow {
  id: number
  output_type: string
  content: string
  title: string | null
  target_url: string | null
  vertical: string | null
  signal_ids: number[] | null
  status: string
}

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user || (session.user as { role?: string }).role !== 'admin') {
    return NextResponse.json({ error: 'Admin only' }, { status: 403 })
  }

  const body = (await req.json().catch(() => ({}))) as {
    queueItemId?: number
    platforms?: Platform[]
    use_embed?: boolean
  }

  const { queueItemId, platforms, use_embed } = body

  if (!queueItemId || !platforms?.length) {
    return NextResponse.json(
      { error: 'Missing queueItemId or platforms' },
      { status: 400 },
    )
  }

  const [item] = (await sql`
    SELECT id, output_type, content, title, target_url, vertical, signal_ids, status
    FROM growth_agent_queue
    WHERE id = ${queueItemId}
  `) as unknown as QueueRow[]

  if (!item) {
    return NextResponse.json({ error: 'Queue item not found' }, { status: 404 })
  }

  if (item.status !== 'approved' && item.status !== 'draft') {
    return NextResponse.json(
      { error: `Cannot post item with status=${item.status}` },
      { status: 400 },
    )
  }

  // Look up signal_type from the first associated signal (drives Discord channel routing)
  let signalType: string | null = null
  if (item.signal_ids?.length) {
    const rows = (await sql`
      SELECT signal_type FROM signals WHERE id = ${item.signal_ids[0]}
    `) as unknown as { signal_type: string | null }[]
    signalType = rows[0]?.signal_type ?? null
  }

  const results: Array<{
    platform: Platform
    ok: boolean
    error?: string
    post_id?: string
    post_url?: string
    channel?: string
    result_id?: number
  }> = []

  for (const platform of platforms) {
    if (platform === 'discord') {
      // The agent often stores content as JSON. Try to extract a clean string.
      const text = extractText(item.content)

      const out = await postToDiscord({
        content: text,
        title: item.title,
        target_url: item.target_url,
        vertical: item.vertical,
        signal_type: signalType,
        output_type: item.output_type,
        use_embed,
      })

      const [logged] = (await sql`
        INSERT INTO post_results (
          queue_item_id, platform, channel,
          platform_post_id, platform_post_url,
          status, error_message
        )
        VALUES (
          ${item.id}, 'discord', ${out.webhook_resolved_to ?? out.channel ?? null},
          ${out.message_id ?? null}, ${out.message_url ?? null},
          ${out.ok ? 'posted' : 'failed'}, ${out.error ?? null}
        )
        RETURNING id
      `) as unknown as { id: number }[]

      results.push({
        platform,
        ok: out.ok,
        error: out.error,
        post_id: out.message_id,
        post_url: out.message_url,
        channel: out.webhook_resolved_to ?? out.channel ?? undefined,
        result_id: logged?.id,
      })
      continue
    }

    // X and LinkedIn — wired up next session.
    const [logged] = (await sql`
      INSERT INTO post_results (queue_item_id, platform, status, error_message)
      VALUES (${item.id}, ${platform}, 'failed', 'not_implemented')
      RETURNING id
    `) as unknown as { id: number }[]

    results.push({
      platform,
      ok: false,
      error: 'not_implemented',
      result_id: logged?.id,
    })
  }

  const anySuccess = results.some(r => r.ok)
  // status is narrowed to 'approved' | 'draft' by the guard above, so we
  // know it isn't 'published' here — the early return at line 65 ensures it.
  if (anySuccess) {
    await sql`
      UPDATE growth_agent_queue SET
        status = 'published',
        published_at = COALESCE(published_at, NOW()),
        updated_at = NOW()
      WHERE id = ${item.id}
    `
  }

  return NextResponse.json({
    success: anySuccess,
    queue_item_id: item.id,
    results,
  })
}

/**
 * Queue items often store content as JSON (e.g. {hook_sentence, geo_summary}).
 * Pull the most natural-language field for posting.
 */
function extractText(raw: string): string {
  if (!raw) return ''
  try {
    const parsed = JSON.parse(raw)
    if (typeof parsed === 'string') return parsed
    if (parsed && typeof parsed === 'object') {
      const obj = parsed as Record<string, unknown>
      const candidates = [
        obj.post_text,
        obj.hook_sentence,
        obj.summary,
        obj.geo_summary,
        obj.content,
        obj.text,
      ]
      for (const c of candidates) {
        if (typeof c === 'string' && c.trim()) return c
      }
      // Fall back to a flattened key:value join for visibility
      return Object.entries(obj)
        .filter(([, v]) => typeof v === 'string')
        .map(([k, v]) => `${k}: ${v}`)
        .join('\n')
    }
    return String(parsed)
  } catch {
    return raw
  }
}
