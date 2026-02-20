<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { watchlistApi } from '@/api/watchlist'
import type { WatchlistItem, StockSearchResult } from '@/types/watchlist'
import Loading from '@/components/common/Loading.vue'

const emit = defineEmits<{
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
    <!-- Header -->
    <div class="px-3 py-2.5 border-b border-slate-100 flex items-center justify-between">
      <span class="text-xs font-semibold text-slate-600 uppercase tracking-wide">自选股</span>
      <button
        class="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
        @click="showAddPanel = !showAddPanel"
      >
        <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        添加
      </button>
    </div>

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
        暂无自选股，点击右上角 + 添加
      </p>
      <div v-else>
        <div
          v-for="item in items"
          :key="item.id"
          class="group flex items-center justify-between px-3 py-2.5 border-b border-slate-50 hover:bg-slate-50 transition-colors"
        >
          <!-- 点击触发分析 -->
          <button
            class="flex items-center gap-2 min-w-0 flex-1 text-left"
            @click="emit('analyze', item.stockCode)"
          >
            <div class="min-w-0">
              <p class="text-sm font-medium text-slate-800 truncate">
                {{ item.stockName || item.stockCode }}
              </p>
              <p class="text-xs text-slate-400 font-mono">{{ item.stockCode }}</p>
            </div>
          </button>

          <!-- 删除按钮（hover 时显示） -->
          <button
            :disabled="deletingId === item.id"
            class="ml-2 shrink-0 opacity-0 group-hover:opacity-100 text-slate-300 hover:text-red-400 transition-all disabled:cursor-not-allowed"
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
  </div>
</template>
