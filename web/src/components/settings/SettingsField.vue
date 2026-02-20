<script setup lang="ts">
import { ref, computed } from 'vue'
import type { SystemConfigItem, ConfigValidationIssue } from '@/types/systemConfig'

const props = defineProps<{
  item: SystemConfigItem
  modelValue: string
  issues?: ConfigValidationIssue[]
}>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const showPassword = ref(false)
const control = computed(() => props.item.schema?.uiControl ?? 'text')
const isEditable = computed(() => props.item.schema?.isEditable !== false)

function update(v: string) { emit('update:modelValue', v) }

// Multi-value
const listItems = computed(() =>
  props.modelValue ? props.modelValue.split(',').map((s) => s.trim()).filter(Boolean) : [],
)
function addItem() { emit('update:modelValue', [...listItems.value, ''].join(',')) }
function updateItem(idx: number, v: string) {
  const arr = [...listItems.value]
  arr[idx] = v
  emit('update:modelValue', arr.join(','))
}
function removeItem(idx: number) {
  const arr = listItems.value.filter((_, i) => i !== idx)
  emit('update:modelValue', arr.join(','))
}
</script>

<template>
  <div class="space-y-1.5">
    <div class="flex items-center gap-2">
      <label class="text-sm font-medium text-slate-700">
        {{ item.schema?.title || item.key }}
        <span v-if="item.schema?.isRequired" class="text-red-500 ml-0.5">*</span>
      </label>
      <span v-if="item.schema?.isSensitive" class="text-xs bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded">敏感</span>
    </div>
    <p v-if="item.schema?.description" class="text-xs text-slate-400">{{ item.schema.description }}</p>

    <!-- Switch -->
    <div v-if="control === 'switch'" class="flex items-center gap-3">
      <button
        type="button"
        :disabled="!isEditable"
        :class="[
          'relative inline-flex h-5 w-9 rounded-full transition-colors focus:outline-none',
          modelValue === 'true' ? 'bg-blue-600' : 'bg-slate-200',
          !isEditable ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
        ]"
        @click="update(modelValue === 'true' ? 'false' : 'true')"
      >
        <span
          :class="[
            'inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform mt-0.5',
            modelValue === 'true' ? 'translate-x-4' : 'translate-x-0.5',
          ]"
        />
      </button>
      <span class="text-sm text-slate-600">{{ modelValue === 'true' ? '开启' : '关闭' }}</span>
    </div>

    <!-- Select -->
    <select
      v-else-if="control === 'select'"
      :value="modelValue"
      :disabled="!isEditable"
      class="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
      @change="update(($event.target as HTMLSelectElement).value)"
    >
      <option v-for="opt in item.schema?.options" :key="opt" :value="opt">{{ opt }}</option>
    </select>

    <!-- Textarea -->
    <textarea
      v-else-if="control === 'textarea'"
      :value="modelValue"
      :disabled="!isEditable"
      rows="3"
      class="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 resize-y"
      @input="update(($event.target as HTMLTextAreaElement).value)"
    />

    <!-- Password -->
    <div v-else-if="control === 'password'" class="relative">
      <input
        :type="showPassword ? 'text' : 'password'"
        :value="modelValue"
        :disabled="!isEditable"
        class="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 pr-10 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        @input="update(($event.target as HTMLInputElement).value)"
      />
      <button
        type="button"
        class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
        @click="showPassword = !showPassword"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path v-if="showPassword" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      </button>
    </div>

    <!-- Multi-value (list) -->
    <div v-else-if="item.schema?.dataType === 'list'" class="space-y-2">
      <div v-for="(val, idx) in listItems" :key="idx" class="flex gap-2">
        <input
          :value="val"
          :disabled="!isEditable"
          class="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          @input="updateItem(idx, ($event.target as HTMLInputElement).value)"
        />
        <button
          v-if="isEditable"
          type="button"
          class="text-red-400 hover:text-red-600 px-2"
          @click="removeItem(idx)"
        >×</button>
      </div>
      <button
        v-if="isEditable"
        type="button"
        class="text-xs text-blue-600 hover:underline"
        @click="addItem"
      >+ 添加</button>
    </div>

    <!-- Default text / number / time -->
    <input
      v-else
      :type="control === 'number' ? 'number' : control === 'time' ? 'time' : 'text'"
      :value="modelValue"
      :disabled="!isEditable"
      class="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
      @input="update(($event.target as HTMLInputElement).value)"
    />

    <!-- Validation issues -->
    <div v-if="issues?.length">
      <p
        v-for="issue in issues"
        :key="issue.code"
        :class="['text-xs', issue.severity === 'error' ? 'text-red-500' : 'text-amber-500']"
      >{{ issue.message }}</p>
    </div>
  </div>
</template>
