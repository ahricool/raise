import { onMounted, ref, watch } from 'vue'

const STORAGE_KEY = 'theme'

function readTheme(): 'light' | 'dark' {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') {
    return stored
  }
  return 'dark'
}

function applyTheme(value: 'light' | 'dark') {
  const root = document.documentElement
  root.classList.remove('light', 'dark')
  root.classList.add(value)
  root.style.colorScheme = value
}

export function useTheme() {
  const theme = ref<'light' | 'dark'>('dark')

  onMounted(() => {
    theme.value = readTheme()
    applyTheme(theme.value)
  })

  watch(theme, (v) => {
    localStorage.setItem(STORAGE_KEY, v)
    applyTheme(v)
  })

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  return { theme, toggle }
}
