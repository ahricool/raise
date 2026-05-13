<script setup lang="ts">
import { marked } from 'marked'
import { computed } from 'vue'

const props = defineProps<{
  source: string
}>()

marked.setOptions({ gfm: true, breaks: true })

const html = computed(() => marked.parse(props.source || '', { async: false }) as string)
</script>

<template>
  <div
    class="markdown-body max-w-none text-sm leading-relaxed text-foreground [&_a]:text-primary [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-muted [&_pre]:p-3"
    v-html="html"
  />
</template>
