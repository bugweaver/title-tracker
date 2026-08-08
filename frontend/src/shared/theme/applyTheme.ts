import type { ThemeDefinition } from './catalog';

const THEME_STYLE_KEYS = [
  '--theme-primary',
  '--theme-primary-50',
  '--theme-primary-100',
  '--theme-primary-200',
  '--theme-primary-300',
  '--theme-primary-400',
  '--theme-primary-500',
  '--theme-primary-600',
  '--theme-primary-700',
  '--theme-primary-800',
  '--theme-primary-900',
  '--theme-bg',
  '--theme-bg-soft',
  '--theme-bg-mute',
  '--theme-surface',
  '--theme-surface-hover',
  '--theme-text',
  '--theme-text-secondary',
  '--theme-text-muted',
  '--theme-border',
  '--theme-border-hover',
  '--theme-error',
  '--theme-error-bg',
  '--theme-success',
  '--theme-success-bg',
  '--theme-shadow-sm',
  '--theme-shadow-md',
  '--theme-shadow-lg',
] as const;

function mix(color: string, toward: string, amount: number): string {
  return `color-mix(in srgb, ${color} ${amount}%, ${toward})`;
}

function buildThemeVars(theme: ThemeDefinition): Record<(typeof THEME_STYLE_KEYS)[number], string> {
  const towardLight = theme.mode === 'light' ? '#ffffff' : theme.bg;
  const towardDark = theme.mode === 'light' ? '#000000' : '#ffffff';
  const borderBase = theme.mode === 'light' ? '12%' : '10%';
  const borderHover = theme.mode === 'light' ? '29%' : '20%';
  const shadowAlpha = theme.mode === 'light'
    ? { sm: '0.05', md: '0.07', lg: '0.12' }
    : { sm: '0.3', md: '0.4', lg: '0.5' };

  // Light: 50 lightest → 900 darkest. Dark: keep 500 as accent; 50–400 tint toward bg, 600–900 brighten.
  const primaryScale = theme.mode === 'light'
    ? {
      50: mix(theme.primary, towardLight, 8),
      100: mix(theme.primary, towardLight, 16),
      200: mix(theme.primary, towardLight, 30),
      300: mix(theme.primary, towardLight, 50),
      400: mix(theme.primary, towardLight, 75),
      500: theme.primary,
      600: mix(theme.primary, towardDark, 85),
      700: mix(theme.primary, towardDark, 70),
      800: mix(theme.primary, towardDark, 55),
      900: mix(theme.primary, towardDark, 40),
    }
    : {
      50: mix(theme.primary, towardLight, 12),
      100: mix(theme.primary, towardLight, 22),
      200: mix(theme.primary, towardLight, 40),
      300: mix(theme.primary, towardLight, 60),
      400: mix(theme.primary, towardLight, 80),
      500: theme.primary,
      600: mix(theme.primary, towardDark, 80),
      700: mix(theme.primary, towardDark, 65),
      800: mix(theme.primary, towardDark, 50),
      900: mix(theme.primary, towardDark, 35),
    };

  return {
    '--theme-primary': theme.primary,
    '--theme-primary-50': primaryScale[50],
    '--theme-primary-100': primaryScale[100],
    '--theme-primary-200': primaryScale[200],
    '--theme-primary-300': primaryScale[300],
    '--theme-primary-400': primaryScale[400],
    '--theme-primary-500': primaryScale[500],
    '--theme-primary-600': primaryScale[600],
    '--theme-primary-700': primaryScale[700],
    '--theme-primary-800': primaryScale[800],
    '--theme-primary-900': primaryScale[900],
    '--theme-bg': theme.bg,
    '--theme-bg-soft': theme.bgSoft,
    '--theme-bg-mute': theme.bgMute,
    '--theme-surface': theme.surface,
    '--theme-surface-hover': theme.surfaceHover,
    '--theme-text': theme.text,
    '--theme-text-secondary': theme.textSecondary,
    '--theme-text-muted': theme.textMuted,
    '--theme-border': mix(theme.text, 'transparent', Number.parseInt(borderBase, 10)),
    '--theme-border-hover': mix(theme.text, 'transparent', Number.parseInt(borderHover, 10)),
    '--theme-error': theme.error,
    '--theme-error-bg': mix(theme.error, 'transparent', 15),
    '--theme-success': theme.success,
    '--theme-success-bg': mix(theme.success, 'transparent', 15),
    '--theme-shadow-sm': `0 1px 2px rgba(0, 0, 0, ${shadowAlpha.sm})`,
    '--theme-shadow-md': `0 4px 6px rgba(0, 0, 0, ${shadowAlpha.md})`,
    '--theme-shadow-lg': `0 8px 32px rgba(0, 0, 0, ${shadowAlpha.lg})`,
  };
}

export function clearAppliedThemeVars(root: HTMLElement = document.documentElement): void {
  for (const key of THEME_STYLE_KEYS) {
    root.style.removeProperty(key);
  }
}

export function applyThemeVars(
  theme: ThemeDefinition,
  root: HTMLElement = document.documentElement,
): void {
  root.setAttribute('data-theme', theme.id);
  root.setAttribute('data-theme-mode', theme.mode);
  root.style.colorScheme = theme.mode;

  const vars = buildThemeVars(theme);
  for (const [key, value] of Object.entries(vars)) {
    root.style.setProperty(key, value);
  }
}
