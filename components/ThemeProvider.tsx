'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { loadThemePreference, saveThemePreference, getEffectiveTheme, type Theme } from '@/lib/theme';

type ThemeContextType = {
  theme: Theme;
  effective: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
};

const ThemeContext = createContext<ThemeContextType | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('system');
  const [effective, setEffective] = useState<'light' | 'dark'>('dark');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = loadThemePreference();
    setThemeState(stored);
    const eff = getEffectiveTheme(stored);
    setEffective(eff);
    document.documentElement.setAttribute('data-theme', eff);
    setMounted(true);
  }, []);

  function setTheme(newTheme: Theme) {
    setThemeState(newTheme);
    saveThemePreference(newTheme);
    const eff = getEffectiveTheme(newTheme);
    setEffective(eff);
    document.documentElement.setAttribute('data-theme', eff);
  }

  if (!mounted) return <>{children}</>;

  return (
    <ThemeContext.Provider value={{ theme, effective, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider');
  return ctx;
}
