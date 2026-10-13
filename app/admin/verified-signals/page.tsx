import { auth } from '@/auth'
import { pool } from '@/lib/db'
import { notFound, redirect } from 'next/navigation'
import Link from 'next/link'

export const dynamic = 'force-dynamic'

type Evidence = { url?: string; source_name?: string; published_at?: string | null }
type Signal = {
  signal_id: string
  actor_id: string
  status: 'published' | 'qualified' | 'rejected'
  lenses: string[]
  verticals: string[]
  title: string
  summary: string
  change: string
  mechanism: string | null
  use_case: string | null
  impact: string | null
  recommended_action: string | null
  confidence: string
  canonical_url: string
  evidence: Evidence[]
  last_observed_at: string
}

function safeSource(raw: unknown): string | null {
  if (typeof raw !== 'string') return null
  try {
    const url = new URL(raw)
    if (url.protocol === 'http:' || url.protocol === 'https:') return url.href
  } catch {
    return null
  }
  return null
}

function displayDate(value: string): string {
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return 'Date unverified'
  return date.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC',
  })
}

export default async function VerifiedSignalDesk() {
  const session = await auth()
  if (!session?.user?.id) redirect('/auth/invite')
  if (!pool) notFound()
  // A valid session is insufficient. Check the database role on every request.
  const userResult = await pool.query('SELECT role FROM users WHERE id = $1::uuid LIMIT 1', [session.user.id])
    .catch(() => null)
  const role = (userResult?.rows[0] as { role?: string } | undefined)?.role
  if (role !== 'admin') notFound()

  let signals: Signal[] = []
  let storeReady = true
  try {
    const result = await pool.query([
      'SELECT signal_id, actor_id, status, lenses, verticals, title,',
      'summary, change, mechanism, use_case, impact, recommended_action,',
      'confidence, canonical_url, evidence, last_observed_at',
      'FROM ledger_signals ORDER BY last_observed_at DESC LIMIT 50',
    ].join(' '))
    signals = result.rows as Signal[]
  } catch {
    storeReady = false
  }

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <header className="border-b border-[var(--border)]">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-6">
          <div>
            <Link href="/" className="font-serif text-2xl text-[var(--text)]">GenLens</Link>
            <div className="mt-1 text-xs uppercase tracking-widest text-[var(--text2)]">Signal to system.</div>
          </div>
          <div className="rounded border border-[var(--border2)] px-3 py-2 text-xs uppercase tracking-wide text-[var(--text2)]">
            Private intelligence desk
          </div>
        </div>
      </header>
      <div className="mx-auto max-w-6xl px-5 py-10">
        <p className="text-xs uppercase tracking-widest text-[var(--accent)]">Editorial preview</p>
        <h1 className="mt-3 font-serif text-4xl">Verified signal candidates</h1>
        <p className="mt-3 max-w-3xl leading-relaxed text-[var(--text2)]">
          Genny and Marti observations, with evidence, workflow implications, and proposed
          decisions. This is an internal review surface, not a public publication queue.
        </p>
        <div className="my-8 grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            { label: 'Recent records', value: signals.length },
            { label: 'Agent-selected', value: signals.filter((s) => s.status === 'published').length },
            { label: 'Qualified', value: signals.filter((s) => s.status === 'qualified').length },
            { label: 'Rejected', value: signals.filter((s) => s.status === 'rejected').length },
          ].map((stat) => (
            <div key={stat.label} className="rounded-lg border border-[var(--border)] bg-[var(--bg2)] p-4">
              <p className="text-2xl font-semibold">{stat.value}</p>
              <p className="mt-1 text-xs uppercase tracking-wide text-[var(--text2)]">{stat.label}</p>
            </div>
          ))}
        </div>
        {!storeReady && (
          <section className="rounded-lg border border-[var(--border2)] p-6">
            <h2 className="font-semibold">Verified ledger is not connected yet.</h2>
            <p className="mt-2 text-[var(--text2)]">
              Apply migration 009, configure the ingestion secret, and push an authorized
              Genny/Marti ledger. No sample data is substituted for verified records.
            </p>
          </section>
        )}
        {storeReady && signals.length === 0 && (
          <section className="rounded-lg border border-[var(--border2)] p-6 text-[var(--text2)]">
            No agent records ingested yet. This desk will populate after a validated ledger push.
            Public publication remains separately gated.
          </section>
        )}
        <div className="space-y-5">
          {signals.map((s) => {
            const evidence = Array.isArray(s.evidence) ? s.evidence : []
            const source = safeSource(s.canonical_url) ||
              evidence.map((e) => safeSource(e.url)).find((value) => Boolean(value))
            return (
              <article key={s.signal_id} className="rounded-xl border border-[var(--border)] bg-[var(--bg2)] p-6">
                <div className="mb-3 flex flex-wrap items-center gap-2 text-xs uppercase tracking-wide text-[var(--text2)]">
                  <span className="rounded bg-[var(--bg3)] px-2 py-1">{s.lenses.join(' + ')}</span>
                  <span className="rounded bg-[var(--bg3)] px-2 py-1">
                    {s.status === 'published' ? 'Agent-selected, not released' : s.status}
                  </span>
                  <span>{displayDate(s.last_observed_at)}</span>
                  <span>{s.confidence}</span>
                </div>
                <h2 className="font-serif text-2xl leading-snug">{s.title}</h2>
                <p className="mt-2 text-sm text-[var(--text2)]">{s.summary}</p>
                <div className="mt-6 grid gap-5 border-t border-[var(--border)] pt-5 md:grid-cols-3">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-[var(--accent)]">What changed</p>
                    <p className="mt-2 text-sm">{s.change}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-[var(--accent)]">Workflow implication</p>
                    <p className="mt-2 text-sm">{s.impact || s.mechanism || 'Review needed'}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-[var(--accent)]">Decision to consider</p>
                    <p className="mt-2 text-sm">
                      {s.recommended_action ? s.recommended_action.toUpperCase() : 'No action'}
                      {s.use_case ? ': ' + s.use_case : ''}
                    </p>
                  </div>
                </div>
                <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border)] pt-4 text-xs text-[var(--text2)]">
                  <span>{s.verticals.join(' · ')} · {s.signal_id}</span>
                  {source ? (
                    <a href={source} target="_blank" rel="noopener noreferrer" className="text-[var(--blue)]">
                      Open source evidence ↗
                    </a>
                  ) : <span>Evidence link unavailable</span>}
                </div>
              </article>
            )
          })}
        </div>
        <p className="mt-8 max-w-3xl text-xs leading-relaxed text-[var(--text3)]">
          An agent&apos;s published status means briefing selection, not independent
          human approval. Marti and unified outputs remain subject to promotion gates.
          This page never triggers public posts, campaigns, or spending.
        </p>
      </div>
    </main>
  )
}
