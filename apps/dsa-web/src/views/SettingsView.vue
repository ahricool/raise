<script setup lang="ts">
import { WEB_BUILD_INFO } from '@/utils/constants'
</script>

<template>
  <div class="mx-auto max-w-xl space-y-4 rounded-2xl border border-border bg-card/60 p-8">
    <h1 class="text-lg font-semibold">系统设置</h1>
    <p class="text-sm leading-relaxed text-secondary-text">
      可视化配置编辑器（LLM 渠道、通知、导入等）正在从 React 迁移到 Vue。请暂时通过运行环境变量、<code class="rounded bg-muted px-1 py-0.5 text-xs">.env</code> 或
      <a class="text-primary underline" href="/docs" target="_blank" rel="noreferrer">OpenAPI /docs</a>
      维护配置；后端校验逻辑未变。
    </p>
    <div class="rounded-xl border border-border bg-background/80 p-4 text-xs text-muted-foreground">
      <p>WebUI 版本：{{ WEB_BUILD_INFO.version }}</p>
      <p class="mt-1">构建时间：{{ WEB_BUILD_INFO.buildTime }}</p>
    </div>
  </div>
</template>
