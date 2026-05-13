import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/DefaultShell.vue'),
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
        { path: 'chat', name: 'chat', component: () => import('@/views/ChatView.vue') },
        { path: 'portfolio', name: 'portfolio', component: () => import('@/views/PortfolioView.vue') },
        { path: 'backtest', name: 'backtest', component: () => import('@/views/BacktestView.vue') },
        { path: 'settings', name: 'settings', component: () => import('@/views/SettingsView.vue') },
        {
          path: ':pathMatch(.*)*',
          name: 'not-found',
          component: () => import('@/views/NotFoundView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    return true
  }

  if (auth.isLoading) {
    return true
  }

  if (auth.loadError) {
    return true
  }

  if (auth.needsLogin && to.path !== '/login') {
    const redirect = encodeURIComponent(to.fullPath)
    return { path: '/login', query: { redirect } }
  }

  if (!auth.needsLogin && to.path === '/login') {
    return { path: '/' }
  }

  return true
})

export default router
