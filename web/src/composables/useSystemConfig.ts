import { ref, computed, reactive } from 'vue'
import { systemConfigApi, SystemConfigValidationError, SystemConfigConflictError } from '@/api/systemConfig'
import type {
  SystemConfigItem,
  SystemConfigCategorySchema,
  ConfigValidationIssue,
  SystemConfigCategory,
} from '@/types/systemConfig'

interface ToastState {
  message: string
  type: 'success' | 'error' | 'warning'
}

export function useSystemConfig() {
  // Server state
  const configVersion = ref('')
  const serverItems = ref<SystemConfigItem[]>([])
  const categories = ref<SystemConfigCategorySchema[]>([])

  // Draft state
  const draftValues = reactive<Record<string, string>>({})

  // UI state
  const activeCategory = ref<SystemConfigCategory>('base')
  const toast = ref<ToastState | null>(null)

  // Request state
  const isLoading = ref(false)
  const isSaving = ref(false)
  const loadError = ref<string | null>(null)
  const saveError = ref<string | null>(null)
  const issueMap = ref<Record<string, ConfigValidationIssue[]>>({})

  // Computed
  const itemsByCategory = computed(() => {
    const result: Record<string, SystemConfigItem[]> = {}
    for (const cat of categories.value) {
      result[cat.category] = serverItems.value.filter(
        (item) => item.schema?.category === cat.category,
      )
    }
    return result
  })

  const hasDirty = computed(() => Object.keys(draftValues).length > 0)
  const dirtyCount = computed(() => Object.keys(draftValues).length)

  function setDraftValue(key: string, value: string) {
    const item = serverItems.value.find((i) => i.key === key)
    const serverValue = item?.value ?? ''
    if (value === serverValue) {
      delete draftValues[key]
    } else {
      draftValues[key] = value
    }
  }

  function resetDraft() {
    Object.keys(draftValues).forEach((k) => delete draftValues[k])
    issueMap.value = {}
  }

  function clearToast() {
    toast.value = null
  }

  async function load() {
    isLoading.value = true
    loadError.value = null
    try {
      const [configRes, schemaRes] = await Promise.all([
        systemConfigApi.getConfig(true),
        systemConfigApi.getSchema(),
      ])
      serverItems.value = configRes.items
      configVersion.value = configRes.configVersion
      categories.value = schemaRes.categories
      resetDraft()
    } catch (err) {
      loadError.value = err instanceof Error ? err.message : '加载失败'
    } finally {
      isLoading.value = false
    }
  }

  async function retry() {
    await load()
  }

  async function save(): Promise<{ success: boolean }> {
    isSaving.value = true
    saveError.value = null
    issueMap.value = {}
    try {
      const items = Object.entries(draftValues).map(([key, value]) => ({ key, value }))
      if (items.length === 0) return { success: true }

      const res = await systemConfigApi.update({ items, configVersion: configVersion.value })
      configVersion.value = res.configVersion

      // Apply drafts to serverItems
      for (const upd of items) {
        const item = serverItems.value.find((i) => i.key === upd.key)
        if (item) item.value = upd.value
      }
      resetDraft()
      toast.value = { message: '配置已保存', type: 'success' }
      return { success: true }
    } catch (err) {
      if (err instanceof SystemConfigValidationError) {
        const map: Record<string, ConfigValidationIssue[]> = {}
        for (const issue of err.issues) {
          if (!map[issue.key]) map[issue.key] = []
          map[issue.key].push(issue)
        }
        issueMap.value = map
        toast.value = { message: '配置验证失败，请检查错误项', type: 'error' }
      } else if (err instanceof SystemConfigConflictError) {
        toast.value = { message: '配置版本冲突，请刷新后重试', type: 'warning' }
      } else {
        saveError.value = err instanceof Error ? err.message : '保存失败'
        toast.value = { message: saveError.value, type: 'error' }
      }
      return { success: false }
    } finally {
      isSaving.value = false
    }
  }

  return {
    configVersion,
    serverItems,
    categories,
    itemsByCategory,
    issueByKey: issueMap,
    activeCategory,
    setActiveCategory: (cat: SystemConfigCategory) => { activeCategory.value = cat },
    hasDirty,
    dirtyCount,
    toast,
    clearToast,
    isLoading,
    isSaving,
    loadError,
    saveError,
    load,
    retry,
    save,
    resetDraft,
    setDraftValue,
    draftValues,
  }
}
