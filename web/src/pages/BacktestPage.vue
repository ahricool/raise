<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { backtestApi } from '@/api/backtest'
import type { BacktestResultItem, PerformanceMetrics } from '@/types/backtest'
import Loading from '@/components/common/Loading.vue'
import Pagination from '@/components/common/Pagination.vue'
import Badge from '@/components/common/Badge.vue'
import { formatPct, formatDate } from '@/utils/format'

const isRunning = ref(false)
const isLoading = ref(false)
const filterCode = ref('')
const evalWindow = ref(10)

const results = ref<BacktestResultItem[]>([])
const totalResults = ref(0)
const page = ref(1)
const totalPages = ref(1)

const overallMetrics = ref<PerformanceMetrics | null>(null)

async function loadResults() {
  isLoading.value = true
  try {
    const res = await backtestApi.getResults({
      code: filterCode.value || undefined,
      evalWindowDays: evalWindow.value,
      page: page.value,
      limit: 20,
    })
    results.value = res.items
    totalResults.value = res.total
    totalPages.value = res.totalPages
  } finally {
    isLoading.value = false
  }
}

async function loadMetrics() {
  overallMetrics.value = await backtestApi.getOverallPerformance(evalWindow.value)
}

async function runBacktest() {
  isRunning.value = true
  try {
    await backtestApi.run({ evalWindowDays: evalWindow.value, force: false })
    await Promise.all([loadResults(), loadMetrics()])
  } finally {
    isRunning.value = false
  }
}

function outcomeVariant(outcome?: string) {
  if (outcome === 'win') return 'success'
  if (outcome === 'loss') return 'danger'
  return 'default'
}

function statusVariant(status: string) {
  if (status === 'completed') return 'success'
  if (status === 'insufficient') return 'warning'
  return 'danger'
}

const metricCards = computed(() => {
  const m = overallMetrics.value
  if (!m) return []
  return [
    { label: '方向准确率', value: m.directionAccuracyPct != null ? `${m.directionAccuracyPct.toFixed(1)}%` : '-', sub: `${m.completedCount} 条有效` },
    { label: '胜率', value: m.winRatePct != null ? `${m.winRatePct.toFixed(1)}%` : '-', sub: `胜 ${m.winCount} / 负 ${m.lossCount}` },
    { label: '平均模拟收益', value: formatPct(m.avgSimulatedReturnPct), sub: `实际 ${formatPct(m.avgStockReturnPct)}` },
    { label: '止盈触发率', value: m.takeProfitTriggerRate != null ? `${m.takeProfitTriggerRate.toFixed(1)}%` : '-', sub: `止损 ${m.stopLossTriggerRate != null ? m.stopLossTriggerRate.toFixed(1) + '%' : '-'}` },
  ]
})

onMounted(async () => {
  await Promise.all([loadResults(), loadMetrics()])
})
</script>

<template>
  <div class="flex-1 overflow-y-auto p-6">
    <div class="max-w-5xl mx-auto space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-slate-900">回测评估</h1>
          <p class="text-sm text-slate-500 mt-0.5">评估历史分析预测的准确性</p>
        </div>
        <button
          :disabled="isRunning"
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
          @click="runBacktest"
        >
          <svg v-if="isRunning" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ isRunning ? '运行中…' : '运行回测' }}
        </button>
      </div>

      <!-- Metrics -->
      <div v-if="overallMetrics" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="card in metricCards" :key="card.label" class="bg-white rounded-xl border border-slate-200 p-4">
          <p class="text-xs text-slate-500">{{ card.label }}</p>
          <p class="text-2xl font-bold text-slate-900 mt-1">{{ card.value }}</p>
          <p class="text-xs text-slate-400 mt-0.5">{{ card.sub }}</p>
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-4 flex-wrap">
        <div class="flex items-center gap-2">
          <label class="text-sm text-slate-600">股票代码</label>
          <input
            v-model="filterCode"
            type="text"
            placeholder="留空查看全部"
            class="text-sm border border-slate-200 rounded-lg px-3 py-1.5 w-36 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm text-slate-600">评估窗口</label>
          <select
            v-model="evalWindow"
            class="text-sm border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option :value="5">5 天</option>
            <option :value="10">10 天</option>
            <option :value="20">20 天</option>
          </select>
        </div>
        <button
          class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm rounded-lg transition-colors"
          @click="page = 1; loadResults()"
        >查询</button>
      </div>

      <!-- Results table -->
      <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <span class="text-sm font-medium text-slate-700">回测结果</span>
          <span class="text-xs text-slate-400">共 {{ totalResults }} 条</span>
        </div>

        <div v-if="isLoading" class="py-12 flex justify-center">
          <Loading label="加载中…" />
        </div>
        <div v-else-if="results.length === 0" class="py-12 text-center text-sm text-slate-400">
          暂无数据
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-slate-50 border-b border-slate-100">
                <th class="text-left px-4 py-3 text-xs font-medium text-slate-500">股票</th>
                <th class="text-left px-4 py-3 text-xs font-medium text-slate-500">分析日期</th>
                <th class="text-left px-4 py-3 text-xs font-medium text-slate-500">操作建议</th>
                <th class="text-left px-4 py-3 text-xs font-medium text-slate-500">状态</th>
                <th class="text-right px-4 py-3 text-xs font-medium text-slate-500">方向</th>
                <th class="text-right px-4 py-3 text-xs font-medium text-slate-500">结果</th>
                <th class="text-right px-4 py-3 text-xs font-medium text-slate-500">模拟收益</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
              <tr
                v-for="item in results"
                :key="item.analysisHistoryId"
                class="hover:bg-slate-50 transition-colors"
              >
                <td class="px-4 py-3 font-mono text-slate-700">{{ item.code }}</td>
                <td class="px-4 py-3 text-slate-600">{{ item.analysisDate ? formatDate(item.analysisDate) : '-' }}</td>
                <td class="px-4 py-3">
                  <span class="text-slate-700">{{ item.operationAdvice || '-' }}</span>
                </td>
                <td class="px-4 py-3">
                  <Badge :variant="statusVariant(item.evalStatus)" size="sm">
                    {{ item.evalStatus === 'completed' ? '完成' : item.evalStatus === 'insufficient' ? '数据不足' : item.evalStatus }}
                  </Badge>
                </td>
                <td class="px-4 py-3 text-right">
                  <span v-if="item.directionCorrect != null" :class="item.directionCorrect ? 'text-green-600' : 'text-red-500'">
                    {{ item.directionCorrect ? '✓ 准确' : '✗ 偏差' }}
                  </span>
                  <span v-else class="text-slate-300">-</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <Badge v-if="item.outcome" :variant="outcomeVariant(item.outcome)" size="sm">
                    {{ item.outcome === 'win' ? '盈' : item.outcome === 'loss' ? '亏' : '平' }}
                  </Badge>
                  <span v-else class="text-slate-300">-</span>
                </td>
                <td class="px-4 py-3 text-right font-medium"
                  :class="item.simulatedReturnPct != null ? (item.simulatedReturnPct >= 0 ? 'text-green-600' : 'text-red-500') : 'text-slate-300'"
                >
                  {{ formatPct(item.simulatedReturnPct) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="px-4 py-3 border-t border-slate-100 flex justify-center">
          <Pagination v-model:page="page" :total-pages="totalPages" @update:page="loadResults" />
        </div>
      </div>
    </div>
  </div>
</template>
