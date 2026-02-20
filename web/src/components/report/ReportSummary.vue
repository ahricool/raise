<script setup lang="ts">
import ReportOverview from './ReportOverview.vue'
import ReportStrategy from './ReportStrategy.vue'
import ReportNews from './ReportNews.vue'
import ReportDetails from './ReportDetails.vue'
import type { AnalysisReport } from '@/types/analysis'

defineProps<{ report: AnalysisReport }>()
</script>

<template>
  <div class="space-y-6">
    <ReportOverview :report="report" />
    <hr class="border-slate-100" />
    <ReportStrategy v-if="report.strategy" :strategy="report.strategy" />
    <hr class="border-slate-100" />
    <ReportNews :query-id="report.meta.queryId" />
    <hr class="border-slate-100" />
    <ReportDetails :report="report" />
  </div>
</template>
