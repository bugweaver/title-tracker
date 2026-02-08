import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import { apiClient } from '@/shared/api'
import { useUserStore } from '@/entities/user'

const app = createApp(App)

app.use(createPinia())
app.use(router)

apiClient.setUnauthorizedHandler(() => {
  const userStore = useUserStore()
  userStore.clearTokens()
  userStore.setUser(null)
  router.push('/login')
})

app.mount('#app')
