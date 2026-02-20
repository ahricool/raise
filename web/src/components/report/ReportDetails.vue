<script setup lang="ts">
import Collapsible from '@/components/common/Collapsible.vue'
import JsonViewer from '@/components/common/JsonViewer.vue'
import type { AnalysisReport } from '@/types/analysis'

defineProps<{ report: AnalysisReport }>()
</script>

<template>
  <div class="space-y-3">
    <h3 class="text-sm font-semibold text-slate-700">原始数据</h3>

    <div class="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-50 rounded-lg px-3 py-2 font-mono">
      <span>Query ID:</span>
      <span class="text-slate-600">{{ report.meta.queryId }}</span>
    </div>

    <Collapsible title="分析结果 JSON" :default-open="false">
      <JsonViewer v-if="report.details?.rawResult" :data="report.details.rawResult" />
      <p v-else class="text-sm text-slate-400">暂无原始结果</p>
    </Collapsible>

    <Collapsible title="上下文快照" :default-open="false">
      <JsonViewer v-if="report.details?.contextSnapshot" :data="report.details.contextSnapshot" />
      <p v-else class="text-sm text-slate-400">暂无上下文快照</p>
    </Collapsible>
  </div>
</template>
