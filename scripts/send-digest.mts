/**
 * scripts/send-digest.mts
 *
 * Pulls top signals from the DB, composes a digest, and sends via Resend.
 *
 * Usage:
 *   set -a && source .env.local && set +a
 *   npx tsx scripts/send-digest.mts yopooskis@gmail.com
 *   npx tsx scripts/send-digest.mts --dry yopooskis@gmail.com   # preview only, no send
 */

import { neon } from '@neondatabase/serverless'
import { Resend } from 'resend'

const args = process.argv.slice(2)
const dry = args.includes('--dry')
const to = args.filter(a => !a.startsWith('--'))[0]

if (!to) {
  console.error('Usage: tsx scripts/send-digest.mts [--dry] <email>')
  process.exit(1)
}

if (!process.env.DATABASE_URL) {
  console.error('DATABASE_URL not set')
  process.exit(1)
}

if (!dry && !process.env.RESEND_API_KEY) {
  console.error('RESEND_API_KEY not set. Add it to .env.local or pass --dry to preview.')
  process.exit(1)
}

const sql = neon(process.env.DATABASE_URL)

interface SignalRow {
  id: number
  title: string
  summary: string | null
  description: string | null
  vertical: string
  dimension: number
  signal_type: string
  tool_names: string[] | null
  source_name: string
  source_url: string
  trending_score: number | null
}

const VERTICAL_LABEL: Record<string, string> = {
  product_photography: 'Product Photography',
  filmmaking: 'Filmmaking',
  digital_humans: 'Digital Humans',
}

const VERTICAL_ACCENT: Record<string, string> = {
  product_photography: '#c8f04a',
  filmmaking: '#f0a83c',
  digital_humans: '#b07af0',
}

async function main() {
  // Top 8 signals per vertical, prefer tool_release / cost_delta / legal_alert / hiring
  const PRIORITY_TYPES = ['tool_release', 'cost_delta', 'time_delta', 'legal_alert', 'hire_post', 'benchmark', 'workflow_template']

  const signals = (await sql`
    SELECT
      id, title, summary, description, vertical, dimension, signal_type,
      tool_names, source_name, source_url, trending_score
    FROM signals
    WHERE status = 'classified'
    ORDER BY
      CASE WHEN signal_type = ANY(${PRIORITY_TYPES}) THEN 0 ELSE 1 END,
      COALESCE(trending_score, 0) DESC,
      id DESC
    LIMIT 200
  `) as unknown as SignalRow[]

  // Group by vertical, take top 8 each
  const byVertical: Record<string, SignalRow[]> = {
    product_photography: [],
    filmmaking: [],
    digital_humans: [],
  }
  for (const s of signals) {
    const arr = byVertical[s.vertical]
    if (arr && arr.length < 8) arr.push(s)
  }

  const totals = (await sql`
    SELECT vertical, COUNT(*)::int AS n FROM signals GROUP BY vertical
  `) as unknown as { vertical: string; n: number }[]
  const totalMap = Object.fromEntries(totals.map(r => [r.vertical, r.n]))
  const grandTotal = totals.reduce((acc, r) => acc + r.n, 0)

  const today = new Date().toISOString().slice(0, 10)
  const subject = `GenLens Digest — ${today} — ${grandTotal} signals across 3 verticals`
  const html = renderHTML(today, grandTotal, totalMap, byVertical)
  const text = renderText(today, grandTotal, totalMap, byVertical)

  if (dry) {
    console.log('=== SUBJECT ===')
    console.log(subject)
    console.log('\n=== TEXT ===')
    console.log(text)
    console.log('\n=== HTML preview written to /tmp/digest-preview.html ===')
    const fs = await import('node:fs')
    fs.writeFileSync('/tmp/digest-preview.html', html)
    return
  }

  const resend = new Resend(process.env.RESEND_API_KEY)
  const from = process.env.EMAIL_FROM || 'GenLens <onboarding@resend.dev>'
  const result = await resend.emails.send({
    from,
    to,
    subject,
    html,
    text,
  })

  if (result.error) {
    console.error('Resend error:', result.error)
    process.exit(1)
  }
  console.log(`Sent. Message id: ${result.data?.id}`)
}

function renderText(
  date: string,
  grandTotal: number,
  totals: Record<string, number>,
  byVertical: Record<string, SignalRow[]>,
): string {
  const lines: string[] = []
  lines.push(`GenLens Digest — ${date}`)
  lines.push(`${grandTotal} signals across 3 verticals`)
  lines.push('')
  for (const v of ['product_photography', 'filmmaking', 'digital_humans']) {
    lines.push(`## ${VERTICAL_LABEL[v]} (${totals[v] ?? 0})`)
    lines.push('')
    for (const s of byVertical[v]) {
      lines.push(`- [${s.signal_type}] ${s.title}`)
      const sum = s.summary || s.description || ''
      if (sum) lines.push(`  ${sum.slice(0, 240)}${sum.length > 240 ? '...' : ''}`)
      lines.push(`  ${s.source_name}: ${s.source_url}`)
      lines.push('')
    }
  }
  return lines.join('\n')
}

function renderHTML(
  date: string,
  grandTotal: number,
  totals: Record<string, number>,
  byVertical: Record<string, SignalRow[]>,
): string {
  const verticalSection = (v: string) => {
    const accent = VERTICAL_ACCENT[v]
    const items = byVertical[v]
      .map(s => {
        const sum = s.summary || s.description || ''
        const tools = s.tool_names?.length ? `<div style="font-size:11px;color:#9a9690;margin-top:4px;">tools: ${s.tool_names.slice(0, 4).join(', ')}</div>` : ''
        return `
          <li style="margin-bottom:18px;list-style:none;border-left:2px solid ${accent};padding-left:14px;">
            <div style="font-size:11px;letter-spacing:0.08em;color:${accent};text-transform:uppercase;font-weight:600;">${s.signal_type.replace(/_/g, ' ')}</div>
            <div style="font-size:15px;color:#e8e4dc;font-weight:500;line-height:1.4;margin:4px 0;">${escape(s.title)}</div>
            ${sum ? `<div style="font-size:13px;color:#9a9690;line-height:1.55;margin-top:4px;">${escape(sum.slice(0, 280))}${sum.length > 280 ? '...' : ''}</div>` : ''}
            ${tools}
            <div style="font-size:11px;color:#6a6660;margin-top:6px;">
              <a href="${s.source_url}" style="color:#5ab4f0;text-decoration:none;">${escape(s.source_name)} ↗</a>
            </div>
          </li>`
      })
      .join('')
    return `
      <section style="margin-top:32px;">
        <h2 style="font-size:13px;letter-spacing:0.12em;color:${accent};text-transform:uppercase;margin:0 0 6px;font-family:'IBM Plex Mono',monospace;font-weight:700;">
          ${VERTICAL_LABEL[v]}
        </h2>
        <div style="font-size:11px;color:#6a6660;margin-bottom:16px;letter-spacing:0.04em;">
          ${totals[v] ?? 0} signals scraped · top ${byVertical[v].length} shown
        </div>
        <ul style="padding:0;margin:0;">${items}</ul>
      </section>`
  }

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>GenLens Digest</title></head>
<body style="margin:0;padding:0;background:#0e0e0e;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:680px;margin:0 auto;padding:32px 24px;background:#0e0e0e;color:#e8e4dc;">
    <header style="border-bottom:0.5px solid #2a2a2a;padding-bottom:20px;">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:0.16em;color:#c8f04a;font-weight:700;">GENLENS</div>
      <h1 style="font-family:'Playfair Display',Georgia,serif;font-size:32px;line-height:1.15;margin:14px 0 8px;color:#e8e4dc;font-weight:600;">
        Daily Digest
      </h1>
      <div style="font-size:13px;color:#9a9690;font-family:'IBM Plex Mono',monospace;letter-spacing:0.04em;">
        ${date} · ${grandTotal} signals · ${Object.keys(totals).length} verticals
      </div>
    </header>
    ${verticalSection('product_photography')}
    ${verticalSection('filmmaking')}
    ${verticalSection('digital_humans')}
    <footer style="margin-top:48px;padding-top:20px;border-top:0.5px solid #2a2a2a;font-size:11px;color:#6a6660;font-family:'IBM Plex Mono',monospace;letter-spacing:0.04em;">
      Generated from ${grandTotal} classified signals · genlens.app
    </footer>
  </div>
</body></html>`
}

function escape(s: string): string {
  return s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!)
}

await main()
