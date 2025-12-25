/**
 * Theme Store
 * Theme mode state management (light/dark/system)
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ThemeMode } from '@types';

interface ThemeState {
  mode: ThemeMode;
  effectiveTheme: 'light' | 'dark';

  setMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const getEffectiveTheme = (mode: ThemeMode): 'light' | 'dark' => {
  if (mode === 'system') {
    return getSystemTheme();
  }
  return mode;
};

const applyTheme = (theme: 'light' | 'dark') => {
  const root = document.documentElement;
  if (theme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      effectiveTheme: getSystemTheme(),

      setMode: (mode: ThemeMode) => {
        const effectiveTheme = getEffectiveTheme(mode);
        applyTheme(effectiveTheme);
        set({ mode, effectiveTheme });
      },

      toggleTheme: () => {
        const current = get().effectiveTheme;
        const newMode = current === 'light' ? 'dark' : 'light';
        get().setMode(newMode);
      },
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Apply theme on hydration
          const effectiveTheme = getEffectiveTheme(state.mode);
          applyTheme(effectiveTheme);
          state.effectiveTheme = effectiveTheme;
        }
      },
    }
  )
);

// Listen for system theme changes
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const store = useThemeStore.getState();
    if (store.mode === 'system') {
      const effectiveTheme = e.matches ? 'dark' : 'light';
      applyTheme(effectiveTheme);
      useThemeStore.setState({ effectiveTheme });
    }
  });
}
