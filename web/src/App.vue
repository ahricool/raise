<script setup lang="ts">
import SidebarNav from '@/components/layout/SidebarNav.vue'
</script>

<template>
  <div class="flex h-screen bg-slate-50 overflow-hidden">
    <SidebarNav />
    <!-- Main content shifted right of sidebar -->
    <div class="flex flex-col flex-1 ml-16 overflow-hidden">
      <RouterView />
    </div>
  </div>
</template>
