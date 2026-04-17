<script setup lang="ts">
import type { AgentStepStatus } from '@/composables/useMultiAgent'

defineProps<{
  steps: AgentStepStatus[]
  currentStep: number
  totalSteps: number
  isRunning: boolean
}>()
</script>

<template>
  <div class="bg-white border border-slate-200 rounded-xl p-4">
    <!-- 标题 + 进度条 -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm font-semibold text-slate-700">多智能体辩论进度</span>
      <span class="text-xs text-slate-400">{{ currentStep }} / {{ totalSteps }}</span>
    </div>

    <!-- 总进度条 -->
    <div class="h-1.5 bg-slate-100 rounded-full mb-4 overflow-hidden">
      <div
        class="h-full bg-blue-500 rounded-full transition-all duration-500"
        :style="{ width: `${totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0}%` }"
      />
    </div>

    <!-- Agent 步骤列表 -->
    <div class="space-y-1.5">
      <div
        v-for="step in steps"
        :key="step.node"
        class="flex items-center gap-2.5"
      >
        <!-- 状态图标 -->
        <div class="shrink-0 w-5 h-5 flex items-center justify-center">
          <!-- 待执行 -->
          <div
            v-if="step.status === 'pending'"
            class="w-2 h-2 rounded-full bg-slate-200"
          />
          <!-- 执行中 -->
          <svg
            v-else-if="step.status === 'running'"
            class="animate-spin h-4 w-4 text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <!-- 完成 -->
          <svg
            v-else-if="step.status === 'completed'"
            class="h-4 w-4 text-green-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
          <!-- 错误 -->
          <svg
            v-else-if="step.status === 'error'"
            class="h-4 w-4 text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>

        <!-- 节点名称 -->
        <span
          :class="[
            'text-xs',
            step.status === 'running'   ? 'text-blue-600 font-medium' :
            step.status === 'completed' ? 'text-green-600' :
            step.status === 'error'     ? 'text-red-500' :
            'text-slate-400',
          ]"
        >
          {{ step.label }}
        </span>

        <!-- 执行中动点 -->
        <span v-if="step.status === 'running'" class="text-xs text-blue-400 animate-pulse">分析中…</span>
      </div>
    </div>
  </div>
</template>
