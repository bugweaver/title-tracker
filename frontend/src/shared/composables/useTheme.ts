import { ref, watch, onMounted } from 'vue';

export type ThemeName = 'light' | 'dark' | 'midnight' | 'system';

const STORAGE_KEY = 'theme-preference';
const THEMES: ThemeName[] = ['light', 'dark', 'midnight'];

// Global reactive theme state
const currentTheme = ref<ThemeName>('system');
const resolvedTheme = ref<Exclude<ThemeName, 'system'>>('light');

function getSystemTheme(): Exclude<ThemeName, 'system'> {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme: Exclude<ThemeName, 'system'>) {
  document.documentElement.setAttribute('data-theme', theme);
  resolvedTheme.value = theme;
}

function resolveTheme(theme: ThemeName): Exclude<ThemeName, 'system'> {
  return theme === 'system' ? getSystemTheme() : theme;
}

export function useTheme() {
  function setTheme(theme: ThemeName) {
    currentTheme.value = theme;
    localStorage.setItem(STORAGE_KEY, theme);
    applyTheme(resolveTheme(theme));
  }

  function toggleTheme() {
    const current = resolvedTheme.value;
    const currentIndex = THEMES.indexOf(current);
    const nextIndex = (currentIndex + 1) % THEMES.length;
    const nextTheme = THEMES[nextIndex];
    if (nextTheme) {
      setTheme(nextTheme);
    }
  }

  function initTheme() {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeName | null;
    const initial = stored && [...THEMES, 'system'].includes(stored) ? stored : 'system';
    currentTheme.value = initial;
    applyTheme(resolveTheme(initial));

    // Listen for system theme changes
    if (typeof window !== 'undefined') {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (currentTheme.value === 'system') {
          applyTheme(getSystemTheme());
        }
      });
    }
  }

  onMounted(() => {
    initTheme();
  });

  return {
    theme: currentTheme,
    resolvedTheme,
    themes: THEMES,
    setTheme,
    toggleTheme,
    initTheme,
  };
}

// Initialize immediately to prevent flash
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem(STORAGE_KEY) as ThemeName | null;
  const initial = stored && [...THEMES, 'system'].includes(stored) ? stored : 'system';
  applyTheme(resolveTheme(initial));
}
