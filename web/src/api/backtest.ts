import http from './http'
import type {
  BacktestRunResponse,
  BacktestResultsResponse,
  PerformanceMetrics,
} from '@/types/backtest'

export const backtestApi = {
  async run(params: {
    code?: string
    force?: boolean
    evalWindowDays?: number
    minAgeDays?: number
    limit?: number
  }): Promise<BacktestRunResponse> {
    const res = await http.post('/api/v1/backtest/run', params)
    return res.data
  },

  async getResults(params?: {
    code?: string
    evalWindowDays?: number
    page?: number
    limit?: number
  }): Promise<BacktestResultsResponse> {
    const res = await http.get('/api/v1/backtest/results', { params })
    return res.data
  },

  async getOverallPerformance(evalWindowDays?: number): Promise<PerformanceMetrics | null> {
    try {
      const res = await http.get('/api/v1/backtest/performance', {
        params: evalWindowDays ? { eval_window_days: evalWindowDays } : {},
      })
      return res.data
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const e = err as { response: { status: number } }
        if (e.response?.status === 404) return null
      }
      throw err
    }
  },

  async getStockPerformance(code: string, evalWindowDays?: number): Promise<PerformanceMetrics | null> {
    try {
      const res = await http.get(`/api/v1/backtest/performance/${code}`, {
        params: evalWindowDays ? { eval_window_days: evalWindowDays } : {},
      })
      return res.data
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const e = err as { response: { status: number } }
        if (e.response?.status === 404) return null
      }
      throw err
    }
  },
}
