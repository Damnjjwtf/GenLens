import type { Metadata } from 'next';
import { IBM_Plex_Mono, Lora, Playfair_Display } from 'next/font/google';
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
  title: 'GenLens',
  description: 'Daily intelligence for creative technologists working in AI-accelerated visual production.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${plexMono.variable} ${lora.variable} ${playfair.variable}`}>
      <body>{children}</body>
    </html>
  );
}
