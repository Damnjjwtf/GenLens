import { auth, signOut } from '@/auth';
import Link from 'next/link';
import { ThemeToggle } from '@/components/ThemeToggle';

export default async function Dashboard() {
  const session = await auth();

  return (
    <main className="min-h-screen px-6 py-8 max-w-6xl mx-auto">
      <header className="flex items-baseline justify-between border-b border-[var(--border)] pb-4 mb-8">
        <div>
          <h1 className="font-serif text-3xl text-[var(--text)]">GenLens</h1>
          <p className="text-xs text-[var(--text2)] uppercase tracking-widest mt-1">
            Daily intelligence · creative technologists
          </p>
        </div>
        <nav className="flex items-center gap-6 text-xs uppercase tracking-widest text-[var(--text2)]">
          <Link href="/" className="text-[var(--accent)]">Feed</Link>
          <Link href="/templates" className="hover:text-[var(--text)]">Templates</Link>
          <Link href="/leaderboard" className="hover:text-[var(--text)]">Leaderboard</Link>
          <Link href="/settings" className="hover:text-[var(--text)]">Settings</Link>
          <span className="text-[var(--text3)]">·</span>
          <span className="text-[var(--text3)]">{session?.user?.email}</span>
          <ThemeToggle />
          <form action={async () => { 'use server'; await signOut({ redirectTo: '/auth/invite' }); }}>
            <button type="submit" className="hover:text-[var(--red)]">Sign out</button>
          </form>
        </nav>
      </header>

      <section className="border border-[var(--border)] bg-[var(--bg2)] p-6">
        <div className="text-xs text-[var(--text2)] uppercase tracking-widest mb-2">Status</div>
        <p className="text-[var(--text)] mb-1">Phase 1 foundation is live.</p>
        <p className="text-xs text-[var(--text3)]">
          Scrapers, synthesis, signal feed, and email delivery come online in Phase 2 onward.
        </p>
      </section>
    </main>
  );
}
