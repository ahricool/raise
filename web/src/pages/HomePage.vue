<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { analysisApi, DuplicateTaskError } from '@/api/analysis'
import { historyApi } from '@/api/history'
import { validateStockCode } from '@/utils/validation'
import { getRecentStartDate } from '@/utils/format'
import { useTaskStream } from '@/composables/useTaskStream'
import TaskPanel from '@/components/tasks/TaskPanel.vue'
import ReportSummary from '@/components/report/ReportSummary.vue'
import Loading from '@/components/common/Loading.vue'
import WatchlistPanel from '@/components/watchlist/WatchlistPanel.vue'
import type { HistoryItem, AnalysisReport, TaskInfo } from '@/types/analysis'

const stockCode = ref('')
const inputError = ref<string | null>(null)
const isAnalyzing = ref(false)
const analyzeError = ref<string | null>(null)

// Watchlist + latest history map
const latestHistoryMap = ref<Record<string, HistoryItem>>({})

// Chip shown in input area when a watchlist stock is selected
const chipStock = ref<{ code: string; name: string } | null>(null)

function chipColor(code: string) {
  const score = latestHistoryMap.value[code]?.sentimentScore
  if (score == null) return 'border-blue-400 text-blue-600 bg-blue-50'
  if (score >= 70) return 'border-green-500 text-green-700 bg-green-50'
  if (score >= 50) return 'border-blue-500 text-blue-700 bg-blue-50'
  if (score >= 30) return 'border-amber-500 text-amber-700 bg-amber-50'
  return 'border-red-500 text-red-700 bg-red-50'
}

// Current stock history navigation
const selectedStockCode = ref<string | undefined>(undefined)
const stockHistory = ref<HistoryItem[]>([])
const historyIndex = ref(0)
const reportLoading = ref(false)
const selectedReport = ref<AnalysisReport | null>(null)

// Active tasks
const activeTasks = ref<TaskInfo[]>([])

// SSE stream
useTaskStream({
  onTaskCreated(task) {
    if (!activeTasks.value.find((t) => t.taskId === task.taskId)) {
      activeTasks.value.unshift(task)
    }
  },
  onTaskStarted(task) {
    const idx = activeTasks.value.findIndex((t) => t.taskId === task.taskId)
    if (idx >= 0) activeTasks.value[idx] = task
    else activeTasks.value.unshift(task)
  },
  onTaskCompleted(task) {
    activeTasks.value = activeTasks.value.filter((t) => t.taskId !== task.taskId)
    loadLatestHistoryMap()
    if (selectedStockCode.value === task.stockCode) {
      handleWatchlistSelect(task.stockCode)
    }
  },
  onTaskFailed(task) {
    activeTasks.value = activeTasks.value.filter((t) => t.taskId !== task.taskId)
  },
})

async function loadLatestHistoryMap() {
  const res = await historyApi.getList({ startDate: getRecentStartDate(60), limit: 500 })
  const map: Record<string, HistoryItem> = {}
  for (const item of res.items) {
    if (!map[item.stockCode]) map[item.stockCode] = item // desc order, first = newest
  }
  latestHistoryMap.value = map
}

async function handleWatchlistSelect(code: string, name?: string) {
  selectedStockCode.value = code
  const displayName = name ?? latestHistoryMap.value[code]?.stockName ?? code
  chipStock.value = { code, name: displayName }
  stockCode.value = code
  stockHistory.value = []
  historyIndex.value = 0
  selectedReport.value = null
  const res = await historyApi.getList({ stockCode: code, limit: 100 })
  stockHistory.value = res.items
  if (res.items.length > 0) await loadReport(res.items[0])
}

async function loadReport(item: HistoryItem) {
  reportLoading.value = true
  selectedReport.value = null
  try {
    selectedReport.value = await historyApi.getDetail(item.queryId)
  } finally {
    reportLoading.value = false
  }
}

function navOlder() {
  if (historyIndex.value < stockHistory.value.length - 1) {
    historyIndex.value++
    loadReport(stockHistory.value[historyIndex.value])
  }
}

function navNewer() {
  if (historyIndex.value > 0) {
    historyIndex.value--
    loadReport(stockHistory.value[historyIndex.value])
  }
}

function validateInput() {
  inputError.value = validateStockCode(stockCode.value)
  return !inputError.value
}

async function handleAnalyze(code?: string) {
  if (code) {
    stockCode.value = code
  }
  if (!validateInput()) return
  isAnalyzing.value = true
  analyzeError.value = null
  try {
    await analysisApi.analyzeAsync({
      stockCode: stockCode.value.trim().toUpperCase(),
      reportType: 'simple',
      asyncMode: true,
    })
    stockCode.value = ''
    chipStock.value = null
  } catch (err) {
    if (err instanceof DuplicateTaskError) {
      analyzeError.value = `${err.stockCode} 已在分析队列中`
    } else {
      analyzeError.value = err instanceof Error ? err.message : '提交失败'
    }
  } finally {
    isAnalyzing.value = false
  }
}

onMounted(async () => {
  await loadLatestHistoryMap()
  try {
    const res = await analysisApi.getTasks({ status: 'active', limit: 20 })
    activeTasks.value = res.tasks.filter((t) => t.status === 'pending' || t.status === 'processing')
  } catch { /* ignore */ }
})
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <!-- Left panel -->
    <div class="w-72 bg-white border-r border-slate-200 flex flex-col shrink-0">
      <!-- Input area -->
      <div class="p-4 border-b border-slate-100">
        <h1 class="text-sm font-semibold text-slate-800 mb-3">股票分析</h1>
        <div class="flex gap-2">
          <!-- Stock chip (when selected from watchlist) -->
          <div v-if="chipStock" class="flex-1 flex items-center">
            <span
              :class="[
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm font-medium flex-1',
                chipColor(chipStock.code),
              ]"
            >
              <span class="truncate">{{ chipStock.name }}（{{ chipStock.code }}）</span>
              <button
                class="shrink-0 opacity-60 hover:opacity-100 transition-opacity ml-auto"
                @click="chipStock = null; stockCode = ''"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          </div>
          <!-- Text input (default) -->
          <div v-else class="flex-1">
            <input
              v-model="stockCode"
              type="text"
              placeholder="股票代码 (如 600519)"
              :class="[
                'w-full text-sm px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500',
                inputError ? 'border-red-300 bg-red-50' : 'border-slate-200 bg-white',
              ]"
              @keydown.enter="handleAnalyze()"
              @input="inputError = null"
            />
          </div>
          <button
            :disabled="isAnalyzing"
            class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors flex items-center gap-1.5"
            @click="handleAnalyze()"
          >
            <svg v-if="isAnalyzing" class="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <span>{{ isAnalyzing ? '…' : '分析' }}</span>
          </button>
        </div>
        <p v-if="inputError && !chipStock" class="text-xs text-red-500 mt-1">{{ inputError }}</p>
        <p v-if="analyzeError" class="text-xs text-red-500 mt-1.5">{{ analyzeError }}</p>
      </div>

      <!-- Active tasks -->
      <TaskPanel :tasks="activeTasks" />

      <!-- Watchlist -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <WatchlistPanel
          :latest-history="latestHistoryMap"
          :selected-code="selectedStockCode"
          @select="handleWatchlistSelect"
        />
      </div>
    </div>

    <!-- Right panel: report -->
    <div class="flex-1 overflow-y-auto bg-slate-50">
      <div class="max-w-2xl mx-auto p-6">
        <!-- History navigation -->
        <div
          v-if="stockHistory.length > 0"
          class="flex items-center justify-between mb-4 bg-white border border-slate-200 rounded-xl px-4 py-2.5"
        >
          <button
            :disabled="historyIndex >= stockHistory.length - 1"
            class="text-sm text-slate-500 hover:text-slate-800 disabled:opacity-30 flex items-center gap-1"
            @click="navOlder"
          >
            ← 上一条
          </button>
          <span class="text-xs text-slate-400">
            第 {{ historyIndex + 1 }} / {{ stockHistory.length }} 条
          </span>
          <button
            :disabled="historyIndex <= 0"
            class="text-sm text-slate-500 hover:text-slate-800 disabled:opacity-30 flex items-center gap-1"
            @click="navNewer"
          >
            下一条 →
          </button>
        </div>

        <div v-if="reportLoading" class="flex items-center justify-center py-20">
          <Loading size="lg" label="加载报告中…" />
        </div>
        <div v-else-if="selectedReport">
          <ReportSummary :report="selectedReport" />
        </div>
        <div v-else class="flex flex-col items-center justify-center py-24 text-center">
          <div class="h-16 w-16 rounded-2xl bg-slate-200 flex items-center justify-center mb-4">
            <svg class="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p class="text-slate-500 text-sm">从左侧自选股选择股票查看分析记录</p>
        </div>
      </div>
    </div>
  </div>
</template>
