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
    const res = await http.get('/api/v1/history', { params })
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
