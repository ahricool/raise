<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { watchlistApi } from '@/api/watchlist'
import { formatDateTime } from '@/utils/format'
import type { WatchlistItem, StockSearchResult } from '@/types/watchlist'
import type { HistoryItem } from '@/types/analysis'
import Loading from '@/components/common/Loading.vue'

const props = defineProps<{
  latestHistory: Record<string, HistoryItem>
  selectedCode?: string
}>()

const emit = defineEmits<{
  (e: 'select', code: string, name: string): void
  (e: 'analyze', code: string): void
}>()

// ── 列表 ─────────────────────────────────────────────────────────────────
const items = ref<WatchlistItem[]>([])
const listLoading = ref(false)
const listError = ref<string | null>(null)

async function loadList() {
  listLoading.value = true
  listError.value = null
  try {
    const res = await watchlistApi.list()
    items.value = res.items
  } catch {
    listError.value = '加载失败'
  } finally {
    listLoading.value = false
  }
}

// ── 删除 ─────────────────────────────────────────────────────────────────
const deletingId = ref<number | null>(null)

async function handleRemove(item: WatchlistItem) {
  deletingId.value = item.id
  try {
    await watchlistApi.remove(item.id)
    items.value = items.value.filter((i) => i.id !== item.id)
  } finally {
    deletingId.value = null
  }
}

// ── 评分颜色 ──────────────────────────────────────────────────────────────
function scoreColor(score?: number) {
  if (score == null) return 'bg-slate-300'
  if (score >= 70) return 'bg-green-500'
  if (score >= 50) return 'bg-blue-500'
  if (score >= 30) return 'bg-amber-500'
  return 'bg-red-500'
}

// ── 搜索并添加 ────────────────────────────────────────────────────────────
const showAddPanel = ref(false)
const searchQuery = ref('')
const searchResults = ref<StockSearchResult[]>([])
const searchLoading = ref(false)
const searchError = ref<string | null>(null)
const addingCode = ref<string | null>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) { searchResults.value = []; return }
  searchLoading.value = true
  searchError.value = null
  try {
    const res = await watchlistApi.search(q)
    searchResults.value = res.results
    if (res.results.length === 0) searchError.value = '未找到匹配股票'
  } catch {
    searchError.value = '搜索失败'
  } finally {
    searchLoading.value = false
  }
}

function onInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(doSearch, 400)
}

async function confirmAdd(result: StockSearchResult) {
  addingCode.value = result.stockCode
  try {
    const added = await watchlistApi.add(result.stockCode, result.stockName)
    if (!items.value.find((i) => i.id === added.id)) {
      items.value.unshift(added)
    }
    searchQuery.value = ''
    searchResults.value = []
    showAddPanel.value = false
  } finally {
    addingCode.value = null
  }
}

function cancelAdd() {
  showAddPanel.value = false
  searchQuery.value = ''
  searchResults.value = []
  searchError.value = null
}

onMounted(loadList)
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Add panel (search) -->
    <div v-if="showAddPanel" class="border-b border-slate-100 bg-blue-50/50">
      <div class="px-3 pt-2.5 pb-1">
        <div class="flex gap-2">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="输入代码或名称，如 600519 / 茅台"
            class="flex-1 text-xs px-2.5 py-2 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            @input="onInput"
            @keydown.enter="doSearch"
            @keydown.escape="cancelAdd"
          />
          <button class="text-xs text-slate-400 hover:text-slate-600 px-1" @click="cancelAdd">✕</button>
        </div>
      </div>

      <!-- Search results -->
      <div class="max-h-48 overflow-y-auto px-3 pb-2">
        <div v-if="searchLoading" class="py-3 flex justify-center">
          <Loading size="sm" />
        </div>
        <p v-else-if="searchError" class="text-xs text-slate-400 py-2 text-center">{{ searchError }}</p>
        <div v-else class="space-y-1 mt-1">
          <button
            v-for="r in searchResults"
            :key="r.stockCode"
            :disabled="addingCode === r.stockCode"
            class="w-full flex items-center justify-between px-2.5 py-2 rounded-lg bg-white hover:bg-blue-50 border border-transparent hover:border-blue-200 transition-all text-left disabled:opacity-50"
            @click="confirmAdd(r)"
          >
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono text-slate-500">{{ r.stockCode }}</span>
              <span class="text-sm font-medium text-slate-800">{{ r.stockName }}</span>
              <span v-if="r.market" class="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">{{ r.market }}</span>
            </div>
            <svg
              v-if="addingCode === r.stockCode"
              class="animate-spin h-3.5 w-3.5 text-blue-500 shrink-0"
              fill="none" viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <svg v-else class="h-3.5 w-3.5 text-blue-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- List -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="listLoading" class="py-6 flex justify-center">
        <Loading size="sm" />
      </div>
      <p v-else-if="listError" class="text-xs text-slate-400 text-center py-4">{{ listError }}</p>
      <p v-else-if="items.length === 0" class="text-xs text-slate-400 text-center py-6">
        暂无自选股
      </p>
      <div v-else>
        <div
          v-for="item in items"
          :key="item.id"
          :class="[
            'group px-3 py-3 border-b border-slate-100 cursor-pointer transition-colors',
            props.selectedCode === item.stockCode
              ? 'bg-blue-50 border-l-2 border-l-blue-500'
              : 'hover:bg-slate-50',
          ]"
          @click="emit('select', item.stockCode, item.stockName || item.stockCode)"
        >
          <!-- Row 1: dot + name + code | score + actions -->
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
              <span
                :class="['h-2 w-2 rounded-full shrink-0', scoreColor(props.latestHistory[item.stockCode]?.sentimentScore)]"
              />
              <span class="font-medium text-sm text-slate-800 truncate">{{ item.stockName || item.stockCode }}</span>
              <span class="text-xs text-slate-400 font-mono shrink-0">{{ item.stockCode }}</span>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <span class="text-xs font-semibold text-slate-600">
                {{ props.latestHistory[item.stockCode]?.sentimentScore ?? '-' }}
              </span>
              <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                <button
                  class="px-2 py-1 rounded-md text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 border border-transparent hover:border-blue-200"
                  @click.stop="emit('analyze', item.stockCode)"
                >
                  分析
                </button>
                <button
                  :disabled="deletingId === item.id"
                  class="text-slate-300 hover:text-red-400 transition-all disabled:cursor-not-allowed"
                  title="从自选股移除"
                  @click.stop="handleRemove(item)"
                >
                  <svg
                    v-if="deletingId === item.id"
                    class="animate-spin h-4 w-4"
                    fill="none" viewBox="0 0 24 24"
                  >
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                  </svg>
                  <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <!-- Row 2: advice + date -->
          <div class="mt-0.5 flex items-center justify-between">
            <span class="text-xs text-slate-500">{{ props.latestHistory[item.stockCode]?.operationAdvice ?? '-' }}</span>
            <span class="text-xs text-slate-400">
              {{ props.latestHistory[item.stockCode] ? formatDateTime(props.latestHistory[item.stockCode].createdAt) : '-' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Add button (bottom) -->
    <div class="shrink-0 border-t border-slate-100 px-3 py-2.5">
      <button
        class="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium text-blue-600 hover:bg-blue-50 transition-colors"
        @click="showAddPanel = !showAddPanel"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        添加自选股
      </button>
    </div>
  </div>
</template>
