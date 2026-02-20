<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
}>()
</script>

<template>
  <button
    :type="type ?? 'button'"
    :disabled="disabled || loading"
    :class="[
      'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all',
      'focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
      size === 'sm' ? 'px-3 py-1.5 text-sm' : size === 'lg' ? 'px-6 py-3 text-base' : 'px-4 py-2 text-sm',
      variant === 'primary' || !variant
        ? 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500'
        : variant === 'secondary'
        ? 'bg-slate-100 hover:bg-slate-200 text-slate-700 focus:ring-slate-400'
        : variant === 'outline'
        ? 'border border-slate-300 hover:bg-slate-50 text-slate-700 focus:ring-slate-400'
        : variant === 'ghost'
        ? 'hover:bg-slate-100 text-slate-600 focus:ring-slate-400'
        : variant === 'danger'
        ? 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500'
        : '',
    ]"
  >
    <svg v-if="loading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <slot />
  </button>
</template>
