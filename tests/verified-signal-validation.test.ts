import test from 'node:test'
import assert from 'node:assert/strict'
import { validateIngestEnvelope } from '../lib/ingest/validate'

function example(): Record<string, unknown> {
  const event_id = 'evt_' + 'a'.repeat(24)
  return {
    schema_version: '1.0.0',
    actor_id: 'genny',
    event_id,
    idempotency_key: event_id,
    record: {
      id: 'sig_' + 'b'.repeat(20),
      status: 'published',
      lenses: ['genny'],
      verticals: ['AI Filmmaking'],
      title: 'Verified workflow change',
      summary: 'A release that affects a workflow.',
      canonical_url: 'https://example.org/release',
      source: {
        name: 'Vendor releases', url: 'https://example.org',
        type: 'release_notes', priority: 'high', authoritative: true,
      },
      evidence: [{
        url: 'https://example.org/release', source_name: 'Vendor',
        source_url: 'https://example.org', source_type: 'release_notes',
        authoritative: true, published_at: '2026-10-10',
      }],
      change: 'A verifiable change',
      mechanism: 'An official API change',
      use_case: 'A repeatable production workflow',
      impact: 'Operators should rerun acceptance tests',
      recommended_action: 'test',
      confidence: 'primary-source',
      score: 8,
      rejection_reason: null,
      first_observed_at: '2026-10-10T12:00:00+00:00',
      last_observed_at: '2026-10-10T12:00:00+00:00',
      observation_count: 1,
      reviews: [],
      history: [],
    },
  }
}

function signal(envelope: Record<string, unknown>): Record<string, unknown> {
  return envelope.record as Record<string, unknown>
}

test('accepts the canonical 1.0.0 signal shape', () => {
  assert.equal(validateIngestEnvelope(example()).ok, true)
})
test('requires evidence for published signals', () => {
  const data = example()
  signal(data).evidence = []
  assert.equal(validateIngestEnvelope(data).ok, false)
})
test('rejects unknown record properties', () => {
  const data = example()
  signal(data).unverified_claim = 'Marketing copy pretending to be evidence'
  assert.equal(validateIngestEnvelope(data).ok, false)
})
test('rejects actor/lens mismatch', () => {
  const data = example()
  data.actor_id = 'marti'
  assert.equal(validateIngestEnvelope(data).ok, false)
})
test('rejects mismatched idempotency and event IDs', () => {
  const data = example()
  data.idempotency_key = 'evt_' + 'c'.repeat(24)
  assert.equal(validateIngestEnvelope(data).ok, false)
})
test('rejects wrong timestamp and unsafe evidence link', () => {
  const data = example()
  signal(data).first_observed_at = 'yesterday'
  const evidence = signal(data).evidence as Array<Record<string, unknown>>
  evidence[0].url = 'javascript:alert(1)'
  assert.equal(validateIngestEnvelope(data).ok, false)
})
test('rejects malformed nested source objects', () => {
  const data = example()
  const source = signal(data).source as Record<string, unknown>
  source.extra = true
  assert.equal(validateIngestEnvelope(data).ok, false)
})