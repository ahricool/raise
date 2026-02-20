import http from './http'
import type {
  WatchlistResponse,
  WatchlistItem,
  StockSearchResponse,
} from '@/types/watchlist'

export const watchlistApi = {
  async list(): Promise<WatchlistResponse> {
    const res = await http.get('/api/v1/watchlist')
    return res.data
  },

  async search(q: string): Promise<StockSearchResponse> {
    const res = await http.get('/api/v1/watchlist/search', { params: { q } })
    return res.data
  },

  async add(stockCode: string, stockName?: string): Promise<WatchlistItem> {
    const res = await http.post('/api/v1/watchlist', {
      stock_code: stockCode,
      stock_name: stockName ?? null,
    })
    return res.data
  },

  async remove(id: number): Promise<void> {
    await http.delete(`/api/v1/watchlist/${id}`)
  },
}
