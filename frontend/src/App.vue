<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { onMounted, computed } from 'vue'
import { useUserStore } from '@/entities/user'
import { useTheme } from '@/shared/composables'

import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const { toggleTheme, resolvedTheme } = useTheme()

const themeIcon = computed(() => {
  switch (resolvedTheme.value) {
    case 'light': return '☀️'
    case 'dark': return '🌙'
    case 'midnight': return '🌌'
    default: return '🌗'
  }
})

onMounted(async () => {
  // Auth initialization is now handled in router guard
})

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <header 
    v-if="!['login', 'register'].includes($route.name as string)"
    class="leading-normal px-8 py-4 bg-background-soft m-4 rounded-xl border border-border"
  >
    <div class="w-full">
      <nav class="w-full flex items-center gap-2 text-base">
        <button
          class="
            flex items-center justify-center w-9 h-9 p-2
            text-lg/none bg-transparent border border-border
            rounded-lg cursor-pointer transition-all duration-200
            hover:bg-surface-hover hover:border-border-hover
          "
          @click="toggleTheme"
          :title="'Тема: ' + resolvedTheme"
        >
          {{ themeIcon }}
        </button>
        <template v-if="userStore.isAuthenticated">
        <RouterLink
          to="/"
          class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-primary-500/10"
          active-class="text-primary-500"
        >
          Главная
        </RouterLink>

        <RouterLink
          to="/my-titles"
          class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-primary-500/10"
          active-class="text-primary-500"
        >
          Мои тайтлы
          </RouterLink>
        <RouterLink
          to="/community"
          class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-primary-500/10"
          active-class="text-primary-500"
        >
          Сообщество
        </RouterLink>
        <RouterLink
          to="/settings"
          class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-primary-500/10"
          active-class="text-primary-500"
        >
          Настройки
        </RouterLink>
          <div class="flex-grow"></div>
          <div class="flex items-center gap-3 justify-end">
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
            class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-primary-500/10"
            active-class="text-primary-500"
          >
            Войти
          </RouterLink>
          <RouterLink
            to="/register"
            class="px-4 py-2 rounded-lg transition-all duration-200 hover:bg-primary-500/10"
            active-class="text-primary-500"
          >
            Регистрация
          </RouterLink>
        </template>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

