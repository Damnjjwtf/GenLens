import ledgerSchema from '@/agents/genny/data/genlens_signal_record.schema.json'

type Rule = {
  $ref?: string
  type?: string | string[]
  const?: unknown
  enum?: unknown[]
  required?: string[]
  properties?: Record<string, Rule>
  additionalProperties?: boolean | Rule
  items?: Rule
  minLength?: number
  minItems?: number
  maxItems?: number
  uniqueItems?: boolean
  pattern?: string
  minimum?: number
  format?: string
}

export type LedgerSignal = {
  id: string
  status: 'published' | 'qualified' | 'rejected'
  lenses: Array<'genny' | 'marti'>
  verticals: string[]
  title: string
  summary: string
  canonical_url: string
  change: string
  mechanism: string | null
  use_case: string | null
  impact: string | null
  recommended_action: string | null
  confidence: string
  evidence: Array<{ url: string; [key: string]: unknown }>
  first_observed_at: string
  last_observed_at: string
  observation_count: number
  [key: string]: unknown
}

export type LedgerEnvelope = {
  schema_version: '1.0.0'
  actor_id: 'genny' | 'marti' | 'unified'
  event_id: string
  idempotency_key: string
  record: LedgerSignal
}

type Result = { ok: true; data: LedgerEnvelope } | { ok: false; errors: string[] }
const defs = (ledgerSchema as unknown as { $defs: Record<string, Rule> }).$defs
const supported = new Set([
  '$ref', 'type', 'const', 'enum', 'required', 'properties', 'additionalProperties',
  'items', 'minLength', 'minItems', 'maxItems', 'uniqueItems', 'pattern', 'minimum', 'format',
])

function obj(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function matches(t: string, value: unknown): boolean {
  if (t === 'null') return value === null
  if (t === 'integer') return typeof value === 'number' && Number.isInteger(value)
  if (t === 'number') return typeof value === 'number' && Number.isFinite(value)
  if (t === 'object') return obj(value)
  if (t === 'array') return Array.isArray(value)
  return typeof value === t
}

function check(rule: Rule, value: unknown, at: string, errors: string[]): void {
  if (errors.length >= 12) return
  if (Object.keys(rule).some((key) => !supported.has(key))) {
    errors.push(at + ': unsupported contract constraint')
    return
  }
  if (rule.$ref) {
    const name = rule.$ref.startsWith('#/$defs/') ? rule.$ref.slice(8) : ''
    if (!name || !defs[name]) errors.push(at + ': unknown contract reference')
    else check(defs[name], value, at, errors)
    return
  }
  if (rule.type) {
    const types = Array.isArray(rule.type) ? rule.type : [rule.type]
    if (!types.some((type) => matches(type, value))) {
      errors.push(at + ': incorrect type')
      return
    }
  }
  if (Object.prototype.hasOwnProperty.call(rule, 'const') && value !== rule.const) errors.push(at + ': invalid constant')
  if (rule.enum && !rule.enum.includes(value)) errors.push(at + ': invalid option')
  if (typeof value === 'number' && rule.minimum !== undefined && value < rule.minimum) errors.push(at + ': below minimum')
  if (typeof value === 'string') {
    if (rule.minLength !== undefined && value.length < rule.minLength) errors.push(at + ': too short')
    if (rule.pattern && !new RegExp(rule.pattern).test(value)) errors.push(at + ': invalid pattern')
    if (rule.format === 'date-time' &&
        (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)
         || !Number.isFinite(Date.parse(value)))) errors.push(at + ': invalid timestamp')
    if (rule.format && rule.format !== 'date-time') errors.push(at + ': unknown format')
  }
  if (Array.isArray(value)) {
    if (rule.minItems !== undefined && value.length < rule.minItems) errors.push(at + ': too few items')
    if (rule.maxItems !== undefined && value.length > rule.maxItems) errors.push(at + ': too many items')
    if (rule.uniqueItems && new Set(value.map((part) => JSON.stringify(part))).size !== value.length) errors.push(at + ': duplicates')
    if (rule.items) value.forEach((part, i) => check(rule.items!, part, at + '[' + i + ']', errors))
  }
  if (obj(value)) {
    for (const name of rule.required ?? []) if (!(name in value)) errors.push(at + '.' + name + ': missing')
    for (const [key, part] of Object.entries(value)) {
      const nested = rule.properties?.[key]
      if (nested) check(nested, part, at + '.' + key, errors)
      else if (rule.additionalProperties === false) errors.push(at + '.' + key + ': unknown')
      else if (obj(rule.additionalProperties)) check(rule.additionalProperties as Rule, part, at + '.' + key, errors)
    }
  }
}

function webUrl(value: unknown): boolean {
  if (typeof value !== 'string') return false
  try {
    const parsed = new URL(value)
    return ['https:', 'http:'].includes(parsed.protocol) && Boolean(parsed.hostname)
  } catch {
    return false
  }
}

export function validateIngestEnvelope(input: unknown): Result {
  if (!obj(input)) return { ok: false, errors: ['Expected object'] }
  const errors: string[] = []
  for (const name of Object.keys(input)) {
    if (!['schema_version', 'actor_id', 'event_id', 'idempotency_key', 'record'].includes(name)) errors.push(name + ': unknown envelope field')
  }
  if (input.schema_version !== '1.0.0') errors.push('Incorrect contract version')
  if (!['genny', 'marti', 'unified'].includes(String(input.actor_id))) errors.push('Incorrect actor')
  if (typeof input.event_id !== 'string' || !/^evt_[a-f0-9]{24}$/.test(input.event_id)) errors.push('Incorrect event ID')
  if (input.idempotency_key !== input.event_id) errors.push('Idempotency key must match event ID')
  check(defs.signal, input.record, 'record', errors)
  if (obj(input.record)) {
    const r = input.record
    if (input.actor_id !== 'unified' && Array.isArray(r.lenses) && !r.lenses.includes(input.actor_id)) {
      errors.push('Actor is not a member of the signal lens')
    }
    if (r.status === 'published' &&
        (!Array.isArray(r.evidence) || !r.evidence.some((row) => obj(row) && webUrl(row.url)))) {
      errors.push('Published signal requires a source link')
    }
    if (r.status === 'rejected' && (r.recommended_action !== null || typeof r.rejection_reason !== 'string' || !r.rejection_reason)) {
      errors.push('Rejected signals cannot recommend action')
    }
    if (r.status !== 'rejected' && r.recommended_action === null) errors.push('Non-rejected signal requires action')
  }
  if (errors.length) return { ok: false, errors: errors.slice(0, 12) }
  return { ok: true, data: input as LedgerEnvelope }
}