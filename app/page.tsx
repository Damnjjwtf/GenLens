import type { Metadata } from 'next'
import { auth } from '@/auth'
import Landing from '@/components/Landing'
import Dashboard from './dashboard'

export const metadata: Metadata = {
  title: 'GenLens | Signal to system.',
  description:
    'Evidence-backed intelligence for creative technologists and go-to-market engineers. Understand what changed, why it matters, and what to test next.',
  openGraph: {
    title: 'GenLens | Signal to system.',
    description:
      'AI production and GTM intelligence for people building creative and growth systems.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'GenLens | Signal to system.',
    description: 'Know what changed. Know what to test.',
  },
}

export default async function Home() {
  const session = await auth()
  if (session?.user?.id) return <Dashboard />
  return <Landing />
}
