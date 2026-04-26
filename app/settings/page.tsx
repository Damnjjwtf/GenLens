import { auth } from '@/auth';
import { getUserPreferences } from '@/lib/db';
import { redirect } from 'next/navigation';
import SettingsForm from './settings-form';

export default async function SettingsPage() {
  const session = await auth();
  if (!session?.user?.id) redirect('/auth/invite');

  const preferences = await getUserPreferences(session.user.id);

  return (
    <main className="min-h-screen px-6 py-8 max-w-3xl mx-auto">
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
