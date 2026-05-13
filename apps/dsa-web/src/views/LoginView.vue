<script setup lang="ts">
import ApiErrorAlert from '@/components/ApiErrorAlert.vue'
import { useAuthStore } from '@/stores/auth'
import { getParsedApiError } from '@/api/error'
import { useRoute, useRouter } from 'vue-router'
import { ref } from 'vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const password = ref('')
const passwordConfirm = ref('')
const error = ref<ReturnType<typeof getParsedApiError> | null>(null)
const submitting = ref(false)

async function onSubmit() {
  error.value = null
  submitting.value = true
  try {
    const needConfirm = auth.setupState === 'no_password'
    await auth.login(
      password.value,
      needConfirm ? passwordConfirm.value : undefined,
    )
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect || '/')
  } catch (e) {
    error.value = getParsedApiError(e)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background px-4 text-foreground">
    <div class="w-full max-w-md rounded-2xl border border-border bg-card p-8 shadow-lg">
      <h1 class="text-xl font-semibold">登录 DSA Web</h1>
      <p class="mt-2 text-sm text-secondary-text">请输入访问密码</p>
      <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
        <div v-if="error">
          <ApiErrorAlert :error="error" />
        </div>
        <label class="block text-sm font-medium text-secondary-text">
          密码
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="mt-1 w-full rounded-xl border border-input bg-background px-3 py-2 text-foreground outline-none ring-primary focus:ring-2"
            required
          />
        </label>
        <label v-if="auth.setupState === 'no_password'" class="block text-sm font-medium text-secondary-text">
          确认密码
          <input
            v-model="passwordConfirm"
            type="password"
            autocomplete="new-password"
            class="mt-1 w-full rounded-xl border border-input bg-background px-3 py-2 text-foreground outline-none ring-primary focus:ring-2"
            required
          />
        </label>
        <button
          type="submit"
          class="w-full rounded-xl bg-primary py-2.5 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
          :disabled="submitting"
        >
          {{ submitting ? '登录中…' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>
