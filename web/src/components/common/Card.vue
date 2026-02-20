<script setup lang="ts">
defineProps<{
  title?: string
  subtitle?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hoverable?: boolean
}>()
</script>

<template>
  <div
    :class="[
      'bg-white rounded-xl border border-slate-200 shadow-sm',
      hoverable ? 'hover:shadow-md transition-shadow cursor-pointer' : '',
      padding === 'none' ? '' : padding === 'sm' ? 'p-3' : padding === 'lg' ? 'p-6' : 'p-4',
    ]"
  >
    <div v-if="title || subtitle" class="mb-3">
      <h3 v-if="title" class="text-sm font-semibold text-slate-800">{{ title }}</h3>
      <p v-if="subtitle" class="text-xs text-slate-500 mt-0.5">{{ subtitle }}</p>
    </div>
    <slot />
  </div>
</template>
