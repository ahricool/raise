<script setup lang="ts">
import { computed, ref } from 'vue'
const props = defineProps<{ data: unknown; maxHeight?: string }>()
const copied = ref(false)
const text = computed(() => JSON.stringify(props.data, null, 2))

function highlighted(json: string): string {
  return json
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        if (/^"/.test(match)) {
          return /:$/.test(match)
            ? `<span class="text-blue-700">${match}</span>`
            : `<span class="text-green-700">${match}</span>`
        }
        if (/true|false/.test(match)) return `<span class="text-amber-600">${match}</span>`
        if (/null/.test(match)) return `<span class="text-slate-400">${match}</span>`
        return `<span class="text-purple-700">${match}</span>`
      },
    )
}

async function copy() {
  await navigator.clipboard.writeText(text.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}
</script>

<template>
  <div class="relative bg-slate-50 rounded-lg border border-slate-200">
    <button
      class="absolute top-2 right-2 text-xs px-2 py-1 rounded bg-white border border-slate-200 text-slate-500 hover:text-slate-700 transition-colors"
      @click="copy"
    >{{ copied ? '已复制' : '复制' }}</button>
    <pre
      class="p-4 text-xs font-mono overflow-auto"
      :style="maxHeight ? `max-height: ${maxHeight}` : 'max-height: 300px'"
      v-html="highlighted(text)"
    />
  </div>
</template>
