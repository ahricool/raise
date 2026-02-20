import { ref, onUnmounted } from 'vue'
import { analysisApi } from '@/api/analysis'
import type { TaskInfo } from '@/types/analysis'

interface TaskStreamOptions {
  onTaskCreated?: (task: TaskInfo) => void
  onTaskStarted?: (task: TaskInfo) => void
  onTaskCompleted?: (task: TaskInfo) => void
  onTaskFailed?: (task: TaskInfo) => void
  onConnected?: () => void
  onError?: (event: Event) => void
  autoReconnect?: boolean
  reconnectDelay?: number
  enabled?: boolean
}

export function useTaskStream(options: TaskStreamOptions = {}) {
  const {
    autoReconnect = true,
    reconnectDelay = 3000,
    enabled = true,
  } = options

  const isConnected = ref(false)
  let es: EventSource | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let destroyed = false

  function parseTask(raw: string): TaskInfo | null {
    try {
      return JSON.parse(raw) as TaskInfo
    } catch {
      return null
    }
  }

  function connect() {
    if (!enabled || destroyed) return
    if (es) es.close()

    es = new EventSource(analysisApi.getTaskStreamUrl())

    es.addEventListener('connected', () => {
      isConnected.value = true
      options.onConnected?.()
    })

    es.addEventListener('heartbeat', () => {
      isConnected.value = true
    })

    es.addEventListener('task_created', (e) => {
      const task = parseTask((e as MessageEvent).data)
      if (task) options.onTaskCreated?.(task)
    })

    es.addEventListener('task_started', (e) => {
      const task = parseTask((e as MessageEvent).data)
      if (task) options.onTaskStarted?.(task)
    })

    es.addEventListener('task_completed', (e) => {
      const task = parseTask((e as MessageEvent).data)
      if (task) options.onTaskCompleted?.(task)
    })

    es.addEventListener('task_failed', (e) => {
      const task = parseTask((e as MessageEvent).data)
      if (task) options.onTaskFailed?.(task)
    })

    es.onerror = (event) => {
      isConnected.value = false
      options.onError?.(event)
      es?.close()
      es = null
      if (autoReconnect && !destroyed) {
        reconnectTimer = setTimeout(connect, reconnectDelay)
      }
    }
  }

  function disconnect() {
    destroyed = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    es?.close()
    es = null
    isConnected.value = false
  }

  function reconnect() {
    destroyed = false
    connect()
  }

  if (enabled) connect()

  onUnmounted(disconnect)

  return { isConnected, reconnect, disconnect }
}
