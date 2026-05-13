<script setup lang="ts">
import type { ParsedApiError } from '@/api/error'

const props = defineProps<{
  error: ParsedApiError
}>()
</script>

<template>
  <div
    class="rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-foreground"
    role="alert"
  >
    <p class="font-semibold text-danger">{{ props.error.title }}</p>
    <p class="mt-1 text-secondary-text">{{ props.error.message }}</p>
  </div>
</template>
