'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ThemeToggle } from './ThemeToggle';

export default function Landing() {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function subscribe(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error('Failed to subscribe');
      setSubscribed(true);
      setEmail('');
    } catch {
      setError('Could not subscribe. Try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-6 py-12 max-w-5xl mx-auto">
      {/* Nav */}
      <nav className="flex items-center justify-between mb-16 pb-6 border-b border-[var(--border)]">
        <div>
          <h1 className="font-serif text-2xl text-[var(--text)]">GenLens</h1>
          <p className="text-xs text-[var(--text2)] uppercase tracking-widest">Intelligence for creatives</p>
        </div>
        <div className="flex items-center gap-5">
          <ThemeToggle />
          <Link
            href="/auth/invite"
            className="text-xs uppercase tracking-widest text-[var(--accent)] hover:text-[var(--accent2)]"
          >
            Join beta →
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="mb-20">
        <h2 className="font-display text-5xl sm:text-6xl text-[var(--text)] mb-4 leading-tight">
          Daily intelligence for<br />Creative Technologists
        </h2>
        <p className="text-lg text-[var(--text2)] max-w-2xl mb-8 font-serif">
          Stay ahead of what's changing in AI-accelerated visual production. Product photography, filmmaking, digital humans — all in one feed.
        </p>
        <div className="flex gap-4 flex-wrap">
          <Link
            href="/auth/invite"
            className="bg-[var(--accent)] text-[var(--bg)] px-6 py-3 font-mono text-sm uppercase tracking-widest hover:bg-[var(--accent2)]"
          >
            Get early access
          </Link>
          <a
            href="#features"
            className="border border-[var(--border)] px-6 py-3 font-mono text-sm uppercase tracking-widest hover:bg-[var(--bg2)]"
          >
            Learn more
          </a>
        </div>
      </section>

      {/* Email signup */}
      <section className="border border-[var(--border)] bg-[var(--bg2)] p-8 mb-20 max-w-2xl">
        <h3 className="font-serif text-xl text-[var(--text)] mb-2">Early access</h3>
        <p className="text-sm text-[var(--text2)] mb-6">
          Join the waitlist. We'll send you an invite code and weekly intelligence briefings.
        </p>
        {subscribed ? (
          <p className="text-sm text-[var(--accent)]">✓ Thanks. Check your email.</p>
        ) : (
          <form onSubmit={subscribe} className="flex gap-2">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@studio.com"
              required
              className="flex-1 bg-[var(--bg)] border border-[var(--border2)] px-3 py-2 text-[var(--text)] placeholder-[var(--text3)] focus:outline-none focus:border-[var(--accent)]"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-[var(--accent)] text-[var(--bg)] px-4 py-2 font-mono text-sm uppercase disabled:opacity-50"
            >
              {loading ? '...' : 'Join'}
            </button>
          </form>
        )}
        {error && <p className="text-xs text-[var(--red)] mt-2">{error}</p>}
      </section>

      {/* Features */}
      <section id="features" className="mb-20">
        <h3 className="font-serif text-2xl text-[var(--text)] mb-8">What you get</h3>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="border border-[var(--border)] p-6">
            <div className="text-[var(--accent)] font-mono text-xs uppercase tracking-widest mb-2">Dimension 1</div>
            <h4 className="font-serif text-lg text-[var(--text)] mb-2">Workflow Stage Signals</h4>
            <p className="text-sm text-[var(--text2)]">
              What changed in rendering, voice generation, animation, or your bottleneck. Real-time updates from 130+ sources.
            </p>
          </div>
          <div className="border border-[var(--border)] p-6">
            <div className="text-[var(--accent2)] font-mono text-xs uppercase tracking-widest mb-2">Dimension 3</div>
            <h4 className="font-serif text-lg text-[var(--text)] mb-2">Competitive Intelligence</h4>
            <p className="text-sm text-[var(--text2)]">
              What other creatives are shipping. Trending projects, commercial success, tool stacks winning.
            </p>
          </div>
          <div className="border border-[var(--border)] p-6">
            <div className="text-[var(--blue)] font-mono text-xs uppercase tracking-widest mb-2">Dimension 4</div>
            <h4 className="font-serif text-lg text-[var(--text)] mb-2">Workflow Templates</h4>
            <p className="text-sm text-[var(--text2)]">
              Fastest proven methods from real creators. Time breakdown, cost, quality. Adopt workflows that work.
            </p>
          </div>
          <div className="border border-[var(--border)] p-6">
            <div className="text-[var(--purple)] font-mono text-xs uppercase tracking-widest mb-2">Dimension 5</div>
            <h4 className="font-serif text-lg text-[var(--text)] mb-2">Cost & Time Delta</h4>
            <p className="text-sm text-[var(--text2)]">
              Quantified savings per tool release. How many hours faster? How much cheaper? We do the math.
            </p>
          </div>
          <div className="border border-[var(--border)] p-6">
            <div className="text-[var(--red)] font-mono text-xs uppercase tracking-widest mb-2">Dimension 6</div>
            <h4 className="font-serif text-lg text-[var(--text)] mb-2">Legal & Ethical</h4>
            <p className="text-sm text-[var(--text2)]">
              SAG-AFTRA rules, copyright updates, deepfake legislation. Stay compliant, stay safe.
            </p>
          </div>
          <div className="border border-[var(--border)] p-6">
            <div className="text-[var(--accent2)] font-mono text-xs uppercase tracking-widest mb-2">Dimension 7</div>
            <h4 className="font-serif text-lg text-[var(--text)] mb-2">Talent + Hiring</h4>
            <p className="text-sm text-[var(--text2)]">
              Market rates, skills in demand, salary trends. Know your value. See what's hiring and at what rates.
            </p>
          </div>
        </div>
      </section>

      {/* Three verticals */}
      <section className="mb-20">
        <h3 className="font-serif text-2xl text-[var(--text)] mb-8">For three verticals</h3>
        <div className="grid sm:grid-cols-3 gap-4">
          <div className="border-l-4 border-[var(--accent)] pl-4">
            <h4 className="font-serif text-lg text-[var(--text)]">Product Photography</h4>
            <p className="text-sm text-[var(--text2)] mt-2">Hard goods, soft goods, presale. KeyShot, Claid, presale workflows.</p>
          </div>
          <div className="border-l-4 border-[var(--accent2)] pl-4">
            <h4 className="font-serif text-lg text-[var(--text)]">Filmmaking</h4>
            <p className="text-sm text-[var(--text2)] mt-2">VFX, color grading, sound design. Runway, DaVinci Resolve, motion capture.</p>
          </div>
          <div className="border-l-4 border-[var(--purple)] pl-4">
            <h4 className="font-serif text-lg text-[var(--text)]">Digital Humans</h4>
            <p className="text-sm text-[var(--text2)] mt-2">Synthetic actors, voice, animation. D-ID, ElevenLabs, HeyGen.</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border border-[var(--border)] bg-[var(--bg2)] p-12 text-center mb-20">
        <h3 className="font-serif text-3xl text-[var(--text)] mb-3">Ready?</h3>
        <p className="text-[var(--text2)] mb-6">Get your invite code and join the beta.</p>
        <Link
          href="/auth/invite"
          className="inline-block bg-[var(--accent)] text-[var(--bg)] px-8 py-3 font-mono uppercase tracking-widest hover:bg-[var(--accent2)]"
        >
          Join beta
        </Link>
      </section>

      {/* Footer */}
      <footer className="text-xs text-[var(--text3)] text-center pb-8 border-t border-[var(--border)] pt-8">
        <p>GenLens — Intelligence for creative technologists. Phase 1 beta.</p>
        <p className="mt-2">
          <a href="https://github.com/Damnjjwtf/GenLens-" className="hover:text-[var(--text2)]">GitHub</a>
          {' '} · {' '}
          <a href="mailto:brief@genlens.local" className="hover:text-[var(--text2)]">Feedback</a>
        </p>
      </footer>
    </main>
  );
}
