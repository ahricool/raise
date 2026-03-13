import http from './http'
import type { HistoryListResponse, AnalysisReport, NewsIntelResponse } from '@/types/analysis'

export const historyApi = {
  async getList(params?: {
    stockCode?: string
    startDate?: string
    endDate?: string
    page?: number
    limit?: number
  }): Promise<HistoryListResponse> {
    const snakeParams: Record<string, unknown> = {}
    if (params?.stockCode !== undefined) snakeParams.stock_code = params.stockCode
    if (params?.startDate !== undefined) snakeParams.start_date = params.startDate
    if (params?.endDate !== undefined) snakeParams.end_date = params.endDate
    if (params?.page !== undefined) snakeParams.page = params.page
    if (params?.limit !== undefined) snakeParams.limit = params.limit
    const res = await http.get('/api/v1/history', { params: snakeParams })
    return res.data
  },

  async getDetail(queryId: string): Promise<AnalysisReport> {
    const res = await http.get(`/api/v1/history/${queryId}`)
    return res.data
  },

  async getNews(queryId: string, limit = 20): Promise<NewsIntelResponse> {
    const res = await http.get(`/api/v1/history/${queryId}/news`, { params: { limit } })
    return res.data
  },
}
