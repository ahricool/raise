<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="flex flex-col items-center justify-center py-24 text-center">
    <p class="text-6xl font-bold text-muted-foreground">404</p>
    <p class="mt-2 text-secondary-text">页面不存在</p>
    <RouterLink to="/" class="mt-6 text-sm font-medium text-primary hover:underline">返回首页</RouterLink>
  </div>
</template>
