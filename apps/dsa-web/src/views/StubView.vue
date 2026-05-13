<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <div class="mx-auto max-w-xl rounded-2xl border border-border bg-card/60 p-8">
    <h1 class="text-lg font-semibold">{{ title }}</h1>
    <p class="mt-3 text-sm leading-relaxed text-secondary-text">{{ description }}</p>
    <p class="mt-4 text-xs text-muted-foreground">
      当前 Web 前端已迁移为 Vue 3 + Vite；该模块的完整交互将逐步补齐，后端 API 与原先保持一致。
    </p>
  </div>
</template>
