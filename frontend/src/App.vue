<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useUserStore } from '@/entities/user'
import { useNavbarPosition, useTheme, type NavbarPosition } from '@/shared/composables'

import NotificationBell from '@/components/NotificationBell.vue'

const userStore = useUserStore()
const router = useRouter()
const { toggleTheme, resolvedTheme } = useTheme()
const { navbarPosition, navbarPositionOptions, setNavbarPosition } = useNavbarPosition()

const isNavbarPositionMenuOpen = ref(false)
const navbarPositionMenuRef = ref<HTMLElement | null>(null)

const themeIcon = computed(() => {
  switch (resolvedTheme.value) {
    case 'light': return '☀️'
    case 'dark': return '🌙'
    case 'midnight': return '🌌'
    default: return '🌗'
  }
})

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
  const base = 'fixed z-50 bg-background-soft border border-border shadow-lg shadow-black/5 rounded-xl transition-all duration-500 ease-in-out'

  switch (navbarPosition.value) {
    case 'bottom':
      return `${base} left-1/2 bottom-12 w-[calc(100vw-6rem)] max-w-[1184px] -translate-x-1/2 px-8 py-4`
    case 'left':
      return `${base} left-4 top-1/2 h-[min(720px,calc(100vh-6rem))] w-64 -translate-y-1/2 px-4 py-6`
    case 'right':
      return `${base} right-4 top-1/2 h-[min(720px,calc(100vh-6rem))] w-64 -translate-y-1/2 px-4 py-6`
    case 'top':
    default:
      return `${base} left-1/2 top-12 w-[calc(100vw-6rem)] max-w-[1184px] -translate-x-1/2 px-8 py-4`
  }
})

const navbarNavClass = computed(() => {
  return isSideNavbar.value
    ? 'h-full w-full flex flex-col items-stretch gap-2 text-base'
    : 'w-full flex items-center gap-2 text-base'
})

const pageShellClass = computed(() => {
  if (!showAppNav.value) {
    return 'min-h-screen'
  }

  switch (navbarPosition.value) {
    case 'bottom':
      return 'min-h-screen pb-24 transition-all duration-500 ease-in-out'
    case 'left':
    case 'right':
      return 'min-h-screen transition-all duration-500 ease-in-out'
    case 'top':
    default:
      return 'min-h-screen pt-24 transition-all duration-500 ease-in-out'
  }
})

const navIconButtonClass = computed(() => {
  const base = 'flex items-center text-lg/none bg-transparent border border-border rounded-lg cursor-pointer transition-all duration-200 hover:bg-surface-hover hover:border-border-hover'

  return isSideNavbar.value
    ? `${base} justify-center w-full h-10 px-3`
    : `${base} justify-center w-9 h-9 p-2`
})

const navControlsClass = computed(() => {
  return isSideNavbar.value
    ? 'grid w-full grid-cols-2 gap-2'
    : 'flex items-center gap-2'
})

const navPositionControlClass = computed(() => {
  return 'relative'
})

const navLinkClass = computed(() => {
  return isSideNavbar.value
    ? 'w-full px-4 py-2 rounded-lg transition-all duration-200 hover:bg-primary-500/10'
    : 'px-4 py-2 rounded-lg transition-all duration-200 hover:bg-primary-500/10'
})

const userActionsClass = computed(() => {
  return isSideNavbar.value
    ? 'flex flex-col items-stretch gap-3'
    : 'flex items-center gap-3 justify-end ml-2'
})

const userInfoClass = computed(() => {
  return isSideNavbar.value
    ? 'flex items-center gap-3'
    : 'contents'
})

const notificationDropdownPlacement = computed(() => {
  if (navbarPosition.value === 'left') return 'right-start'
  if (navbarPosition.value === 'right') return 'left-start'
  if (navbarPosition.value === 'bottom') return 'top-end'

  return 'bottom-end'
})

const positionMenuClass = computed(() => {
  const base = 'absolute z-50 w-44 bg-surface border border-border rounded-lg shadow-xl overflow-hidden'

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

function toggleNavbarPositionMenu() {
  isNavbarPositionMenuOpen.value = !isNavbarPositionMenuOpen.value
}

function selectNavbarPosition(position: NavbarPosition) {
  setNavbarPosition(position)
  isNavbarPositionMenuOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  if (
    navbarPositionMenuRef.value &&
    !navbarPositionMenuRef.value.contains(event.target as Node)
  ) {
    isNavbarPositionMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <header 
    v-if="showAppNav"
    :class="navbarShellClass"
  >
    <div class="w-full h-full">
      <nav :class="navbarNavClass">
        <div :class="navControlsClass">
          <button
            :class="navIconButtonClass"
            @click="toggleTheme"
            :title="'Тема: ' + resolvedTheme"
          >
            {{ themeIcon }}
          </button>
          <div ref="navbarPositionMenuRef" :class="navPositionControlClass">
          <button
            :class="navIconButtonClass"
            @click="toggleNavbarPositionMenu"
            :title="'Позиция навбара: ' + selectedNavbarPositionLabel"
          >
            {{ navbarPositionIcon }}
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
                class="w-full flex items-center justify-between px-3 py-2 text-sm text-left text-text cursor-pointer transition-colors duration-150 hover:bg-primary-500/10 hover:text-primary-500"
                :class="{ 'bg-primary-500/5 text-primary-500 font-medium': option.value === navbarPosition }"
                @click="selectNavbarPosition(option.value)"
              >
                <span>{{ option.label }}</span>
                <span v-if="option.value === navbarPosition">✓</span>
              </button>
            </div>
          </Transition>
          </div>
        </div>
        <template v-if="userStore.isAuthenticated">
        <RouterLink
          to="/my-titles"
          :class="navLinkClass"
          active-class="text-primary-500"
        >
          Мои тайтлы
          </RouterLink>
        <RouterLink
          to="/community"
          :class="navLinkClass"
          active-class="text-primary-500"
        >
          Сообщество
        </RouterLink>
        <RouterLink
          to="/settings"
          :class="navLinkClass"
          active-class="text-primary-500"
        >
          Настройки
        </RouterLink>
          <div class="flex-grow"></div>
          <NotificationBell
            v-if="!isSideNavbar"
            :dropdown-placement="notificationDropdownPlacement"
          />
          <div :class="userActionsClass">
            <div :class="userInfoClass">
             <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden border border-border">
                <img 
                  v-if="userStore.user?.avatar_url" 
                  :src="userStore.user.avatar_url" 
                  class="w-full h-full object-cover"
                  alt="Avatar"
                />
                <span v-else class="text-xs font-bold text-primary-600">
                  {{ (userStore.user?.login || '?').substring(0, 1).toUpperCase() }}
                </span>
             </div>
             <span class="font-medium text-text">
                {{ userStore.user?.name || userStore.user?.login }}
             </span>
             <NotificationBell
               v-if="isSideNavbar"
               :dropdown-placement="notificationDropdownPlacement"
             />
            </div>
          
          <button
            class="px-4 py-2 text-sm bg-transparent border border-border rounded-lg text-text cursor-pointer transition-all duration-200 hover:bg-red-500/10 hover:border-red-500 hover:text-red-500"
            @click="handleLogout"
          >
            Выйти
          </button>
          </div>
        </template>
        <template v-else>
          <RouterLink
            to="/login"
            :class="navLinkClass"
            active-class="text-primary-500"
          >
            Войти
          </RouterLink>
          <RouterLink
            to="/register"
            :class="navLinkClass"
            active-class="text-primary-500"
          >
            Регистрация
          </RouterLink>
        </template>
      </nav>
    </div>
  </header>

  <main :class="pageShellClass">
    <RouterView />
  </main>
</template>

