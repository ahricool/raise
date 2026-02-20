import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/backtest', component: () => import('@/pages/BacktestPage.vue') },
    { path: '/settings', component: () => import('@/pages/SettingsPage.vue') },
    { path: '/:pathMatch(.*)*', component: () => import('@/pages/NotFoundPage.vue') },
  ],
})

export default router
