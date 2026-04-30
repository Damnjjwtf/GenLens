/**
 * lib/social/discord.ts
 *
 * Discord webhook posting. No OAuth — each channel has its own webhook URL
 * stored as an env var. The Growth Agent tags each queue item with
 * vertical + signal_type, and we route to the right channel from there.
 *
 * Channel routing rules:
 *   - signal_type === 'legal' (Dimension 6)        → legal_alerts
 *   - signal_type === 'hiring' (Dimension 7)       → hiring
 *   - signal_type === 'tool_release'                → tool_releases (cross-post)
 *   - signal_type === 'template'                    → templates
 *   - vertical === 'product_photography'            → pp
 *   - vertical === 'filmmaking'                     → fm
 *   - vertical === 'digital_humans'                 → dh
 *   - output_type === 'index_post'                  → announcements
 *   - else                                          → general
 *
 * If a routed webhook env is missing, falls back to general.
 * If general is missing too, returns { ok: false, error: 'no_webhook' }.
 */

export type DiscordChannel =
  | 'general'
  | 'announcements'
  | 'pp'
  | 'fm'
  | 'dh'
  | 'tool_releases'
  | 'legal_alerts'
  | 'hiring'
  | 'templates'

const CHANNEL_ENV: Record<DiscordChannel, string> = {
  general: 'DISCORD_WEBHOOK_URL_GENERAL',
  announcements: 'DISCORD_WEBHOOK_URL_ANNOUNCEMENTS',
  pp: 'DISCORD_WEBHOOK_URL_PP',
  fm: 'DISCORD_WEBHOOK_URL_FM',
  dh: 'DISCORD_WEBHOOK_URL_DH',
  tool_releases: 'DISCORD_WEBHOOK_URL_TOOL_RELEASES',
  legal_alerts: 'DISCORD_WEBHOOK_URL_LEGAL_ALERTS',
  hiring: 'DISCORD_WEBHOOK_URL_HIRING',
  templates: 'DISCORD_WEBHOOK_URL_TEMPLATES',
}

interface RouteContext {
  vertical?: string | null
  signal_type?: string | null
  output_type?: string | null
}

export function pickChannel(ctx: RouteContext): DiscordChannel {
  const { vertical, signal_type, output_type } = ctx

  if (signal_type === 'legal') return 'legal_alerts'
  if (signal_type === 'hiring') return 'hiring'
  if (signal_type === 'tool_release') return 'tool_releases'
  if (signal_type === 'template') return 'templates'

  if (output_type === 'index_post') return 'announcements'

  if (vertical === 'product_photography') return 'pp'
  if (vertical === 'filmmaking') return 'fm'
  if (vertical === 'digital_humans') return 'dh'

  return 'general'
}

function resolveWebhook(channel: DiscordChannel): { url: string; resolvedChannel: DiscordChannel } | null {
  const direct = process.env[CHANNEL_ENV[channel]]
  if (direct) return { url: direct, resolvedChannel: channel }

  const fallback = process.env[CHANNEL_ENV.general]
  if (fallback) return { url: fallback, resolvedChannel: 'general' }

  return null
}

interface DiscordEmbed {
  title?: string
  description?: string
  url?: string
  color?: number
  fields?: { name: string; value: string; inline?: boolean }[]
  footer?: { text: string }
  timestamp?: string
}

interface DiscordPayload {
  content?: string
  username?: string
  avatar_url?: string
  embeds?: DiscordEmbed[]
}

export interface PostInput {
  content: string                  // The body text from the queue item
  title?: string | null            // Optional headline (becomes embed title)
  target_url?: string | null       // Optional link
  vertical?: string | null
  signal_type?: string | null
  output_type?: string | null
  use_embed?: boolean              // If true, post as embed instead of plain content
}

export interface PostOutcome {
  ok: boolean
  channel: DiscordChannel | null
  webhook_resolved_to: DiscordChannel | null
  message_id?: string
  message_url?: string
  error?: string
}

const VERTICAL_COLOR: Record<string, number> = {
  product_photography: 0xc8f04a, // lime
  filmmaking: 0xf0a83c,          // amber
  digital_humans: 0xb07af0,      // purple
}

/**
 * Post to Discord. The webhook URL is selected from the channel routing.
 * Discord webhooks return a Message object when ?wait=true is appended.
 */
export async function postToDiscord(input: PostInput): Promise<PostOutcome> {
  const channel = pickChannel(input)
  const resolved = resolveWebhook(channel)

  if (!resolved) {
    return {
      ok: false,
      channel,
      webhook_resolved_to: null,
      error: `no_webhook: missing ${CHANNEL_ENV[channel]} and ${CHANNEL_ENV.general}`,
    }
  }

  const payload: DiscordPayload = {
    username: 'GenLens',
  }

  if (input.use_embed && input.title) {
    const color = (input.vertical && VERTICAL_COLOR[input.vertical]) ?? 0xc8f04a
    payload.embeds = [
      {
        title: input.title,
        description: input.content.slice(0, 4000), // Discord embed description limit
        url: input.target_url || undefined,
        color,
        footer: { text: 'genlens.app' },
        timestamp: new Date().toISOString(),
      },
    ]
  } else {
    // Plain content. 2000 char limit per Discord.
    let body = input.content
    if (input.title && !body.startsWith(input.title)) {
      body = `**${input.title}**\n\n${body}`
    }
    if (input.target_url) {
      body = `${body}\n\n${input.target_url}`
    }
    payload.content = body.length > 2000 ? body.slice(0, 1997) + '...' : body
  }

  // ?wait=true makes Discord return the created message body so we can capture id + URL
  const url = `${resolved.url}${resolved.url.includes('?') ? '&' : '?'}wait=true`

  let res: Response
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch (e) {
    return {
      ok: false,
      channel,
      webhook_resolved_to: resolved.resolvedChannel,
      error: `fetch_failed: ${(e as Error).message}`,
    }
  }

  if (!res.ok) {
    const errText = await res.text().catch(() => '')
    return {
      ok: false,
      channel,
      webhook_resolved_to: resolved.resolvedChannel,
      error: `http_${res.status}: ${errText.slice(0, 300)}`,
    }
  }

  const msg = (await res.json().catch(() => null)) as
    | { id?: string; channel_id?: string }
    | null

  return {
    ok: true,
    channel,
    webhook_resolved_to: resolved.resolvedChannel,
    message_id: msg?.id,
    message_url:
      msg?.id && msg.channel_id
        ? `https://discord.com/channels/@me/${msg.channel_id}/${msg.id}`
        : undefined,
  }
}
