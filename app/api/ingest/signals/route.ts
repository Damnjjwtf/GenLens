import { createHash, timingSafeEqual } from 'node:crypto'
import { NextRequest, NextResponse } from 'next/server'
import { pool } from '@/lib/db'
import { validateIngestEnvelope } from '@/lib/ingest/validate'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const MAX_BYTES = 512 * 1024

function authorized(header: string | null, token: string): boolean {
  const actual = Buffer.from(header || '', 'utf8')
  const expected = Buffer.from('Bearer ' + token, 'utf8')
  return actual.length === expected.length && timingSafeEqual(actual, expected)
}

// This one statement preserves append-only events and updates the projection
// atomically. An old observation cannot replace a newer projection.
const saveStatement = [
  'WITH added_event AS (',
  '  INSERT INTO ledger_signal_events',
  '    (event_id, idempotency_key, signal_id, actor_id, content_hash, record)',
  '  VALUES ($1, $2, $3, $4, $5, $6::jsonb)',
  '  ON CONFLICT (idempotency_key) DO NOTHING',
  '  RETURNING event_id',
  '), projected AS (',
  '  INSERT INTO ledger_signals (',
  '    signal_id, actor_id, status, lenses, verticals, title, summary, canonical_url,',
  '    change, mechanism, use_case, impact, recommended_action, confidence,',
  '    evidence, record, first_observed_at, last_observed_at, observation_count, last_event_id',
  '  )',
  '  SELECT $3, $4, $7, $8::text[], $9::text[], $10, $11, $12,',
  '    $13, $14, $15, $16, $17, $18,',
  '    $19::jsonb, $6::jsonb, $20::timestamptz, $21::timestamptz, $22, $1',
  '  FROM added_event',
  '  ON CONFLICT (signal_id) DO UPDATE SET',
  '    actor_id = EXCLUDED.actor_id,',
  '    status = EXCLUDED.status,',
  '    lenses = EXCLUDED.lenses,',
  '    verticals = EXCLUDED.verticals,',
  '    title = EXCLUDED.title,',
  '    summary = EXCLUDED.summary,',
  '    canonical_url = EXCLUDED.canonical_url,',
  '    change = EXCLUDED.change,',
  '    mechanism = EXCLUDED.mechanism,',
  '    use_case = EXCLUDED.use_case,',
  '    impact = EXCLUDED.impact,',
  '    recommended_action = EXCLUDED.recommended_action,',
  '    confidence = EXCLUDED.confidence,',
  '    evidence = EXCLUDED.evidence,',
  '    record = EXCLUDED.record,',
  '    first_observed_at = LEAST(ledger_signals.first_observed_at, EXCLUDED.first_observed_at),',
  '    last_observed_at = EXCLUDED.last_observed_at,',
  '    observation_count = EXCLUDED.observation_count,',
  '    last_event_id = EXCLUDED.last_event_id,',
  '    updated_at = NOW()',
  '  WHERE ledger_signals.last_observed_at < EXCLUDED.last_observed_at',
  '     OR (ledger_signals.last_observed_at = EXCLUDED.last_observed_at',
  '         AND ledger_signals.observation_count < EXCLUDED.observation_count)',
  '  RETURNING signal_id',
  ')',
  'SELECT (SELECT COUNT(*)::integer FROM added_event) AS events_added,',
  '       (SELECT COUNT(*)::integer FROM projected) AS projections_changed',
].join('\n')

export async function POST(request: NextRequest) {
  const token = process.env.GENLENS_INGEST_TOKEN
  if (!token || token.length < 32 || !pool) {
    return NextResponse.json({ error: 'Ingestion is not configured' }, { status: 503 })
  }
  if (!authorized(request.headers.get('authorization'), token)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
    return NextResponse.json({ error: 'Expected JSON' }, { status: 415 })
  }
  if (Number(request.headers.get('content-length') || 0) > MAX_BYTES) {
    return NextResponse.json({ error: 'Payload too large' }, { status: 413 })
  }

  let text: string
  try {
    text = await request.text()
  } catch {
    return NextResponse.json({ error: 'Unreadable body' }, { status: 400 })
  }
  if (Buffer.byteLength(text, 'utf8') > MAX_BYTES) {
    return NextResponse.json({ error: 'Payload too large' }, { status: 413 })
  }

  let input: unknown
  try {
    input = JSON.parse(text)
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }
  const checked = validateIngestEnvelope(input)
  if (!checked.ok) {
    return NextResponse.json({ error: 'Contract validation failed', reasons: checked.errors }, { status: 422 })
  }

  const { event_id, idempotency_key, actor_id, record: s } = checked.data
  const serialized = JSON.stringify(s)
  const digest = createHash('sha256').update(serialized).digest('hex')
  const values = [
    event_id, idempotency_key, s.id, actor_id, digest, serialized,
    s.status, s.lenses, s.verticals, s.title, s.summary, s.canonical_url,
    s.change, s.mechanism, s.use_case, s.impact, s.recommended_action, s.confidence,
    JSON.stringify(s.evidence), s.first_observed_at, s.last_observed_at, s.observation_count,
  ]

  try {
    const result = await pool.query(saveStatement, values)
    const outcome = result.rows[0] as { events_added: number; projections_changed: number }
    if (Number(outcome.events_added) === 0) {
      const previous = await pool.query(
        'SELECT content_hash, actor_id, signal_id FROM ledger_signal_events WHERE idempotency_key = $1 LIMIT 1',
        [idempotency_key],
      )
      const row = previous.rows[0] as { content_hash: string; actor_id: string; signal_id: string } | undefined
      if (!row || row.content_hash !== digest || row.actor_id !== actor_id || row.signal_id !== s.id) {
        return NextResponse.json({ error: 'Idempotency conflict' }, { status: 409 })
      }
      return NextResponse.json({ ok: true, duplicate: true, event_id, signal_id: s.id })
    }
    return NextResponse.json({
      ok: true, duplicate: false, projected: Number(outcome.projections_changed) > 0,
      event_id, signal_id: s.id,
    }, { status: 201 })
  } catch (error) {
    console.error('[ingest/signals] storage failure', error instanceof Error ? error.name : 'unknown')
    return NextResponse.json({ error: 'Ingestion storage unavailable' }, { status: 503 })
  }
}