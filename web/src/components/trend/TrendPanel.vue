<script setup lang="ts">
import { computed } from 'vue'
import type { HistoryItem } from '@/types/analysis'

const props = defineProps<{
  items: HistoryItem[]
  stockCode: string
  stockName?: string
}>()

const emit = defineEmits<{ close: [] }>()

// Last 30 days for this stock only, sorted ascending
const trendData = computed(() => {
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - 30)
  return [...props.items]
    .filter((item) => item.stockCode === props.stockCode && new Date(item.createdAt) >= cutoff)
    .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
})

const hasData = computed(() => trendData.value.length > 0)

// Stats
const scores = computed(() =>
  trendData.value.map((d) => d.sentimentScore ?? 0).filter((s) => s > 0),
)
const avgScore = computed(() =>
  scores.value.length ? Math.round(scores.value.reduce((a, b) => a + b, 0) / scores.value.length) : 0,
)
const maxScore = computed(() => (scores.value.length ? Math.max(...scores.value) : 0))
const minScore = computed(() => (scores.value.length ? Math.min(...scores.value) : 0))
const latestScore = computed(() => trendData.value.at(-1)?.sentimentScore ?? 0)

// SVG layout
const W = 560
const H = 180
const PX = 48
const PY = 16
const CW = W - PX * 2
const CH = H - PY * 2

function xPos(i: number, total: number) {
  return PX + (total <= 1 ? CW / 2 : (i / (total - 1)) * CW)
}
function yPos(score: number) {
  return PY + CH - (Math.max(0, Math.min(100, score)) / 100) * CH
}

const points = computed(() =>
  trendData.value.map((item, i) => ({
    x: xPos(i, trendData.value.length),
    y: yPos(item.sentimentScore ?? 0),
    score: item.sentimentScore,
    item,
  })),
)

const polyline = computed(() => points.value.map((p) => `${p.x},${p.y}`).join(' '))

// Filled area path
const areaPath = computed(() => {
  if (points.value.length < 2) return ''
  const pts = points.value
  const base = PY + CH
  return (
    `M ${pts[0].x},${base} ` +
    pts.map((p) => `L ${p.x},${p.y}`).join(' ') +
    ` L ${pts.at(-1)!.x},${base} Z`
  )
})

// Reference lines at 30, 50, 70
const refLines = [
  { y: yPos(70), label: '70', color: '#22c55e' },
  { y: yPos(50), label: '50', color: '#3b82f6' },
  { y: yPos(30), label: '30', color: '#f59e0b' },
]

// X-axis date labels (show at most 6)
const xLabels = computed(() => {
  const data = trendData.value
  if (data.length === 0) return []
  const step = Math.max(1, Math.floor(data.length / 5))
  return data
    .map((item, i) => ({ i, label: fmtDate(item.createdAt) }))
    .filter((_, i) => i % step === 0 || i === data.length - 1)
})

function fmtDate(s: string) {
  const d = new Date(s)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function fmtDateFull(s: string) {
  const d = new Date(s)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function scoreColor(score?: number) {
  if (score == null || score === 0) return '#94a3b8'
  if (score >= 70) return '#22c55e'
  if (score >= 50) return '#3b82f6'
  if (score >= 30) return '#f59e0b'
  return '#ef4444'
}

function scoreTextClass(score?: number) {
  if (score == null || score === 0) return 'text-slate-400'
  if (score >= 70) return 'text-green-600'
  if (score >= 50) return 'text-blue-600'
  if (score >= 30) return 'text-amber-600'
  return 'text-red-600'
}

function adviceBadgeClass(advice?: string) {
  if (!advice) return 'bg-slate-100 text-slate-500'
  if (advice.includes('买')) return 'bg-green-100 text-green-700'
  if (advice.includes('卖')) return 'bg-red-100 text-red-700'
  return 'bg-blue-100 text-blue-700'
}
</script>

<template>
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
    @click.self="emit('close')"
  >
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
        <div>
          <h2 class="text-base font-semibold text-slate-800">
            趋势分析
            <span class="text-slate-400 font-normal ml-1">{{ stockName || stockCode }}</span>
            <span class="text-slate-300 font-normal ml-1">{{ stockName ? `(${stockCode})` : '' }}</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">最近 30 天 · {{ trendData.length }} 条记录</p>
        </div>
        <button
          class="h-8 w-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          @click="emit('close')"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="overflow-y-auto flex-1 px-6 py-5 space-y-5">
        <!-- No data -->
        <div v-if="!hasData" class="flex flex-col items-center justify-center py-16 text-center">
          <p class="text-slate-400 text-sm">最近 30 天内暂无分析记录</p>
        </div>

        <template v-else>
          <!-- Score stat cards -->
          <div class="grid grid-cols-4 gap-3">
            <div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 text-center">
              <p class="text-xs text-slate-400 mb-1">最新评分</p>
              <p :class="['text-2xl font-bold', scoreTextClass(latestScore)]">{{ latestScore }}</p>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 text-center">
              <p class="text-xs text-slate-400 mb-1">平均评分</p>
              <p :class="['text-2xl font-bold', scoreTextClass(avgScore)]">{{ avgScore }}</p>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 text-center">
              <p class="text-xs text-slate-400 mb-1">最高评分</p>
              <p class="text-2xl font-bold text-green-600">{{ maxScore }}</p>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 text-center">
              <p class="text-xs text-slate-400 mb-1">最低评分</p>
              <p class="text-2xl font-bold text-red-500">{{ minScore }}</p>
            </div>
          </div>

          <!-- Score trend chart -->
          <div class="rounded-xl border border-slate-100 overflow-hidden">
            <div class="px-4 pt-3 pb-1">
              <p class="text-xs font-medium text-slate-600">情绪评分趋势</p>
            </div>
            <svg :viewBox="`0 0 ${W} ${H}`" class="w-full" style="height: 180px">
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.18" />
                  <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.01" />
                </linearGradient>
              </defs>

              <!-- Reference lines -->
              <g v-for="ref in refLines" :key="ref.label">
                <line
                  :x1="PX" :y1="ref.y" :x2="W - PX" :y2="ref.y"
                  :stroke="ref.color" stroke-width="1" stroke-dasharray="4,4" opacity="0.35"
                />
                <text :x="PX - 6" :y="ref.y + 4" text-anchor="end" font-size="10" :fill="ref.color" opacity="0.7">
                  {{ ref.label }}
                </text>
              </g>

              <!-- Area fill -->
              <path v-if="areaPath" :d="areaPath" fill="url(#areaGrad)" />

              <!-- Score line -->
              <polyline
                v-if="points.length >= 2"
                :points="polyline"
                fill="none"
                stroke="#3b82f6"
                stroke-width="2"
                stroke-linejoin="round"
                stroke-linecap="round"
              />

              <!-- Data points -->
              <g v-for="p in points" :key="p.item.queryId">
                <circle :cx="p.x" :cy="p.y" r="4" fill="white" :stroke="scoreColor(p.score)" stroke-width="2" />
              </g>

              <!-- X-axis labels -->
              <g v-for="lbl in xLabels" :key="lbl.i">
                <text
                  :x="xPos(lbl.i, trendData.length)"
                  :y="H - 2"
                  text-anchor="middle"
                  font-size="10"
                  fill="#94a3b8"
                >{{ lbl.label }}</text>
              </g>
            </svg>
          </div>

          <!-- Operation advice timeline -->
          <div class="rounded-xl border border-slate-100 overflow-hidden">
            <div class="px-4 pt-3 pb-1">
              <p class="text-xs font-medium text-slate-600">操作建议历程</p>
            </div>
            <div class="px-4 pb-4 pt-2">
              <div class="flex flex-wrap gap-2">
                <div
                  v-for="item in trendData"
                  :key="item.queryId"
                  class="flex flex-col items-center gap-1"
                >
                  <span
                    :class="['text-xs px-2 py-0.5 rounded-full font-medium', adviceBadgeClass(item.operationAdvice)]"
                  >
                    {{ item.operationAdvice || '—' }}
                  </span>
                  <span class="text-[10px] text-slate-400">{{ fmtDate(item.createdAt) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Score detail list -->
          <div class="rounded-xl border border-slate-100 overflow-hidden">
            <div class="px-4 pt-3 pb-1">
              <p class="text-xs font-medium text-slate-600">评分明细</p>
            </div>
            <div class="divide-y divide-slate-50">
              <div
                v-for="item in [...trendData].reverse()"
                :key="item.queryId"
                class="flex items-center justify-between px-4 py-2.5"
              >
                <span class="text-xs text-slate-500">{{ fmtDateFull(item.createdAt) }}</span>
                <div class="flex items-center gap-3">
                  <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', adviceBadgeClass(item.operationAdvice)]">
                    {{ item.operationAdvice || '—' }}
                  </span>
                  <div class="flex items-center gap-1.5">
                    <div class="h-1.5 w-16 rounded-full bg-slate-100 overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all"
                        :style="{ width: `${item.sentimentScore ?? 0}%`, background: scoreColor(item.sentimentScore) }"
                      />
                    </div>
                    <span :class="['text-xs font-semibold w-6 text-right', scoreTextClass(item.sentimentScore)]">
                      {{ item.sentimentScore ?? '—' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
