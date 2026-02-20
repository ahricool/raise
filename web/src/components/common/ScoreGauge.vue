<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score: number
  size?: 'sm' | 'md' | 'lg'
}>()

const dim = computed(() => props.size === 'sm' ? 72 : props.size === 'lg' ? 140 : 100)
const r = computed(() => dim.value * 0.38)
const cx = computed(() => dim.value / 2)
const cy = computed(() => dim.value / 2)
const circumference = computed(() => 2 * Math.PI * r.value)
// 3/4 arc
const arc = computed(() => circumference.value * 0.75)
const gap = computed(() => circumference.value * 0.25)
const filled = computed(() => (arc.value * props.score) / 100)
const empty = computed(() => arc.value - filled.value + gap.value)

const color = computed(() => {
  if (props.score >= 80) return '#16a34a'      // green-600
  if (props.score >= 60) return '#0891b2'      // cyan-600
  if (props.score >= 40) return '#2563eb'      // blue-600
  if (props.score >= 20) return '#d97706'      // amber-600
  return '#dc2626'                              // red-600
})

const label = computed(() => {
  if (props.score >= 80) return '看多'
  if (props.score >= 60) return '偏多'
  if (props.score >= 40) return '中性'
  if (props.score >= 20) return '偏空'
  return '看空'
})

const fontSize = computed(() => props.size === 'sm' ? 14 : props.size === 'lg' ? 28 : 20)
const subFontSize = computed(() => props.size === 'sm' ? 8 : props.size === 'lg' ? 14 : 11)
</script>

<template>
  <div class="flex flex-col items-center">
    <svg :width="dim" :height="dim" :viewBox="`0 0 ${dim} ${dim}`">
      <!-- Track -->
      <circle
        :cx="cx" :cy="cy" :r="r"
        fill="none"
        stroke="#e2e8f0"
        stroke-width="8"
        :stroke-dasharray="`${arc} ${gap}`"
        stroke-linecap="round"
        :transform="`rotate(135 ${cx} ${cy})`"
      />
      <!-- Fill -->
      <circle
        :cx="cx" :cy="cy" :r="r"
        fill="none"
        :stroke="color"
        stroke-width="8"
        :stroke-dasharray="`${filled} ${empty}`"
        stroke-linecap="round"
        :transform="`rotate(135 ${cx} ${cy})`"
        class="transition-all duration-500"
      />
      <!-- Score text -->
      <text
        :x="cx" :y="cy - 2"
        text-anchor="middle"
        dominant-baseline="middle"
        :font-size="fontSize"
        font-weight="700"
        :fill="color"
      >{{ score }}</text>
      <!-- Label -->
      <text
        :x="cx" :y="cy + fontSize * 0.85"
        text-anchor="middle"
        :font-size="subFontSize"
        fill="#64748b"
      >{{ label }}</text>
    </svg>
  </div>
</template>
