import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AnalysisReport } from '@/types/analysis'

export const useAnalysisStore = defineStore('analysis', () => {
  const isLoading = ref(false)
  const result = ref<AnalysisReport | null>(null)
  const error = ref<string | null>(null)
  const historyReport = ref<AnalysisReport | null>(null)

  function setLoading(v: boolean) { isLoading.value = v }
  function setResult(v: AnalysisReport | null) { result.value = v }
  function setError(v: string | null) { error.value = v }
  function setHistoryReport(v: AnalysisReport | null) { historyReport.value = v }

  function reset() {
    isLoading.value = false
    result.value = null
    error.value = null
    historyReport.value = null
  }

  return { isLoading, result, error, historyReport, setLoading, setResult, setError, setHistoryReport, reset }
})
