<script setup lang="ts">
import { computed } from 'vue'
import Badge from '@/components/common/Badge.vue'
import ScoreGauge from '@/components/common/ScoreGauge.vue'
import type { AnalysisReport } from '@/types/analysis'

const props = defineProps<{ report: AnalysisReport }>()

const meta = computed(() => props.report.meta)
const summary = computed(() => props.report.summary)

const adviceVariant = computed(() => {
  const a = summary.value.operationAdvice
  if (a?.includes('买入')) return 'success'
  if (a?.includes('卖出')) return 'danger'
  return 'warning'
})

const changePctColor = computed(() => {
  const v = meta.value.changePct
  if (v == null) return 'text-slate-600'
  return v >= 0 ? 'text-red-600' : 'text-green-600'
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-start justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 flex-wrap">
          <h2 class="text-xl font-bold text-slate-900">{{ meta.stockName }}</h2>
          <span class="text-sm text-slate-500 font-mono">{{ meta.stockCode }}</span>
          <Badge variant="blue">{{ meta.reportType === 'simple' ? '普通' : '标准' }}</Badge>
        </div>
        <div class="mt-2 flex items-center gap-3">
          <span v-if="meta.currentPrice" class="text-2xl font-bold text-slate-900">
            {{ meta.currentPrice.toFixed(2) }}
          </span>
          <span v-if="meta.changePct != null" :class="['text-sm font-medium', changePctColor]">
            {{ meta.changePct >= 0 ? '+' : '' }}{{ meta.changePct.toFixed(2) }}%
          </span>
        </div>
      </div>
      <ScoreGauge :score="summary.sentimentScore" size="md" />
    </div>

    <!-- Analysis summary -->
    <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
      <p class="text-sm text-slate-700 leading-relaxed">{{ summary.analysisSummary }}</p>
    </div>

    <!-- Key cards -->
    <div class="grid grid-cols-2 gap-3">
      <div class="bg-white rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500 mb-1">操作建议</p>
        <Badge :variant="adviceVariant" size="md">{{ summary.operationAdvice }}</Badge>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3">
        <p class="text-xs text-slate-500 mb-1">趋势预判</p>
        <p class="text-sm font-medium text-slate-800">{{ summary.trendPrediction }}</p>
      </div>
    </div>
  </div>
</template>
