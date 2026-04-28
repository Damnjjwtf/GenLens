/**
 * app/index/archive/page.tsx
 *
 * Public Index archive redirect.
 * Temp: redirects to /index/[latest-date]
 */

import { redirect } from 'next/navigation'

export default function IndexArchivePage() {
  redirect('/index')
}
