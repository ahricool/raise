<script setup lang="ts">
defineProps<{ size?: 'sm' | 'md' | 'lg'; label?: string }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-2">
    <svg
      :class="['animate-spin text-blue-600', size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-10 w-10' : 'h-6 w-6']"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <span v-if="label" class="text-sm text-slate-500">{{ label }}</span>
  </div>
</template>
