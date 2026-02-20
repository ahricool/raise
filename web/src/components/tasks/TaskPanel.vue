<script setup lang="ts">
import type { TaskInfo } from '@/types/analysis'

defineProps<{ tasks: TaskInfo[] }>()
</script>

<template>
  <div v-if="tasks.length > 0" class="border-b border-slate-100">
    <div class="px-3 py-2 flex items-center gap-1.5">
      <svg class="animate-spin h-3.5 w-3.5 text-blue-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
      <span class="text-xs font-medium text-blue-600">进行中 {{ tasks.length }}</span>
    </div>
    <div class="max-h-36 overflow-y-auto">
      <div
        v-for="task in tasks"
        :key="task.taskId"
        class="px-3 py-2 border-b border-slate-50 last:border-0"
      >
        <div class="flex items-center justify-between gap-2">
          <span class="text-xs font-medium text-slate-700 truncate">{{ task.stockName || task.stockCode }}</span>
          <span class="text-xs text-slate-400 shrink-0">{{ task.status === 'processing' ? '分析中' : '等待中' }}</span>
        </div>
        <div v-if="task.message" class="text-xs text-slate-400 mt-0.5 truncate">{{ task.message }}</div>
      </div>
    </div>
  </div>
</template>
