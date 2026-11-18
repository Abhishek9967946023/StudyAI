/**
 * =============================================================================
 * StudyAI — Theme Management Hook
 * =============================================================================
 * Supports light / dark theme toggle, defaults to system preference,
 * persists choice in localStorage, and applies [data-theme="dark"] to <html>.
 * =============================================================================
 */

import { useState, useEffect } from 'react';

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('studyai_theme');
    if (saved) return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches 
      ? 'dark' 
      : 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('studyai_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return { theme, setTheme, toggleTheme, isDark: theme === 'dark' };
}
