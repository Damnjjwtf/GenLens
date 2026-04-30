import type { Metadata } from 'next';
import { IBM_Plex_Mono, Lora, Playfair_Display } from 'next/font/google';
import { ThemeProvider } from '@/components/ThemeProvider';
import { organizationLD, websiteLD, SITE_URL, SITE_NAME } from '@/lib/schema/jsonld';
import './globals.css';

const plexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-mono',
});

const lora = Lora({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-serif',
});

const playfair = Playfair_Display({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-display',
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${SITE_NAME} — Daily intelligence for AI-accelerated creative production`,
    template: `%s — ${SITE_NAME}`,
  },
  description:
    'GenLens publishes the GenLens Score and the weekly GenLens Index — citable benchmarks for AI creative tools across product photography, filmmaking, and digital humans.',
  applicationName: SITE_NAME,
  keywords: [
    'GenLens',
    'GenLens Score',
    'GenLens Index',
    'AI creative tools',
    'AI video generation',
    'product photography',
    'filmmaking',
    'digital humans',
    'tool ranking',
    'weekly index',
  ],
  authors: [{ name: SITE_NAME, url: SITE_URL }],
  creator: SITE_NAME,
  publisher: SITE_NAME,
  alternates: { canonical: SITE_URL },
  openGraph: {
    type: 'website',
    siteName: SITE_NAME,
    url: SITE_URL,
    title: `${SITE_NAME} — Daily intelligence for AI-accelerated creative production`,
    description:
      'Citable benchmarks for AI creative tools. GenLens Score per tool. Weekly GenLens Index per vertical.',
  },
  twitter: {
    card: 'summary_large_image',
    title: SITE_NAME,
    description: 'Citable benchmarks for AI creative tools.',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, 'max-snippet': -1, 'max-image-preview': 'large' },
  },
};

export const viewport = 'width=device-width, initial-scale=1.0';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const siteJsonLd = [organizationLD(), websiteLD()];

  return (
    <html lang="en" className={`${plexMono.variable} ${lora.variable} ${playfair.variable}`}>
      <head>
        <link rel="alternate" type="text/markdown" title="llms.txt" href="/llms.txt" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(siteJsonLd) }}
        />
      </head>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
