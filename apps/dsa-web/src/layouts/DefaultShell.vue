<script setup lang="ts">
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'
import { RouterLink, RouterView } from 'vue-router'

const auth = useAuthStore()

const items = [
  { to: '/', label: '首页' },
  { to: '/chat', label: '问股' },
  { to: '/portfolio', label: '持仓' },
  { to: '/backtest', label: '回测' },
  { to: '/settings', label: '设置' },
]

async function onLogout() {
  if (!window.confirm('确认退出当前登录状态吗？退出后需要重新输入密码。')) {
    return
  }
  await auth.logout()
}
</script>

<template>
  <div class="flex min-h-screen flex-col bg-background text-foreground md:flex-row">
    <aside
      class="flex flex-row flex-wrap gap-1 border-b border-border bg-card/80 p-2 md:w-52 md:flex-col md:flex-nowrap md:border-b-0 md:border-r md:p-4"
      aria-label="主导航"
    >
      <div class="mr-auto flex items-center gap-2 px-2 py-1 md:mr-0 md:mb-4">
        <div
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-cyan-600 text-sm text-primary-foreground"
        >
          DSA
        </div>
        <span class="text-sm font-semibold md:hidden">工作台</span>
      </div>
      <RouterLink
        v-for="link in items"
        :key="link.to"
        :to="link.to"
        class="rounded-lg px-3 py-2 text-sm whitespace-nowrap text-secondary-text transition hover:bg-hover"
        active-class="bg-primary/15 font-medium text-primary"
      >
        {{ link.label }}
      </RouterLink>
      <div class="mt-auto flex w-full flex-col gap-2 pt-2 md:pt-4">
        <ThemeToggle />
        <button
          v-if="auth.authEnabled"
          type="button"
          class="rounded-lg px-3 py-2 text-left text-sm text-secondary-text hover:bg-hover"
          @click="onLogout"
        >
          退出
        </button>
      </div>
    </aside>
    <main class="min-h-0 min-w-0 flex-1 p-4 md:p-6">
      <RouterView />
    </main>
  </div>
</template>
