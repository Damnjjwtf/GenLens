import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        bg2: 'var(--bg2)',
        bg3: 'var(--bg3)',
        border1: 'var(--border)',
        border2: 'var(--border2)',
        text1: 'var(--text)',
        text2: 'var(--text2)',
        text3: 'var(--text3)',
        accent: 'var(--accent)',
        accent2: 'var(--accent2)',
        red: 'var(--red)',
        blue: 'var(--blue)',
        purple: 'var(--purple)',
      },
      fontFamily: {
        mono: ['var(--font-mono)', 'IBM Plex Mono', 'ui-monospace', 'monospace'],
        serif: ['var(--font-serif)', 'Lora', 'Georgia', 'serif'],
        display: ['var(--font-display)', 'Playfair Display', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};
export default config;
