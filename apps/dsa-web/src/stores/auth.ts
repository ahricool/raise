import { authApi, type AuthStatusResponse } from '@/api/auth'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getParsedApiError, type ParsedApiError } from '@/api/error'

export const useAuthStore = defineStore('auth', () => {
  const authEnabled = ref(false)
  const loggedIn = ref(false)
  const passwordSet = ref<boolean | undefined>(undefined)
  const passwordChangeable = ref<boolean | undefined>(undefined)
  const setupState = ref<AuthStatusResponse['setupState']>('no_password')
  const isLoading = ref(true)
  const loadError = ref<ParsedApiError | null>(null)

  const needsLogin = computed(() => authEnabled.value && !loggedIn.value)

  function applyStatus(data: AuthStatusResponse) {
    authEnabled.value = data.authEnabled
    loggedIn.value = data.loggedIn
    passwordSet.value = data.passwordSet
    passwordChangeable.value = data.passwordChangeable
    setupState.value = data.setupState
  }

  async function bootstrap() {
    isLoading.value = true
    loadError.value = null
    try {
      const data = await authApi.getStatus()
      applyStatus(data)
    } catch (e) {
      loadError.value = getParsedApiError(e)
    } finally {
      isLoading.value = false
    }
  }

  async function login(password: string, passwordConfirm?: string) {
    await authApi.login(password, passwordConfirm)
    await bootstrap()
  }

  async function logout() {
    await authApi.logout()
    await bootstrap()
  }

  return {
    authEnabled,
    loggedIn,
    passwordSet,
    passwordChangeable,
    setupState,
    isLoading,
    loadError,
    needsLogin,
    bootstrap,
    login,
    logout,
  }
})
