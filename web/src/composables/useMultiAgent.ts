import { ref, onUnmounted } from 'vue'
import type { MultiAgentProgressEvent, MultiAgentResult } from '@/types/analysis'
import { API_BASE_URL } from '@/utils/constants'

// Agent 节点顺序（用于进度条计算）
export const AGENT_STEPS = [
  { node: 'market_analyst',       label: '技术面分析师' },
  { node: 'fundamentals_analyst', label: '基本面分析师' },
  { node: 'news_analyst',         label: '新闻分析师' },
  { node: 'sentiment_analyst',    label: '情绪分析师' },
  { node: 'bull_researcher',      label: '多方研究员' },
  { node: 'bear_researcher',      label: '空方研究员' },
  { node: 'trader',               label: '交易员' },
  { node: 'aggressive_risk',      label: '激进风控' },
  { node: 'conservative_risk',    label: '保守风控' },
  { node: 'neutral_risk',         label: '中立风控' },
  { node: 'portfolio_manager',    label: '投资组合经理' },
]

export interface AgentStepStatus {
  node: string
  label: string
  status: 'pending' | 'running' | 'completed' | 'error'
}

export function useMultiAgent() {
  const isRunning = ref(false)
  const isConnected = ref(false)
  const error = ref<string | null>(null)
  const result = ref<MultiAgentResult | null>(null)
  const currentStep = ref(0)
  const totalSteps = ref(AGENT_STEPS.length)

  const stepStatuses = ref<AgentStepStatus[]>(
    AGENT_STEPS.map((s) => ({ ...s, status: 'pending' as const })),
  )

  let ws: WebSocket | null = null

  function reset() {
    error.value = null
    result.value = null
    currentStep.value = 0
    totalSteps.value = AGENT_STEPS.length
    stepStatuses.value = AGENT_STEPS.map((s) => ({ ...s, status: 'pending' as const }))
  }

  function buildWsUrl(): string {
    const base = API_BASE_URL || window.location.origin
    const url = new URL('/api/v1/ws/multi-agent', base)
    url.protocol = url.protocol.replace('http', 'ws')
    return url.toString()
  }

  function updateStep(node: string, status: AgentStepStatus['status']) {
    const idx = stepStatuses.value.findIndex((s) => s.node === node)
    if (idx >= 0) stepStatuses.value[idx].status = status
  }

  /**
   * 启动多智能体分析。
   * @param stockCode 股票代码
   */
  function run(stockCode: string): Promise<MultiAgentResult> {
    return new Promise((resolve, reject) => {
      if (ws) {
        ws.close()
        ws = null
      }
      reset()
      isRunning.value = true

      ws = new WebSocket(buildWsUrl())

      ws.onopen = () => {
        isConnected.value = true
        ws!.send(JSON.stringify({ stock_code: stockCode, analysis_mode: 'multi_agent' }))
      }

      ws.onmessage = (evt) => {
        let event: MultiAgentProgressEvent
        try {
          event = JSON.parse(evt.data)
        } catch {
          return
        }

        switch (event.event) {
          case 'init':
            totalSteps.value = event.total ?? AGENT_STEPS.length
            break

          case 'started':
            if (event.node) updateStep(event.node, 'running')
            break

          case 'completed':
            if (event.node) updateStep(event.node, 'completed')
            currentStep.value = event.step ?? currentStep.value
            break

          case 'error':
            if (event.node) {
              updateStep(event.node, 'error')
            } else {
              error.value = event.message ?? '未知错误'
              isRunning.value = false
              ws?.close()
              reject(new Error(error.value ?? undefined))
            }
            break

          case 'done':
            if (event.result) {
              result.value = event.result
              isRunning.value = false
              resolve(event.result)
            }
            break
        }
      }

      ws.onerror = () => {
        error.value = 'WebSocket 连接失败'
        isRunning.value = false
        isConnected.value = false
        reject(new Error('WebSocket 连接失败'))
      }

      ws.onclose = () => {
        isConnected.value = false
        if (isRunning.value) {
          // 异常断开
          isRunning.value = false
          if (!result.value && !error.value) {
            error.value = '连接意外断开'
            reject(new Error('连接意外断开'))
          }
        }
      }
    })
  }

  function cancel() {
    ws?.close()
    ws = null
    isRunning.value = false
    isConnected.value = false
  }

  onUnmounted(() => {
    ws?.close()
    ws = null
  })

  return {
    isRunning,
    isConnected,
    error,
    result,
    currentStep,
    totalSteps,
    stepStatuses,
    run,
    cancel,
    reset,
  }
}
