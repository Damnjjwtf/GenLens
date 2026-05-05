'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';

export function SignInForm() {
  const params = useSearchParams();
  const next = params.get('next') ?? '/';

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitEmail(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signIn('resend', { email, redirectTo: next });
    } catch {
      setError('Could not send magic link. Try again.');
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={submitEmail} className="flex gap-2">
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
          disabled={loading || !email}
          className="bg-[var(--accent)] text-[var(--bg)] px-4 py-2 font-mono text-sm uppercase disabled:opacity-50"
        >
          {loading ? '...' : 'Sign in'}
        </button>
      </form>

      <div className="flex items-center gap-3 text-[10px] uppercase tracking-widest text-[var(--text3)] font-mono">
        <div className="flex-1 border-t border-[var(--border)]" />
        <span>or</span>
        <div className="flex-1 border-t border-[var(--border)]" />
      </div>

      <button
        type="button"
        onClick={() => signIn('github', { redirectTo: next })}
        className="w-full flex items-center justify-center gap-2 border border-[var(--border2)] bg-[var(--bg)] text-[var(--text)] px-4 py-2 font-mono text-sm uppercase hover:border-[var(--accent)]"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
          <path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2.1c-3.3.7-4-1.6-4-1.6-.5-1.4-1.3-1.7-1.3-1.7-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1.1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3-5.5-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.7 1.7.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .3"/>
        </svg>
        Continue with GitHub
      </button>

      {error && <p className="text-xs text-[var(--red)]">{error}</p>}
    </div>
  );
}
