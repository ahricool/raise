<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ page: number; totalPages: number }>()
const emit = defineEmits<{ (e: 'update:page', v: number): void }>()

const pages = computed(() => {
  const total = props.totalPages
  const cur = props.page
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 4) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 3) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})
</script>

<template>
  <div class="flex items-center gap-1">
    <button
      :disabled="page <= 1"
      class="px-2 py-1.5 text-sm rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      @click="emit('update:page', page - 1)"
    >
      ‹
    </button>
    <template v-for="p in pages" :key="p">
      <span v-if="p === '...'" class="px-2 text-slate-400 text-sm">…</span>
      <button
        v-else
        :class="[
          'min-w-[32px] py-1.5 text-sm rounded-lg border transition-colors',
          p === page
            ? 'bg-blue-600 border-blue-600 text-white'
            : 'border-slate-200 hover:bg-slate-50 text-slate-700',
        ]"
        @click="emit('update:page', p as number)"
      >{{ p }}</button>
    </template>
    <button
      :disabled="page >= totalPages"
      class="px-2 py-1.5 text-sm rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      @click="emit('update:page', page + 1)"
    >
      ›
    </button>
  </div>
</template>
