<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()

const nav = [
  {
    to: '/',
    label: '分析',
    exact: true,
    icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />`,
  },
  {
    to: '/backtest',
    label: '回测',
    exact: false,
    icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />`,
  },
  {
    to: '/settings',
    label: '设置',
    exact: false,
    icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />`,
  },
]

function isActive(item: typeof nav[0]) {
  return item.exact ? route.path === item.to : route.path.startsWith(item.to)
}
</script>

<template>
  <aside class="fixed left-0 top-0 h-full w-16 bg-white border-r border-slate-200 flex flex-col items-center py-4 z-30">
    <!-- Logo -->
    <div class="mb-6">
      <div class="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center">
        <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      </div>
    </div>

    <!-- Nav items -->
    <nav class="flex flex-col items-center gap-1 flex-1">
      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        :class="[
          'group relative flex flex-col items-center justify-center h-12 w-12 rounded-xl transition-all',
          isActive(item)
            ? 'bg-blue-50 text-blue-600'
            : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600',
        ]"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" v-html="item.icon" />
        <!-- Tooltip -->
        <div class="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          {{ item.label }}
        </div>
      </RouterLink>
    </nav>
  </aside>
</template>
