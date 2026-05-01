import { auth } from '@/auth';
import { getUserPreferences } from '@/lib/db';
import { redirect } from 'next/navigation';
import Link from 'next/link';
import SettingsForm from './settings-form';

export default async function SettingsPage() {
  const session = await auth();
  if (!session?.user?.id) redirect('/?next=/settings#sign-in');

  const preferences = await getUserPreferences(session.user.id);

  return (
    <main className="min-h-screen px-6 py-8 max-w-3xl mx-auto">
      <Link
        href="/"
        className="inline-block font-mono text-[10px] uppercase tracking-widest text-[var(--text2)] hover:text-[var(--accent)] mb-6"
      >
        ← Home
      </Link>
      <header className="border-b border-[var(--border)] pb-4 mb-8">
        <h1 className="font-serif text-3xl text-[var(--text)]">Settings</h1>
        <p className="text-xs text-[var(--text2)] uppercase tracking-widest mt-1">
          {session.user.email}
        </p>
      </header>
      <SettingsForm initial={preferences} />
    </main>
  );
}
