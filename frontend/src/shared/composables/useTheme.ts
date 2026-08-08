import { computed, onMounted, ref } from 'vue';
import {
  THEME_CATALOG,
  THEME_IDS,
  applyThemeVars,
  getThemeById,
  type ThemeDefinition,
  type ThemeMode,
} from '@/shared/theme';

export type ThemeName = string;

const STORAGE_KEY = 'theme-preference';

const currentTheme = ref<ThemeName>('light');
const resolvedTheme = ref<ThemeName>('light');
const previewThemeId = ref<ThemeName | null>(null);

function getSystemThemeId(): ThemeName {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function resolveThemeId(theme: ThemeName): ThemeName {
  if (theme === 'system') return getSystemThemeId();
  return THEME_IDS.includes(theme) ? theme : 'light';
}

function paintTheme(themeId: ThemeName) {
  const theme = getThemeById(themeId);
  applyThemeVars(theme);
  resolvedTheme.value = theme.id;
}

function applyStoredOrPreview() {
  const id = previewThemeId.value ?? resolveThemeId(currentTheme.value);
  paintTheme(id);
}

export function useTheme() {
  const activeTheme = computed<ThemeDefinition>(() => getThemeById(resolvedTheme.value));
  const themeMode = computed<ThemeMode>(() => activeTheme.value.mode);

  function setTheme(theme: ThemeName) {
    previewThemeId.value = null;
    currentTheme.value = theme;
    localStorage.setItem(STORAGE_KEY, theme);
    paintTheme(resolveThemeId(theme));
  }

  function previewTheme(themeId: ThemeName | null) {
    previewThemeId.value = themeId && THEME_IDS.includes(themeId) ? themeId : null;
    applyStoredOrPreview();
  }

  function toggleTheme() {
    const currentId = resolvedTheme.value;
    const currentIndex = THEME_IDS.indexOf(currentId);
    const nextIndex = (currentIndex + 1) % THEME_IDS.length;
    const nextTheme = THEME_IDS[nextIndex] ?? 'light';
    setTheme(nextTheme);
  }

  function initTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    const initial = stored && (stored === 'system' || THEME_IDS.includes(stored))
      ? stored
      : 'system';
    currentTheme.value = initial;
    paintTheme(resolveThemeId(initial));

    if (typeof window !== 'undefined') {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (currentTheme.value === 'system' && !previewThemeId.value) {
          paintTheme(getSystemThemeId());
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
    activeTheme,
    themeMode,
    themes: THEME_CATALOG,
    themeIds: THEME_IDS,
    setTheme,
    previewTheme,
    toggleTheme,
    initTheme,
  };
}

// Initialize immediately to prevent flash
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem(STORAGE_KEY);
  const initial = stored && (stored === 'system' || THEME_IDS.includes(stored))
    ? stored
    : 'system';
  currentTheme.value = initial;
  paintTheme(resolveThemeId(initial));
}
