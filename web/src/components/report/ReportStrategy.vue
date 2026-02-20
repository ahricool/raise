<script setup lang="ts">
import type { ReportStrategy } from '@/types/analysis'
defineProps<{ strategy: ReportStrategy }>()

const points = [
  { key: 'idealBuy' as const, label: '理想买点', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' },
  { key: 'secondaryBuy' as const, label: '次级买点', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  { key: 'stopLoss' as const, label: '止损位', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
  { key: 'takeProfit' as const, label: '止盈位', color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200' },
]
</script>

<template>
  <div>
    <h3 class="text-sm font-semibold text-slate-700 mb-3">策略点位</h3>
    <div class="grid grid-cols-2 gap-3">
      <div
        v-for="p in points"
        :key="p.key"
        :class="['rounded-xl border p-3', p.bg, p.border]"
      >
        <p class="text-xs text-slate-500 mb-1">{{ p.label }}</p>
        <p :class="['text-base font-semibold', p.color]">
          {{ strategy[p.key] || '-' }}
        </p>
      </div>
    </div>
  </div>
</template>
