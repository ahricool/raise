import http from './http'
import type {
  AnalysisRequest,
  AnalysisReport,
  TaskStatus,
  TaskListResponse,
} from '@/types/analysis'
import { API_BASE_URL } from '@/utils/constants'

export class DuplicateTaskError extends Error {
  constructor(
    public stockCode: string,
    public existingTaskId: string,
    message: string,
  ) {
    super(message)
    this.name = 'DuplicateTaskError'
  }
}

export const analysisApi = {
  async analyzeAsync(data: AnalysisRequest): Promise<{ taskId: string; status: string; message: string }> {
    try {
      const res = await http.post('/api/v1/analysis/analyze', {
        ...data,
        async_mode: true,
      })
      return res.data
    } catch (err: unknown) {
      if (
        err &&
        typeof err === 'object' &&
        'response' in err &&
        (err as { response: { status: number; data: { taskId: string; stockCode: string } } }).response?.status === 409
      ) {
        const e = err as { response: { data: { taskId: string; stockCode: string; message: string } } }
        throw new DuplicateTaskError(
          e.response.data.stockCode ?? data.stockCode,
          e.response.data.taskId ?? '',
          e.response.data.message ?? '任务已在进行中',
        )
      }
      throw err
    }
  },

  async getStatus(taskId: string): Promise<TaskStatus> {
    const res = await http.get(`/api/v1/analysis/status/${taskId}`)
    return res.data
  },

  async getTasks(params?: { status?: string; limit?: number }): Promise<TaskListResponse> {
    const res = await http.get('/api/v1/analysis/tasks', { params })
    return res.data
  },

  getTaskStreamUrl(): string {
    return `${API_BASE_URL}/api/v1/analysis/tasks/stream`
  },
}
