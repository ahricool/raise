<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{ title: string; defaultOpen?: boolean }>()
const open = ref(props.defaultOpen ?? false)
</script>

<template>
  <div class="border border-slate-200 rounded-lg overflow-hidden">
    <button
      class="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 transition-colors"
      @click="open = !open"
    >
      <span>{{ title }}</span>
      <svg
        :class="['h-4 w-4 text-slate-400 transition-transform', open ? 'rotate-180' : '']"
        fill="none" viewBox="0 0 24 24" stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    <div v-if="open" class="p-4 bg-white">
      <slot />
    </div>
  </div>
</template>
