/**
 * app/markets/archive/page.tsx
 *
 * Public Index archive redirect.
 * Temp: redirects to /markets/[latest-date]
 */

import { redirect } from 'next/navigation'

export default function IndexArchivePage() {
  redirect('/markets')
}
