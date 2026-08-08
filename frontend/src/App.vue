<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useUserStore } from '@/entities/user'
import { useNavbarPosition, useTheme, type NavbarPosition } from '@/shared/composables'

import NotificationBell from '@/components/NotificationBell.vue'

const userStore = useUserStore()
const router = useRouter()
const { toggleTheme, themeMode, activeTheme } = useTheme()
const { navbarPosition, navbarPositionOptions, setNavbarPosition } = useNavbarPosition()

const isNavbarPositionMenuOpen = ref(false)
const isUserMenuOpen = ref(false)
const navbarPositionMenuRef = ref<HTMLElement | null>(null)
const userMenuRef = ref<HTMLElement | null>(null)
const isMobileMenuOpen = ref(false)
let previousBodyOverflow = ''

const primaryNav = [
  { to: '/my-titles', label: 'Мои тайтлы' },
  { to: '/lists', label: 'Списки' },
  { to: '/feed', label: 'Лента' },
  { to: '/community', label: 'Сообщество' },
] as const

const themeIcon = computed(() => (themeMode.value === 'light' ? '☀️' : '🌙'))
const themeLabel = computed(() => activeTheme.value.name)

const navbarPositionIcon = computed(() => {
  switch (navbarPosition.value) {
    case 'top': return '↑'
    case 'right': return '→'
    case 'bottom': return '↓'
    case 'left': return '←'
    default: return '↕'
  }
})

const selectedNavbarPositionLabel = computed(() => {
  return navbarPositionOptions.find(option => option.value === navbarPosition.value)?.label ?? 'Позиция'
})

const showAppNav = computed(() => {
  return !['login', 'register'].includes(router.currentRoute.value.name as string)
})

const isSideNavbar = computed(() => {
  return navbarPosition.value === 'left' || navbarPosition.value === 'right'
})

const navbarShellClass = computed(() => {
  const base = 'hidden md:block fixed z-50 bg-background-soft/95 border border-border shadow-lg shadow-black/5 rounded-2xl backdrop-blur transition-all duration-500 ease-in-out'

  switch (navbarPosition.value) {
    case 'bottom':
      return `${base} left-1/2 bottom-12 w-[calc(100vw-6rem)] max-w-[960px] -translate-x-1/2 px-3 py-2.5`
    case 'left':
      return `${base} left-4 top-1/2 h-[min(640px,calc(100vh-6rem))] w-56 -translate-y-1/2 px-3 py-5`
    case 'right':
      return `${base} right-4 top-1/2 h-[min(640px,calc(100vh-6rem))] w-56 -translate-y-1/2 px-3 py-5`
    case 'top':
    default:
      return `${base} left-1/2 top-10 w-[calc(100vw-6rem)] max-w-[960px] -translate-x-1/2 px-3 py-2.5`
  }
})

const navbarNavClass = computed(() => {
  return isSideNavbar.value
    ? 'h-full w-full flex flex-col items-stretch gap-1.5 text-sm'
    : 'flex h-full w-full items-center justify-between gap-3 text-sm'
})

const primaryNavGroupClass = computed(() => {
  return isSideNavbar.value
    ? 'flex flex-col items-stretch gap-1'
    : 'flex min-w-0 items-center gap-1'
})

const userToolsClass = computed(() => {
  return isSideNavbar.value
    ? 'mt-auto flex flex-col items-stretch gap-1.5'
    : 'ml-auto flex shrink-0 items-center justify-end gap-1.5'
})

const pageShellClass = computed(() => {
  if (!showAppNav.value) {
    return 'min-h-screen'
  }

  switch (navbarPosition.value) {
    case 'bottom':
      return 'min-h-screen pt-[calc(4rem+env(safe-area-inset-top))] md:pt-0 md:pb-24 transition-all duration-500 ease-in-out'
    case 'left':
      return 'min-h-screen pt-[calc(4rem+env(safe-area-inset-top))] md:pt-0 md:pl-60 transition-all duration-500 ease-in-out'
    case 'right':
      return 'min-h-screen pt-[calc(4rem+env(safe-area-inset-top))] md:pt-0 md:pr-60 transition-all duration-500 ease-in-out'
    case 'top':
    default:
      return 'min-h-screen pt-[calc(4rem+env(safe-area-inset-top))] md:pt-24 transition-all duration-500 ease-in-out'
  }
})

const navLinkClass = computed(() => {
  return isSideNavbar.value
    ? 'w-full px-3 py-2 rounded-lg text-text-secondary transition-colors duration-200 hover:bg-primary-500/10 hover:text-text'
    : 'flex min-h-10 shrink-0 items-center whitespace-nowrap px-3 py-2 rounded-lg text-text-secondary transition-colors duration-200 hover:bg-primary-500/10 hover:text-text'
})

const notificationDropdownPlacement = computed(() => {
  if (navbarPosition.value === 'left') return 'right-start'
  if (navbarPosition.value === 'right') return 'left-start'
  if (navbarPosition.value === 'bottom') return 'top-end'
  return 'bottom-end'
})

const userMenuClass = computed(() => {
  const base = 'absolute z-50 w-56 rounded-xl border border-border bg-surface shadow-xl overflow-hidden'

  if (navbarPosition.value === 'right') {
    return `${base} right-full top-0 mr-2`
  }
  if (navbarPosition.value === 'left') {
    return `${base} left-full bottom-0 ml-2`
  }
  if (navbarPosition.value === 'bottom') {
    return `${base} right-0 bottom-full mb-2`
  }
  return `${base} right-0 top-full mt-2`
})

const positionMenuClass = computed(() => {
  const base = 'absolute z-[60] w-44 bg-surface border border-border rounded-lg shadow-xl overflow-hidden'

  if (navbarPosition.value === 'right') {
    return `${base} right-full top-0 mr-2`
  }
  if (navbarPosition.value === 'left') {
    return `${base} left-full top-0 ml-2`
  }
  if (navbarPosition.value === 'bottom') {
    return `${base} left-0 bottom-full mb-2`
  }
  return `${base} left-0 top-full mt-2`
})

function toggleUserMenu() {
  isUserMenuOpen.value = !isUserMenuOpen.value
  if (isUserMenuOpen.value) {
    isNavbarPositionMenuOpen.value = false
  }
}

function closeUserMenu() {
  isUserMenuOpen.value = false
  isNavbarPositionMenuOpen.value = false
}

function toggleNavbarPositionMenu() {
  isNavbarPositionMenuOpen.value = !isNavbarPositionMenuOpen.value
}

function selectNavbarPosition(position: NavbarPosition) {
  setNavbarPosition(position)
  isNavbarPositionMenuOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target as Node
  if (userMenuRef.value && !userMenuRef.value.contains(target)) {
    isUserMenuOpen.value = false
  }
  if (
    navbarPositionMenuRef.value &&
    !navbarPositionMenuRef.value.contains(target)
  ) {
    isNavbarPositionMenuOpen.value = false
  }
}

function closeMobileMenu() {
  isMobileMenuOpen.value = false
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closeMobileMenu()
    closeUserMenu()
  }
}

watch(isMobileMenuOpen, (isOpen) => {
  if (isOpen) {
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = previousBodyOverflow
  }
})

watch(() => router.currentRoute.value.fullPath, () => {
  closeMobileMenu()
  closeUserMenu()
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = previousBodyOverflow
})

async function handleLogout() {
  closeMobileMenu()
  closeUserMenu()
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <header
    v-if="showAppNav"
    class="fixed inset-x-0 top-0 z-50 flex h-[calc(4rem+env(safe-area-inset-top))] items-center gap-3 border-b border-border bg-background-soft/95 px-3 pt-[env(safe-area-inset-top)] shadow-sm backdrop-blur md:hidden"
  >
    <button
      class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-border text-2xl text-text transition-colors hover:bg-surface-hover"
      type="button"
      aria-controls="mobile-navigation"
      :aria-expanded="isMobileMenuOpen"
      aria-label="Открыть меню"
      @click="isMobileMenuOpen = true"
    >
      ☰
    </button>
    <RouterLink
      v-if="userStore.isAuthenticated"
      to="/my-titles"
      class="min-w-0 flex-1 truncate text-base font-bold text-text"
    >
      Title Tracker
    </RouterLink>
    <span v-else class="min-w-0 flex-1 truncate text-base font-bold text-text">
      Title Tracker
    </span>
    <NotificationBell
      v-if="userStore.isAuthenticated"
      dropdown-placement="bottom-end"
    />
  </header>

  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-active-class="transition-opacity duration-200"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showAppNav && isMobileMenuOpen"
        class="fixed inset-0 z-[70] bg-black/55 md:hidden"
        aria-hidden="true"
        @click="closeMobileMenu"
      />
    </Transition>
    <Transition
      enter-active-class="transition-transform duration-300 ease-out"
      enter-from-class="-translate-x-full"
      leave-active-class="transition-transform duration-200 ease-in"
      leave-to-class="-translate-x-full"
    >
      <aside
        v-if="showAppNav && isMobileMenuOpen"
        id="mobile-navigation"
        class="fixed inset-y-0 left-0 z-[80] flex w-[min(86vw,340px)] flex-col overflow-y-auto border-r border-border bg-surface px-4 pb-[calc(1rem+env(safe-area-inset-bottom))] pt-[calc(1rem+env(safe-area-inset-top))] shadow-2xl md:hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Навигация"
      >
        <div class="mb-5 flex items-center justify-between gap-3">
          <span class="text-lg font-bold text-text">Меню</span>
          <button
            type="button"
            class="flex h-11 w-11 items-center justify-center rounded-lg text-2xl text-text transition-colors hover:bg-surface-hover"
            aria-label="Закрыть меню"
            @click="closeMobileMenu"
          >
            ×
          </button>
        </div>

        <template v-if="userStore.isAuthenticated">
          <div class="mb-5 flex min-w-0 items-center gap-3 rounded-xl bg-background-soft p-3">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-full border border-border bg-primary-100">
              <img
                v-if="userStore.user?.avatar_url"
                :src="userStore.user.avatar_url"
                class="h-full w-full object-cover"
                alt="Аватар"
              />
              <span v-else class="font-bold text-primary-600">
                {{ (userStore.user?.login || '?').substring(0, 1).toUpperCase() }}
              </span>
            </div>
            <div class="min-w-0">
              <div class="truncate font-semibold text-text">
                {{ userStore.user?.name || userStore.user?.login }}
              </div>
              <div class="truncate text-sm text-text-secondary">@{{ userStore.user?.login }}</div>
            </div>
          </div>

          <nav class="flex flex-col gap-1 text-base">
            <RouterLink
              v-for="item in primaryNav"
              :key="item.to"
              :to="item.to"
              class="flex min-h-11 items-center rounded-lg px-4 text-text transition-colors hover:bg-primary-500/10"
              active-class="bg-primary-500/10 text-primary-500"
            >
              {{ item.label }}
            </RouterLink>
          </nav>

          <div class="my-4 border-t border-border" />

          <nav class="flex flex-col gap-1 text-base">
            <RouterLink to="/stats" class="flex min-h-11 items-center rounded-lg px-4 text-text-secondary transition-colors hover:bg-primary-500/10" active-class="bg-primary-500/10 text-primary-500">
              Статистика
            </RouterLink>
            <RouterLink to="/settings" class="flex min-h-11 items-center rounded-lg px-4 text-text-secondary transition-colors hover:bg-primary-500/10" active-class="bg-primary-500/10 text-primary-500">
              Настройки
            </RouterLink>
            <RouterLink to="/about" class="flex min-h-11 items-center rounded-lg px-4 text-text-secondary transition-colors hover:bg-primary-500/10" active-class="bg-primary-500/10 text-primary-500">
              О проекте
            </RouterLink>
          </nav>

          <div class="mt-auto flex flex-col gap-2 border-t border-border pt-4">
            <button
              type="button"
              class="flex min-h-11 items-center justify-between rounded-lg border border-border px-4 text-left text-text transition-colors hover:bg-surface-hover"
              :title="`Тема: ${themeLabel}. Клик — следующая, полный список в Настройках.`"
              @click="toggleTheme"
            >
              <span>Тема: {{ themeLabel }}</span>
              <span aria-hidden="true">{{ themeIcon }}</span>
            </button>
            <button
              type="button"
              class="min-h-11 rounded-lg border border-red-500/40 px-4 text-left text-red-500 transition-colors hover:bg-red-500/10"
              @click="handleLogout"
            >
              Выйти
            </button>
          </div>
        </template>

        <nav v-else class="flex flex-col gap-2">
          <RouterLink to="/about" class="flex min-h-11 items-center rounded-lg px-4 text-text hover:bg-primary-500/10">О проекте</RouterLink>
          <RouterLink to="/login" class="flex min-h-11 items-center rounded-lg px-4 text-text hover:bg-primary-500/10">Войти</RouterLink>
          <RouterLink to="/register" class="flex min-h-11 items-center rounded-lg px-4 text-text hover:bg-primary-500/10">Регистрация</RouterLink>
        </nav>
      </aside>
    </Transition>
  </Teleport>

  <header
    v-if="showAppNav"
    :class="navbarShellClass"
  >
    <div class="h-full w-full">
      <nav :class="navbarNavClass">
        <template v-if="userStore.isAuthenticated">
          <div :class="primaryNavGroupClass">
            <RouterLink
              v-for="item in primaryNav"
              :key="item.to"
              :to="item.to"
              :class="navLinkClass"
              active-class="!text-primary-500 bg-primary-500/10 font-medium"
            >
              {{ item.label }}
            </RouterLink>
          </div>

          <div :class="userToolsClass">
            <NotificationBell
              :dropdown-placement="notificationDropdownPlacement"
            />

            <div ref="userMenuRef" class="relative">
              <button
                type="button"
                class="flex h-10 items-center gap-2 rounded-full border border-border bg-transparent px-1.5 pr-2 transition-colors hover:bg-surface-hover hover:border-border-hover"
                :class="isSideNavbar ? 'w-full justify-start' : ''"
                :aria-expanded="isUserMenuOpen"
                aria-haspopup="menu"
                aria-label="Меню профиля"
                @click.stop="toggleUserMenu"
              >
                <span class="flex h-7 w-7 items-center justify-center overflow-hidden rounded-full border border-border bg-primary-100">
                  <img
                    v-if="userStore.user?.avatar_url"
                    :src="userStore.user.avatar_url"
                    class="h-full w-full object-cover"
                    alt=""
                  />
                  <span v-else class="text-xs font-bold text-primary-600">
                    {{ (userStore.user?.login || '?').substring(0, 1).toUpperCase() }}
                  </span>
                </span>
                <span
                  class="max-w-28 truncate text-sm font-medium text-text"
                  :class="isSideNavbar ? 'block' : 'hidden lg:inline'"
                >
                  {{ userStore.user?.name || userStore.user?.login }}
                </span>
              </button>

              <Transition
                enter-active-class="transition duration-150 ease-out"
                enter-from-class="transform scale-95 opacity-0"
                enter-to-class="transform scale-100 opacity-100"
                leave-active-class="transition duration-100 ease-in"
                leave-from-class="transform scale-100 opacity-100"
                leave-to-class="transform scale-95 opacity-0"
              >
                <div
                  v-if="isUserMenuOpen"
                  :class="userMenuClass"
                  role="menu"
                >
                  <div class="border-b border-border px-3 py-2.5">
                    <div class="truncate text-sm font-semibold text-text">
                      {{ userStore.user?.name || userStore.user?.login }}
                    </div>
                    <div class="truncate text-xs text-text-muted">
                      @{{ userStore.user?.login }}
                    </div>
                  </div>

                  <div class="p-1">
                    <RouterLink
                      to="/stats"
                      class="flex min-h-10 items-center rounded-lg px-3 text-sm text-text transition-colors hover:bg-primary-500/10"
                      role="menuitem"
                      @click="closeUserMenu"
                    >
                      Статистика
                    </RouterLink>
                    <RouterLink
                      to="/settings"
                      class="flex min-h-10 items-center rounded-lg px-3 text-sm text-text transition-colors hover:bg-primary-500/10"
                      role="menuitem"
                      @click="closeUserMenu"
                    >
                      Настройки
                    </RouterLink>
                    <RouterLink
                      to="/about"
                      class="flex min-h-10 items-center rounded-lg px-3 text-sm text-text transition-colors hover:bg-primary-500/10"
                      role="menuitem"
                      @click="closeUserMenu"
                    >
                      О проекте
                    </RouterLink>
                  </div>

                  <div class="border-t border-border p-1">
                    <button
                      type="button"
                      class="flex min-h-10 w-full items-center justify-between rounded-lg px-3 text-left text-sm text-text transition-colors hover:bg-surface-hover"
                      role="menuitem"
                      :title="`Тема: ${themeLabel}. Клик — следующая, полный список в Настройках.`"
                      @click="toggleTheme"
                    >
                      <span>Тема: {{ themeLabel }}</span>
                      <span aria-hidden="true">{{ themeIcon }}</span>
                    </button>

                    <div ref="navbarPositionMenuRef" class="relative">
                      <button
                        type="button"
                        class="flex min-h-10 w-full items-center justify-between rounded-lg px-3 text-left text-sm text-text transition-colors hover:bg-surface-hover"
                        role="menuitem"
                        @click.stop="toggleNavbarPositionMenu"
                      >
                        <span>Позиция: {{ selectedNavbarPositionLabel }}</span>
                        <span aria-hidden="true">{{ navbarPositionIcon }}</span>
                      </button>

                      <Transition
                        enter-active-class="transition duration-150 ease-out"
                        enter-from-class="transform scale-95 opacity-0"
                        enter-to-class="transform scale-100 opacity-100"
                        leave-active-class="transition duration-100 ease-in"
                        leave-from-class="transform scale-100 opacity-100"
                        leave-to-class="transform scale-95 opacity-0"
                      >
                        <div
                          v-if="isNavbarPositionMenuOpen"
                          :class="positionMenuClass"
                        >
                          <button
                            v-for="option in navbarPositionOptions"
                            :key="option.value"
                            class="flex w-full items-center justify-between px-3 py-2 text-left text-sm text-text transition-colors hover:bg-primary-500/10 hover:text-primary-500"
                            :class="{ 'bg-primary-500/5 font-medium text-primary-500': option.value === navbarPosition }"
                            @click="selectNavbarPosition(option.value)"
                          >
                            <span>{{ option.label }}</span>
                            <span v-if="option.value === navbarPosition">✓</span>
                          </button>
                        </div>
                      </Transition>
                    </div>
                  </div>

                  <div class="border-t border-border p-1">
                    <button
                      type="button"
                      class="flex min-h-10 w-full items-center rounded-lg px-3 text-left text-sm text-red-500 transition-colors hover:bg-red-500/10"
                      role="menuitem"
                      @click="handleLogout"
                    >
                      Выйти
                    </button>
                  </div>
                </div>
              </Transition>
            </div>
          </div>
        </template>

        <template v-else>
          <div :class="primaryNavGroupClass">
            <RouterLink
              to="/about"
              :class="navLinkClass"
              active-class="!text-primary-500"
            >
              О проекте
            </RouterLink>
          </div>
          <div :class="userToolsClass">
            <RouterLink
              to="/login"
              :class="navLinkClass"
              active-class="!text-primary-500"
            >
              Войти
            </RouterLink>
            <RouterLink
              to="/register"
              class="flex min-h-10 items-center rounded-lg bg-primary-500 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-600"
            >
              Регистрация
            </RouterLink>
          </div>
        </template>
      </nav>
    </div>
  </header>

  <main :class="pageShellClass">
    <RouterView />
  </main>
</template>
