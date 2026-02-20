<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import type { HistoryItem } from '@/types/analysis'
import { formatDateTime } from '@/utils/format'

const props = defineProps<{
  items: HistoryItem[]
  selectedId?: string
  hasMore: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'select', item: HistoryItem): void
  (e: 'load-more'): void
}>()

const bottomEl = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

function scoreColor(score?: number) {
  if (score == null) return 'bg-slate-300'
  if (score >= 70) return 'bg-green-500'
  if (score >= 50) return 'bg-blue-500'
  if (score >= 30) return 'bg-amber-500'
  return 'bg-red-500'
}

onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    if (entries[0]?.isIntersecting && props.hasMore && !props.loading) {
      emit('load-more')
    }
  })
  if (bottomEl.value) observer.observe(bottomEl.value)
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div class="flex flex-col">
    <div v-if="items.length === 0 && !loading" class="py-8 text-center text-sm text-slate-400">
      暂无记录
    </div>

    <button
      v-for="item in items"
      :key="item.queryId"
      :class="[
        'w-full text-left px-3 py-3 border-b border-slate-100 hover:bg-slate-50 transition-colors',
        selectedId === item.queryId ? 'bg-blue-50 border-l-2 border-l-blue-500' : '',
      ]"
      @click="emit('select', item)"
    >
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2 min-w-0">
          <span :class="['h-2 w-2 rounded-full shrink-0', scoreColor(item.sentimentScore)]" />
          <span class="font-medium text-sm text-slate-800 truncate">{{ item.stockName || item.stockCode }}</span>
          <span class="text-xs text-slate-400 font-mono shrink-0">{{ item.stockCode }}</span>
        </div>
        <span v-if="item.sentimentScore != null" class="text-xs font-semibold text-slate-600 shrink-0">
          {{ item.sentimentScore }}
        </span>
      </div>
      <div class="mt-0.5 flex items-center justify-between">
        <span v-if="item.operationAdvice" class="text-xs text-slate-500">{{ item.operationAdvice }}</span>
        <span class="text-xs text-slate-400 ml-auto">{{ formatDateTime(item.createdAt) }}</span>
      </div>
    </button>

    <div ref="bottomEl" class="py-2 text-center">
      <span v-if="loading" class="text-xs text-slate-400">加载中…</span>
      <span v-else-if="!hasMore && items.length > 0" class="text-xs text-slate-300">已加载全部</span>
    </div>
  </div>
</template>
