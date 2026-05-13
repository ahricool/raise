<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { theme, toggle } = useTheme()
</script>

<template>
  <button
    type="button"
    class="flex h-10 w-full items-center justify-center gap-2 rounded-2xl border border-border/70 bg-card/80 text-xs text-secondary-text transition hover:bg-hover hover:text-foreground"
    aria-label="切换主题"
    @click="toggle"
  >
    <span class="font-medium">{{ theme === 'dark' ? '深色' : '浅色' }}</span>
    <span class="text-muted-foreground">⇄</span>
  </button>
</template>
