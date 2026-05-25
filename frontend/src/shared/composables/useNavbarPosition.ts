import { ref } from 'vue';

export type NavbarPosition = 'top' | 'right' | 'bottom' | 'left';

const STORAGE_KEY = 'navbar-position-preference';

const NAVBAR_POSITIONS: NavbarPosition[] = ['top', 'right', 'bottom', 'left'];

export const navbarPositionOptions: { value: NavbarPosition; label: string }[] = [
  { value: 'top', label: 'Сверху' },
  { value: 'right', label: 'Справа' },
  { value: 'bottom', label: 'Снизу' },
  { value: 'left', label: 'Слева' },
];

const navbarPosition = ref<NavbarPosition>('top');

function isNavbarPosition(value: string | null): value is NavbarPosition {
  return NAVBAR_POSITIONS.includes(value as NavbarPosition);
}

function getStoredNavbarPosition(): NavbarPosition {
  if (typeof window === 'undefined') return 'top';

  const stored = localStorage.getItem(STORAGE_KEY);
  return isNavbarPosition(stored) ? stored : 'top';
}

function applyNavbarPosition(position: NavbarPosition) {
  navbarPosition.value = position;
}

export function useNavbarPosition() {
  function setNavbarPosition(position: NavbarPosition) {
    navbarPosition.value = position;

    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, position);
    }
  }

  function initNavbarPosition() {
    applyNavbarPosition(getStoredNavbarPosition());
  }

  return {
    navbarPosition,
    navbarPositionOptions,
    setNavbarPosition,
    initNavbarPosition,
  };
}

if (typeof window !== 'undefined') {
  applyNavbarPosition(getStoredNavbarPosition());
}
