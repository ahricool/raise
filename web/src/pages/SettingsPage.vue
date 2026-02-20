<script setup lang="ts">
import { onMounted, computed, watch } from 'vue'
import { useSystemConfig } from '@/composables/useSystemConfig'
import SettingsField from '@/components/settings/SettingsField.vue'
import SettingsAlert from '@/components/settings/SettingsAlert.vue'
import Loading from '@/components/common/Loading.vue'
import { getCategoryTitleZh, getCategoryDescriptionZh } from '@/utils/systemConfigI18n'

const {
  categories, itemsByCategory, activeCategory, setActiveCategory,
  hasDirty, dirtyCount, toast, clearToast,
  isLoading, isSaving, loadError,
  load, retry, save, resetDraft,
  setDraftValue, draftValues, issueByKey, serverItems,
} = useSystemConfig()

onMounted(load)

// Auto-clear toast
watch(toast, (val) => {
  if (val) setTimeout(clearToast, 3000)
})

function getValue(key: string): string {
  if (key in draftValues) return draftValues[key]
  return serverItems.value.find((i) => i.key === key)?.value ?? ''
}

const activeItems = computed(() =>
  itemsByCategory.value[activeCategory.value] ?? []
)
</script>

<template>
  <div class="flex-1 overflow-hidden flex flex-col">
    <!-- Header -->
    <div class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shrink-0">
      <div>
        <h1 class="text-lg font-bold text-slate-900">系统配置</h1>
        <p class="text-xs text-slate-500 mt-0.5">修改配置后点击保存生效</p>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="hasDirty" class="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full">
          {{ dirtyCount }} 项已修改
        </span>
        <button
          v-if="hasDirty"
          class="text-sm text-slate-500 hover:text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          @click="resetDraft"
        >放弃</button>
        <button
          :disabled="isSaving || !hasDirty"
          class="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
          @click="save"
        >
          <svg v-if="isSaving" class="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ isSaving ? '保存中…' : '保存配置' }}
        </button>
      </div>
    </div>

    <!-- Toast -->
    <div
      v-if="toast"
      :class="[
        'fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-2 transition-all',
        toast.type === 'success' ? 'bg-green-600 text-white' : toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-amber-500 text-white',
      ]"
    >
      {{ toast.message }}
    </div>

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <div class="w-52 bg-white border-r border-slate-200 overflow-y-auto shrink-0 py-3">
        <div v-if="isLoading" class="py-8 flex justify-center">
          <Loading size="sm" />
        </div>
        <template v-else>
          <button
            v-for="cat in categories"
            :key="cat.category"
            :class="[
              'w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center justify-between',
              activeCategory === cat.category
                ? 'bg-blue-50 text-blue-700 font-medium border-r-2 border-blue-500'
                : 'text-slate-600 hover:bg-slate-50',
            ]"
            @click="setActiveCategory(cat.category)"
          >
            <span>{{ getCategoryTitleZh(cat.category, cat.title) }}</span>
            <span class="text-xs text-slate-400">{{ (itemsByCategory[cat.category] ?? []).length }}</span>
          </button>
        </template>
      </div>

      <!-- Fields -->
      <div class="flex-1 overflow-y-auto p-6 bg-slate-50">
        <div v-if="isLoading" class="flex items-center justify-center py-20">
          <Loading size="lg" label="加载配置中…" />
        </div>
        <div v-else-if="loadError" class="max-w-lg mx-auto py-10">
          <SettingsAlert variant="error" title="加载失败" :message="loadError" action-label="重试" @action="retry" />
        </div>
        <div v-else class="max-w-2xl space-y-6">
          <div>
            <h2 class="text-base font-semibold text-slate-800">
              {{ getCategoryTitleZh(activeCategory) }}
            </h2>
            <p v-if="getCategoryDescriptionZh(activeCategory)" class="text-sm text-slate-500 mt-0.5">
              {{ getCategoryDescriptionZh(activeCategory) }}
            </p>
          </div>

          <div v-if="activeItems.length === 0" class="text-sm text-slate-400 py-8 text-center">
            该分类暂无可编辑配置项
          </div>

          <div v-else class="space-y-5">
            <div v-for="item in activeItems" :key="item.key" class="bg-white rounded-xl border border-slate-200 p-4">
              <SettingsField
                :item="item"
                :model-value="getValue(item.key)"
                :issues="issueByKey[item.key]"
                @update:model-value="setDraftValue(item.key, $event)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
