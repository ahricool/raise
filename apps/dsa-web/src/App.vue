<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import ApiErrorAlert from '@/components/ApiErrorAlert.vue'
import { RouterView } from 'vue-router'

const auth = useAuthStore()

async function retryAuth() {
  await auth.bootstrap()
}
</script>

<template>
  <div v-if="auth.isLoading" class="flex min-h-screen items-center justify-center bg-background text-foreground">
    <div
      class="h-8 w-8 animate-spin rounded-full border-2 border-primary/20 border-t-primary"
      aria-label="加载中"
    />
  </div>
  <div
    v-else-if="auth.loadError"
    class="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4 text-foreground"
  >
    <div class="w-full max-w-lg">
      <ApiErrorAlert :error="auth.loadError" />
    </div>
    <button type="button" class="rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground" @click="retryAuth">
      重试
    </button>
  </div>
  <RouterView v-else />
</template>
