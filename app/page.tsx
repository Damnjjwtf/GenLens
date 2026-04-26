import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import Landing from '@/components/Landing';
import Dashboard from './dashboard';

export default async function Home() {
  const session = await auth();

  if (session?.user?.id) {
    return <Dashboard />;
  }

  return <Landing />;
}
