<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { historyApi } from '@/api/history'
import type { NewsIntelItem } from '@/types/analysis'
import Loading from '@/components/common/Loading.vue'

const props = defineProps<{ queryId: string }>()

const items = ref<NewsIntelItem[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

async function load() {
  isLoading.value = true
  error.value = null
  try {
    const res = await historyApi.getNews(props.queryId)
    items.value = res.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-slate-700">相关新闻</h3>
      <button class="text-xs text-blue-600 hover:text-blue-700" @click="load">刷新</button>
    </div>

    <div v-if="isLoading" class="py-6">
      <Loading size="sm" label="加载中…" />
    </div>
    <div v-else-if="error" class="text-center py-4">
      <p class="text-sm text-red-500">{{ error }}</p>
      <button class="mt-2 text-xs text-blue-600 hover:underline" @click="load">重试</button>
    </div>
    <div v-else-if="items.length === 0" class="text-center py-4 text-sm text-slate-400">
      暂无新闻数据
    </div>
    <ul v-else class="space-y-2">
      <li
        v-for="item in items"
        :key="item.url"
        class="bg-slate-50 rounded-lg p-3 border border-slate-100 hover:border-slate-200 transition-colors"
      >
        <a
          :href="item.url"
          target="_blank"
          rel="noopener noreferrer"
          class="text-sm font-medium text-slate-800 hover:text-blue-600 flex items-start gap-1"
        >
          {{ item.title }}
          <svg class="h-3 w-3 mt-0.5 shrink-0 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
        <p v-if="item.snippet" class="text-xs text-slate-500 mt-1 line-clamp-2">{{ item.snippet }}</p>
      </li>
    </ul>
  </div>
</template>
