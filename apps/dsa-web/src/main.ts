import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import './dsa-index.css'
import router from './router'
import { useAuthStore } from '@/stores/auth'

async function boot() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)

  const auth = useAuthStore()
  await auth.bootstrap()

  app.mount('#app')
}

void boot()
