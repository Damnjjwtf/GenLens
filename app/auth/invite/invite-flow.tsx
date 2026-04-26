'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';

export default function InviteFlow() {
  const params = useSearchParams();
  const next = params.get('next') ?? '/';

  const [step, setStep] = useState<'invite' | 'email'>('invite');
  const [code, setCode] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submitInvite(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch('/api/invite', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const json = await res.json();
      if (!res.ok || !json.ok) {
        setError(json.error ?? 'Invalid invite');
        return;
      }
      setStep('email');
    } catch {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  }

  async function submitEmail(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signIn('resend', { email, redirectTo: next });
    } catch {
      setError('Could not send magic link');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-md border border-[var(--border)] bg-[var(--bg2)] p-8">
        <div className="mb-8">
          <h1 className="font-serif text-3xl text-[var(--text)] mb-1">GenLens</h1>
          <p className="text-xs text-[var(--text2)] uppercase tracking-widest">
            Daily intelligence for creative technologists
          </p>
        </div>

        {step === 'invite' && (
          <form onSubmit={submitInvite} className="space-y-4">
            <label className="block text-xs text-[var(--text2)] uppercase tracking-widest">
              Invite code
            </label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              autoFocus
              required
              className="w-full bg-[var(--bg)] border border-[var(--border2)] px-3 py-2 font-mono text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
              placeholder="GL-XXXX-XXXX"
            />
            {error && <p className="text-xs text-[var(--red)]">{error}</p>}
            <button
              type="submit"
              disabled={loading || !code}
              className="w-full bg-[var(--accent)] text-[var(--bg)] py-2 font-mono text-sm uppercase tracking-widest disabled:opacity-50"
            >
              {loading ? 'Verifying…' : 'Continue'}
            </button>
          </form>
        )}

        {step === 'email' && (
          <form onSubmit={submitEmail} className="space-y-4">
            <p className="text-sm text-[var(--text)]">
              Invite accepted. Enter your email for a magic link.
            </p>
            <label className="block text-xs text-[var(--text2)] uppercase tracking-widest">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
              required
              className="w-full bg-[var(--bg)] border border-[var(--border2)] px-3 py-2 font-mono text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
              placeholder="you@studio.com"
            />
            {error && <p className="text-xs text-[var(--red)]">{error}</p>}
            <button
              type="submit"
              disabled={loading || !email}
              className="w-full bg-[var(--accent)] text-[var(--bg)] py-2 font-mono text-sm uppercase tracking-widest disabled:opacity-50"
            >
              {loading ? 'Sending…' : 'Send magic link'}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
