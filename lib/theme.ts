export type Theme = 'light' | 'dark' | 'system';

export function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'dark';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function getEffectiveTheme(stored: Theme): 'light' | 'dark' {
  if (stored === 'system') return getSystemTheme();
  return stored;
}

export function saveThemePreference(theme: Theme) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('genlens-theme', theme);
  }
}

export function loadThemePreference(): Theme {
  if (typeof window === 'undefined') return 'system';
  return (localStorage.getItem('genlens-theme') as Theme) || 'system';
}
