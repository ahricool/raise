<script setup lang="ts">
import ApiErrorAlert from '@/components/ApiErrorAlert.vue'
import MarkdownBlock from '@/components/MarkdownBlock.vue'
import { analysisApi, DuplicateTaskError } from '@/api/analysis'
import { getParsedApiError, type ParsedApiError } from '@/api/error'
import { historyApi } from '@/api/history'
import { systemConfigApi } from '@/api/systemConfig'
import type { HistoryItem } from '@/types/analysis'
import type { TaskAccepted, BatchTaskAcceptedResponse } from '@/types/analysis'
import { onBeforeUnmount, onMounted, ref } from 'vue'

const stockCode = ref('')
const listError = ref<ParsedApiError | null>(null)
const actionError = ref<ParsedApiError | null>(null)
const items = ref<HistoryItem[]>([])
const loadingList = ref(false)
const submitting = ref(false)
const selectedId = ref<number | null>(null)
const markdown = ref<string>('')
const loadingMd = ref(false)
const setupComplete = ref<boolean | null>(null)
const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)

async function loadHistory() {
  loadingList.value = true
  listError.value = null
  try {
    const res = await historyApi.getList({ page: 1, limit: 30 })
    items.value = res.items
  } catch (e) {
    listError.value = getParsedApiError(e)
  } finally {
    loadingList.value = false
  }
}

async function loadSetup() {
  try {
    const st = await systemConfigApi.getSetupStatus()
    setupComplete.value = st.isComplete
  } catch {
    setupComplete.value = null
  }
}

async function selectItem(id: number) {
  selectedId.value = id
  loadingMd.value = true
  markdown.value = ''
  try {
    markdown.value = await historyApi.getMarkdown(id)
  } catch (e) {
    markdown.value = `> 加载报告失败：${getParsedApiError(e).message}`
  } finally {
    loadingMd.value = false
  }
}

function stopPoll() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

async function pollTask(taskId: string) {
  stopPoll()
  pollTimer.value = setInterval(async () => {
    try {
      const st = await analysisApi.getStatus(taskId)
        if (st.status === 'completed' || st.status === 'failed') {
          stopPoll()
          submitting.value = false
          await loadHistory()
          if (st.status === 'completed' && st.result) {
            const code = st.result.stockCode
            const match = items.value.find((i) => i.stockCode === code)
            if (match) {
              await selectItem(match.id)
            }
          }
        }
    } catch {
      stopPoll()
      submitting.value = false
    }
  }, 2000)
}

function isTaskAccepted(x: unknown): x is TaskAccepted {
  return typeof x === 'object' && x !== null && 'taskId' in x && !('accepted' in x)
}

function isBatchAccepted(x: unknown): x is BatchTaskAcceptedResponse {
  return typeof x === 'object' && x !== null && 'accepted' in x
}

async function submitAnalysis() {
  const code = stockCode.value.trim()
  if (!code) {
    actionError.value = getParsedApiError(new Error('请输入股票代码'))
    return
  }
  actionError.value = null
  submitting.value = true
  try {
    const res = await analysisApi.analyzeAsync({
      stockCode: code,
      asyncMode: true,
      reportType: 'detailed',
    })
    if (isTaskAccepted(res)) {
      await pollTask(res.taskId)
      return
    }
    if (isBatchAccepted(res) && res.accepted.length > 0) {
      await pollTask(res.accepted[0].taskId)
      return
    }
    submitting.value = false
    await loadHistory()
  } catch (e) {
    submitting.value = false
    if (e instanceof DuplicateTaskError) {
      actionError.value = getParsedApiError(new Error(e.message))
    } else {
      actionError.value = getParsedApiError(e)
    }
  }
}

onMounted(() => {
  void loadHistory()
  void loadSetup()
  document.title = '每日选股分析 - DSA'
})

onBeforeUnmount(() => {
  stopPoll()
})
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-2xl font-semibold tracking-tight">分析工作台</h1>
      <p v-if="setupComplete === false" class="mt-2 text-sm text-amber-600 dark:text-amber-400">
        检测到系统配置未完成，建议先在「设置」或环境变量中补齐 LLM 与通知渠道。
      </p>
    </header>

    <section class="rounded-2xl border border-border bg-card/70 p-4 shadow-sm">
      <h2 class="text-sm font-medium text-secondary-text">发起分析</h2>
      <div class="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end">
        <label class="flex-1 text-sm">
          <span class="text-secondary-text">股票代码</span>
          <input
            v-model="stockCode"
            type="text"
            placeholder="如 600519、hk00700、AAPL"
            class="mt-1 w-full rounded-xl border border-input bg-background px-3 py-2 text-foreground outline-none ring-primary focus:ring-2"
            @keydown.enter.prevent="submitAnalysis"
          />
        </label>
        <button
          type="button"
          class="rounded-xl bg-primary px-5 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
          :disabled="submitting"
          @click="submitAnalysis"
        >
          {{ submitting ? '分析进行中…' : '异步分析' }}
        </button>
      </div>
      <p v-if="submitting" class="mt-2 text-xs text-muted-foreground">任务在后台执行，完成后会自动刷新历史并打开最新报告。</p>
      <div v-if="actionError" class="mt-3">
        <ApiErrorAlert :error="actionError" />
      </div>
    </section>

    <div class="grid gap-6 lg:grid-cols-2">
      <section class="rounded-2xl border border-border bg-card/70 p-4">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-medium text-secondary-text">历史记录</h2>
          <button type="button" class="text-xs text-primary hover:underline" @click="loadHistory">刷新</button>
        </div>
        <div v-if="listError" class="mt-3">
          <ApiErrorAlert :error="listError" />
        </div>
        <p v-else-if="loadingList" class="mt-6 text-center text-sm text-muted-foreground">加载中…</p>
        <ul v-else class="mt-3 max-h-[480px] divide-y divide-border overflow-y-auto text-sm">
          <li v-for="row in items" :key="row.id">
            <button
              type="button"
              class="flex w-full flex-col items-start gap-0.5 py-3 text-left transition hover:bg-hover/60"
              :class="selectedId === row.id ? 'bg-primary/10' : ''"
              @click="selectItem(row.id)"
            >
              <span class="font-medium text-foreground">{{ row.stockCode }} {{ row.stockName || '' }}</span>
              <span class="text-xs text-muted-foreground">{{ row.createdAt }}</span>
            </button>
          </li>
        </ul>
      </section>

      <section class="rounded-2xl border border-border bg-card/70 p-4">
        <h2 class="text-sm font-medium text-secondary-text">报告预览</h2>
        <p v-if="!selectedId" class="mt-6 text-sm text-muted-foreground">选择左侧一条历史记录查看 Markdown 报告。</p>
        <p v-else-if="loadingMd" class="mt-6 text-sm text-muted-foreground">加载报告内容…</p>
        <div v-else class="mt-4 max-h-[560px] overflow-y-auto rounded-xl border border-border/60 bg-background/50 p-4">
          <MarkdownBlock :source="markdown" />
        </div>
      </section>
    </div>
  </div>
</template>
