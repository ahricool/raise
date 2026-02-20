<script setup lang="ts">
defineProps<{
  title?: string
  message: string
  variant?: 'error' | 'success' | 'warning'
  actionLabel?: string
}>()
defineEmits<{ (e: 'action'): void }>()
</script>

<template>
  <div
    :class="[
      'rounded-xl border p-4',
      variant === 'error' ? 'bg-red-50 border-red-200' : variant === 'success' ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200',
    ]"
  >
    <div class="flex items-start gap-3">
      <svg
        :class="['h-5 w-5 mt-0.5 shrink-0', variant === 'error' ? 'text-red-500' : variant === 'success' ? 'text-green-500' : 'text-amber-500']"
        fill="none" viewBox="0 0 24 24" stroke="currentColor"
      >
        <path v-if="variant === 'success'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div class="flex-1">
        <p v-if="title" :class="['text-sm font-semibold', variant === 'error' ? 'text-red-700' : variant === 'success' ? 'text-green-700' : 'text-amber-700']">
          {{ title }}
        </p>
        <p :class="['text-sm', variant === 'error' ? 'text-red-600' : variant === 'success' ? 'text-green-600' : 'text-amber-600']">
          {{ message }}
        </p>
      </div>
      <button v-if="actionLabel" class="text-sm font-medium text-blue-600 hover:underline shrink-0" @click="$emit('action')">
        {{ actionLabel }}
      </button>
    </div>
  </div>
</template>
