import { auth, signOut } from '@/auth';
import Link from 'next/link';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Ticker } from '@/components/Ticker';
import { MainFeed } from '@/components/MainFeed';
import { Sidebar } from '@/components/Sidebar';

export default async function Dashboard() {
  const session = await auth();

  return (
    <main className="min-h-screen bg-[var(--bg)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--bg)]">
        <div className="px-6 py-6 max-w-7xl mx-auto flex items-baseline justify-between">
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
            <form action={async () => { 'use server'; await signOut({ redirectTo: '/' }); }}>
              <button type="submit" className="hover:text-[var(--red)]">Sign out</button>
            </form>
          </nav>
        </div>
      </header>

      {/* Live Ticker */}
      <Ticker />

      {/* Main content */}
      <div className="px-6 py-8 max-w-7xl mx-auto">
        <div className="flex gap-6">
          <MainFeed defaultVertical="product_photography" />
          <Sidebar />
        </div>
      </div>
    </main>
  );
}
