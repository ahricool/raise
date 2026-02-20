<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { analysisApi, DuplicateTaskError } from '@/api/analysis'
import { historyApi } from '@/api/history'
import { validateStockCode } from '@/utils/validation'
import { getRecentStartDate } from '@/utils/format'
import { useTaskStream } from '@/composables/useTaskStream'
import TaskPanel from '@/components/tasks/TaskPanel.vue'
import HistoryList from '@/components/history/HistoryList.vue'
import ReportSummary from '@/components/report/ReportSummary.vue'
import Loading from '@/components/common/Loading.vue'
import WatchlistPanel from '@/components/watchlist/WatchlistPanel.vue'
import type { HistoryItem, AnalysisReport, TaskInfo } from '@/types/analysis'

const stockCode = ref('')
const inputError = ref<string | null>(null)
const isAnalyzing = ref(false)
const analyzeError = ref<string | null>(null)

// Left panel tab
const leftTab = ref<'watchlist' | 'history'>('watchlist')

// History
const historyItems = ref<HistoryItem[]>([])
const selectedId = ref<string | undefined>(undefined)
const selectedReport = ref<AnalysisReport | null>(null)
const reportLoading = ref(false)
const historyPage = ref(1)
const historyTotal = ref(0)
const historyLoading = ref(false)

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
    loadHistory(true)
  },
  onTaskFailed(task) {
    activeTasks.value = activeTasks.value.filter((t) => t.taskId !== task.taskId)
  },
})

async function loadHistory(reset = false) {
  if (reset) {
    historyPage.value = 1
    historyItems.value = []
  }
  historyLoading.value = true
  try {
    const res = await historyApi.getList({
      startDate: getRecentStartDate(30),
      page: historyPage.value,
      limit: 30,
    })
    historyTotal.value = res.total
    if (reset) {
      historyItems.value = res.items
    } else {
      historyItems.value.push(...res.items)
    }
    if (reset && res.items.length > 0 && !selectedId.value) {
      selectHistory(res.items[0])
    }
  } finally {
    historyLoading.value = false
  }
}

async function loadMore() {
  historyPage.value++
  await loadHistory(false)
}

async function selectHistory(item: HistoryItem) {
  selectedId.value = item.queryId
  selectedReport.value = null
  reportLoading.value = true
  try {
    selectedReport.value = await historyApi.getDetail(item.queryId)
  } finally {
    reportLoading.value = false
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
    // Switch to history tab to show progress
    leftTab.value = 'history'
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
  await loadHistory(true)
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
          <div class="flex-1">
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
            <p v-if="inputError" class="text-xs text-red-500 mt-1">{{ inputError }}</p>
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
        <p v-if="analyzeError" class="text-xs text-red-500 mt-1.5">{{ analyzeError }}</p>
      </div>

      <!-- Active tasks -->
      <TaskPanel :tasks="activeTasks" />

      <!-- Tab switcher -->
      <div class="flex border-b border-slate-100 shrink-0">
        <button
          v-for="tab in (['watchlist', 'history'] as const)"
          :key="tab"
          :class="[
            'flex-1 py-2 text-xs font-medium transition-colors',
            leftTab === tab
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-slate-400 hover:text-slate-600',
          ]"
          @click="leftTab = tab"
        >
          {{ tab === 'watchlist' ? '自选股' : '历史记录' }}
        </button>
      </div>

      <!-- Tab content -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <!-- Watchlist tab -->
        <WatchlistPanel
          v-if="leftTab === 'watchlist'"
          @analyze="handleAnalyze"
        />

        <!-- History tab -->
        <template v-else>
          <div class="px-3 py-2 border-b border-slate-100">
            <span class="text-xs text-slate-400 font-medium">近30天</span>
          </div>
          <HistoryList
            :items="historyItems"
            :selected-id="selectedId"
            :has-more="historyItems.length < historyTotal"
            :loading="historyLoading"
            @select="selectHistory"
            @load-more="loadMore"
          />
        </template>
      </div>
    </div>

    <!-- Right panel: report -->
    <div class="flex-1 overflow-y-auto bg-slate-50">
      <div class="max-w-2xl mx-auto p-6">
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
          <p class="text-slate-500 text-sm">从左侧选择历史记录，或输入股票代码开始分析</p>
        </div>
      </div>
    </div>
  </div>
</template>
