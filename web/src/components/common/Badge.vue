<script setup lang="ts">
defineProps<{
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'history' | 'blue'
  size?: 'sm' | 'md'
}>()
</script>

<template>
  <span
    :class="[
      'inline-flex items-center font-medium rounded-full',
      size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs',
      variant === 'success' ? 'bg-green-100 text-green-700'
        : variant === 'warning' ? 'bg-amber-100 text-amber-700'
        : variant === 'danger' ? 'bg-red-100 text-red-700'
        : variant === 'info' ? 'bg-cyan-100 text-cyan-700'
        : variant === 'blue' ? 'bg-blue-100 text-blue-700'
        : variant === 'history' ? 'bg-slate-100 text-slate-600'
        : 'bg-slate-100 text-slate-600',
    ]"
  >
    <slot />
  </span>
</template>
