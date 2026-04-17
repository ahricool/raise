<script setup lang="ts">
import type { MultiAgentResult } from '@/types/analysis'

defineProps<{
  result: MultiAgentResult
}>()

function scoreColor(score: number): string {
  if (score >= 70) return 'text-green-600 bg-green-50 border-green-200'
  if (score >= 50) return 'text-blue-600 bg-blue-50 border-blue-200'
  if (score >= 30) return 'text-amber-600 bg-amber-50 border-amber-200'
  return 'text-red-600 bg-red-50 border-red-200'
}

function adviceColor(advice: string): string {
  if (advice.includes('买入') || advice.includes('加仓')) return 'bg-green-500 text-white'
  if (advice.includes('卖出') || advice.includes('减仓')) return 'bg-red-500 text-white'
  return 'bg-slate-500 text-white'
}

function debateSection(result: MultiAgentResult) {
  const db = result.dashboard as Record<string, unknown> | undefined
  return db?.debate as Record<string, string> | undefined
}
</script>

<template>
  <div class="space-y-4">
    <!-- 顶部摘要卡片 -->
    <div class="bg-white border border-slate-200 rounded-xl p-4">
      <div class="flex items-center gap-3 mb-3">
        <!-- 多智能体徽章 -->
        <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 border border-purple-200">
          多智能体辩论
        </span>
        <span class="text-sm font-semibold text-slate-800">{{ result.name }}（{{ result.code }}）</span>
      </div>

      <div class="flex items-center gap-3">
        <!-- 评分 -->
        <div
          :class="['text-2xl font-bold px-3 py-1.5 rounded-lg border', scoreColor(result.sentiment_score)]"
        >
          {{ result.sentiment_score }}
        </div>
        <!-- 操作建议 -->
        <span
          :class="['text-sm font-semibold px-3 py-1.5 rounded-lg', adviceColor(result.operation_advice)]"
        >
          {{ result.operation_advice }}
        </span>
        <!-- 趋势 -->
        <span class="text-sm text-slate-500">{{ result.trend_prediction }}</span>
        <!-- 置信度 -->
        <span class="ml-auto text-xs text-slate-400 border border-slate-200 px-2 py-0.5 rounded">
          置信度: {{ result.confidence_level }}
        </span>
      </div>

      <!-- 综合摘要 -->
      <p v-if="result.analysis_summary" class="mt-3 text-xs text-slate-600 leading-relaxed line-clamp-4">
        {{ result.analysis_summary }}
      </p>
    </div>

    <!-- 辩论详情（可折叠） -->
    <div v-if="debateSection(result)" class="bg-white border border-slate-200 rounded-xl overflow-hidden">
      <details>
        <summary class="px-4 py-3 text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-50 flex items-center gap-2">
          <svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
          </svg>
          辩论详情
        </summary>

        <div class="border-t border-slate-100 divide-y divide-slate-100">
          <!-- 多空辩论 -->
          <div v-if="debateSection(result)?.bull_case" class="px-4 py-3">
            <p class="text-xs font-semibold text-green-600 mb-1">多方论据</p>
            <p class="text-xs text-slate-600 leading-relaxed">{{ debateSection(result)?.bull_case }}</p>
          </div>
          <div v-if="debateSection(result)?.bear_case" class="px-4 py-3">
            <p class="text-xs font-semibold text-red-500 mb-1">空方论据</p>
            <p class="text-xs text-slate-600 leading-relaxed">{{ debateSection(result)?.bear_case }}</p>
          </div>

          <!-- 交易员 -->
          <div v-if="debateSection(result)?.trader_view" class="px-4 py-3">
            <p class="text-xs font-semibold text-slate-500 mb-1">交易员观点</p>
            <p class="text-xs text-slate-600 leading-relaxed">{{ debateSection(result)?.trader_view }}</p>
          </div>

          <!-- 风控三方 -->
          <div class="px-4 py-3 grid grid-cols-3 gap-3">
            <div v-if="debateSection(result)?.risk_aggressive">
              <p class="text-xs font-semibold text-orange-500 mb-1">激进风控</p>
              <p class="text-xs text-slate-500 leading-relaxed">{{ debateSection(result)?.risk_aggressive }}</p>
            </div>
            <div v-if="debateSection(result)?.risk_conservative">
              <p class="text-xs font-semibold text-blue-500 mb-1">保守风控</p>
              <p class="text-xs text-slate-500 leading-relaxed">{{ debateSection(result)?.risk_conservative }}</p>
            </div>
            <div v-if="debateSection(result)?.risk_neutral">
              <p class="text-xs font-semibold text-slate-400 mb-1">中立风控</p>
              <p class="text-xs text-slate-500 leading-relaxed">{{ debateSection(result)?.risk_neutral }}</p>
            </div>
          </div>

          <!-- 最终裁决 -->
          <div v-if="debateSection(result)?.['final_decision'] || (result.dashboard as any)?.final_decision" class="px-4 py-3 bg-slate-50">
            <p class="text-xs font-semibold text-purple-600 mb-1">投资组合经理最终裁决</p>
            <p class="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
              {{ (result.dashboard as any)?.final_decision ?? debateSection(result)?.['final_decision'] }}
            </p>
          </div>
        </div>
      </details>
    </div>

    <!-- 技术面 -->
    <div v-if="result.technical_analysis" class="bg-white border border-slate-200 rounded-xl p-4">
      <p class="text-xs font-semibold text-slate-500 mb-2">技术面分析</p>
      <p class="text-xs text-slate-600 leading-relaxed whitespace-pre-line">{{ result.technical_analysis }}</p>
    </div>

    <!-- 风险提示 -->
    <div v-if="result.risk_warning" class="bg-amber-50 border border-amber-200 rounded-xl p-4">
      <p class="text-xs font-semibold text-amber-700 mb-1">风险提示</p>
      <p class="text-xs text-amber-800 leading-relaxed">{{ result.risk_warning }}</p>
    </div>
  </div>
</template>
