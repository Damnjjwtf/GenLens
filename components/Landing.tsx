/**
 * components/Landing.tsx
 *
 * Server-rendered marketing homepage that doubles as a live dashboard.
 * Pulls the latest published snapshot per vertical, renders a top
 * movers ticker and three "market index" cards (GLI-PP / FM / DH),
 * SportsBizNow-influenced. Single conversion point: the sign-in form.
 */

import { neon } from '@neondatabase/serverless';
import { ThemeToggle } from './ThemeToggle';
import { SignInForm } from './SignInForm';
import { VERTICALS, VERTICAL_LABELS, type Vertical } from '@/lib/constants';

export const dynamic = 'force-dynamic';

const sql = neon(process.env.DATABASE_URL!);

const VERTICAL_SLUG: Record<Vertical, string> = {
  product_photography: 'product-photography',
  filmmaking: 'filmmaking',
  digital_humans: 'digital-humans',
};

const VERTICAL_TICKER_SYMBOL: Record<Vertical, string> = {
  product_photography: 'GLI-PP',
  filmmaking: 'GLI-FM',
  digital_humans: 'GLI-DH',
};

const VERTICAL_ACCENT_VAR: Record<Vertical, string> = {
  product_photography: 'var(--accent)',
  filmmaking: 'var(--accent2)',
  digital_humans: 'var(--purple)',
};

type Snapshot = {
  vertical: Vertical;
  week_start_date: string;
  headline: string | null;
  lede: string | null;
  top_tools: { tool_slug: string; rank: number; score: number; score_delta: number | null }[] | null;
  biggest_movers_up: { tool_slug: string; score: number; delta: number; prev_score: number }[] | null;
  biggest_movers_down: { tool_slug: string; score: number; delta: number; prev_score: number }[] | null;
  published_at: string | null;
  issue: number;
};

async function loadSnapshots(): Promise<Map<Vertical, Snapshot>> {
  const rows = await sql`
    WITH latest AS (
      SELECT DISTINCT ON (vertical) *
      FROM index_snapshots
      WHERE status = 'published'
      ORDER BY vertical, week_start_date DESC
    )
    SELECT l.*,
      (SELECT COUNT(*)::int FROM index_snapshots
        WHERE vertical = l.vertical AND status = 'published'
          AND week_start_date <= l.week_start_date) AS issue
    FROM latest l
  `;
  const map = new Map<Vertical, Snapshot>();
  for (const r of rows) {
    map.set(r.vertical as Vertical, r as unknown as Snapshot);
  }
  return map;
}

async function loadToolNames(slugs: string[]): Promise<Map<string, string>> {
  if (slugs.length === 0) return new Map();
  const rows = (await sql`
    SELECT slug, canonical_name FROM tools WHERE slug = ANY(${slugs})
  `) as { slug: string; canonical_name: string }[];
  return new Map(rows.map((r) => [r.slug, r.canonical_name]));
}

export default async function Landing() {
  const snapshots = await loadSnapshots();

  // Collect all tool slugs needed for ticker + cards
  const allSlugs = new Set<string>();
  for (const snap of Array.from(snapshots.values())) {
    snap.top_tools?.forEach(t => allSlugs.add(t.tool_slug));
    snap.biggest_movers_up?.forEach(t => allSlugs.add(t.tool_slug));
    snap.biggest_movers_down?.forEach(t => allSlugs.add(t.tool_slug));
  }
  const toolNames = await loadToolNames(Array.from(allSlugs));
  const name = (slug: string) => toolNames.get(slug) || slug;

  // Combined ticker, biggest movers across all verticals, sorted by |delta|
  const tickerItems: { slug: string; delta: number; vertical: Vertical }[] = [];
  for (const [vertical, snap] of Array.from(snapshots.entries())) {
    snap.biggest_movers_up?.forEach(t => tickerItems.push({ slug: t.tool_slug, delta: t.delta, vertical }));
    snap.biggest_movers_down?.forEach(t => tickerItems.push({ slug: t.tool_slug, delta: t.delta, vertical }));
  }
  tickerItems.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));

  return (
    <main className="min-h-screen">
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes home-ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
      ` }} />

      {/* Nav */}
      <div className="max-w-5xl mx-auto px-6">
        <nav className="flex items-center justify-between py-6 border-b border-[var(--border)]">
          <div>
            <h1 className="font-display text-4xl text-[var(--text)] leading-none">GenLens</h1>
            <p className="text-xs text-[var(--text2)] uppercase tracking-widest mt-1">Intelligence for creatives</p>
          </div>
          <div className="flex items-center gap-5">
            <ThemeToggle />
            <a
              href="#sign-in"
              className="text-xs uppercase tracking-widest text-[var(--accent)] hover:text-[var(--accent2)]"
            >
              Sign in →
            </a>
          </div>
        </nav>
      </div>

      {/* Movers ticker — full bleed */}
      {tickerItems.length > 0 && (
        <div
          className="border-y border-[var(--border)] bg-[var(--bg2)] overflow-hidden whitespace-nowrap py-2"
          aria-label="Biggest score movers across all indices"
        >
          <div
            className="inline-block font-mono text-[10px] tracking-wide"
            style={{ animation: 'home-ticker 90s linear infinite' }}
          >
            {tickerItems.concat(tickerItems).map((t, i) => (
              <span key={i} className="text-[var(--text2)]">
                <span className="text-[var(--text)] font-medium">{name(t.slug).toUpperCase()}</span>{' '}
                <span style={{ color: t.delta >= 0 ? 'var(--accent)' : 'var(--red)' }}>
                  {t.delta >= 0 ? '+' : ''}{t.delta}
                </span>
                <span className="mx-3" style={{ color: VERTICAL_ACCENT_VAR[t.vertical] }}>·</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="max-w-5xl mx-auto px-6">
        {/* Hero */}
        <section className="py-16">
          <div className="font-mono text-xs uppercase tracking-widest text-[var(--text3)] mb-3">
            Issue · {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
          </div>
          <h2 className="font-display text-5xl sm:text-6xl text-[var(--text)] mb-4 leading-tight">
            Daily intelligence for<br />Creative Technologists
          </h2>
          <p className="text-lg text-[var(--text2)] max-w-2xl font-serif">
            What changed today in product photography, filmmaking, and digital humans. Citable benchmarks. Score per tool. Weekly Index per vertical.
          </p>
        </section>

        {/* Three market index cards */}
        <section className="mb-16">
          <div className="flex items-baseline justify-between mb-6 pb-3 border-b border-[var(--border)]">
            <h3 className="font-mono text-xs uppercase tracking-widest text-[var(--text)]">This week&apos;s Indices</h3>
            <span className="font-mono text-[10px] uppercase tracking-widest text-[var(--text3)]">Recompute · weekly</span>
          </div>
          <div className="grid sm:grid-cols-3 gap-4">
            {VERTICALS.map(v => {
              const snap = snapshots.get(v);
              const accent = VERTICAL_ACCENT_VAR[v];
              const slug = VERTICAL_SLUG[v];
              const symbol = VERTICAL_TICKER_SYMBOL[v];
              const label = VERTICAL_LABELS[v];

              if (!snap) {
                return (
                  <div key={v} className="border border-[var(--border)] p-5 opacity-60" style={{ borderTop: `3px solid ${accent}` }}>
                    <div className="flex items-baseline justify-between mb-2">
                      <span className="font-mono text-[11px] tracking-widest" style={{ color: accent }}>{symbol}</span>
                      <span className="font-mono text-[10px] uppercase text-[var(--text3)]">Pending</span>
                    </div>
                    <h4 className="font-serif text-base text-[var(--text)] mb-2">{label}</h4>
                    <p className="font-mono text-[11px] text-[var(--text3)]">First Issue arrives next Monday.</p>
                  </div>
                );
              }

              const top = snap.top_tools?.[0];
              const mover = snap.biggest_movers_up?.[0] || snap.biggest_movers_down?.[0];

              return (
                <a
                  key={v}
                  href={`/markets/${slug}`}
                  className="block border border-[var(--border)] hover:bg-[var(--bg2)] transition p-5"
                  style={{ borderTop: `3px solid ${accent}` }}
                >
                  <div className="flex items-baseline justify-between mb-3">
                    <span className="font-mono text-[11px] tracking-widest" style={{ color: accent }}>{symbol}</span>
                    <span className="font-mono text-[10px] uppercase text-[var(--text3)]">Issue #{snap.issue}</span>
                  </div>
                  <h4 className="font-serif text-base text-[var(--text)] mb-3">{label}</h4>

                  {top && (
                    <div className="mb-3 pb-3 border-b border-[var(--border)]">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-[var(--text3)] mb-1">No. 1</div>
                      <div className="flex items-baseline justify-between">
                        <span className="font-serif text-sm text-[var(--text)]">{name(top.tool_slug)}</span>
                        <span className="font-mono text-sm text-[var(--text)]">{top.score}</span>
                      </div>
                    </div>
                  )}

                  {mover && (
                    <div className="mb-3">
                      <div className="font-mono text-[10px] uppercase tracking-widest text-[var(--text3)] mb-1">Biggest mover</div>
                      <div className="flex items-baseline justify-between">
                        <span className="font-serif text-sm text-[var(--text)]">{name(mover.tool_slug)}</span>
                        <span
                          className="font-mono text-sm"
                          style={{ color: mover.delta >= 0 ? 'var(--accent)' : 'var(--red)' }}
                        >
                          {mover.delta >= 0 ? '+' : ''}{mover.delta}
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="font-mono text-[10px] uppercase tracking-widest" style={{ color: accent }}>
                    View Index →
                  </div>
                </a>
              );
            })}
          </div>
        </section>

        {/* Inline lede from latest snapshot — feels editorial */}
        {(() => {
          const allHeadlines = Array.from(snapshots.values()).filter(s => s.headline);
          if (allHeadlines.length === 0) return null;
          const featured = allHeadlines[0];
          return (
            <section className="mb-16 pb-16 border-b border-[var(--border)]">
              <div
                className="font-mono text-[10px] uppercase tracking-widest mb-2"
                style={{ color: VERTICAL_ACCENT_VAR[featured.vertical] }}
              >
                {VERTICAL_TICKER_SYMBOL[featured.vertical]} · This week
              </div>
              <h3 className="font-display text-3xl text-[var(--text)] mb-3 leading-tight">{featured.headline}</h3>
              {featured.lede && (
                <p className="font-serif text-base text-[var(--text2)] max-w-3xl">{featured.lede}</p>
              )}
              <a
                href={`/markets/${VERTICAL_SLUG[featured.vertical]}`}
                className="inline-block mt-4 font-mono text-xs uppercase tracking-widest"
                style={{ color: VERTICAL_ACCENT_VAR[featured.vertical] }}
              >
                Read full Index →
              </a>
            </section>
          );
        })()}

        {/* Sign in — single conversion point */}
        <section
          id="sign-in"
          className="border border-[var(--border)] bg-[var(--bg2)] p-8 mb-16 max-w-2xl scroll-mt-8"
          style={{ borderTop: '3px solid var(--accent)' }}
        >
          <div className="font-mono text-[10px] uppercase tracking-widest text-[var(--accent)] mb-3">Sign in</div>
          <h3 className="font-serif text-xl text-[var(--text)] mb-2">Get the weekly briefing</h3>
          <p className="text-sm text-[var(--text2)] mb-6">
            Top movers, new entries, exits. One email Monday morning. Sign in to unlock your dashboard and the full Index.
          </p>
          <SignInForm />
        </section>

        {/* Footer */}
        <footer className="text-xs text-[var(--text3)] pb-8 border-t border-[var(--border)] pt-8 flex flex-wrap items-center justify-between gap-3">
          <p>GenLens — Intelligence for creative technologists. Phase 1 beta.</p>
          <p>
            <a href="https://github.com/Damnjjwtf/GenLens" className="hover:text-[var(--text2)]">GitHub</a>
            {' · '}
            <a href="mailto:brief@genlens.local" className="hover:text-[var(--text2)]">Feedback</a>
          </p>
        </footer>
      </div>
    </main>
  );
}
