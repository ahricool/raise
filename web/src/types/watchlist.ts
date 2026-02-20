export interface WatchlistItem {
  id: number
  stockCode: string
  stockName?: string
  createdAt: string
}

export interface WatchlistResponse {
  items: WatchlistItem[]
  total: number
}

export interface StockSearchResult {
  stockCode: string
  stockName: string
  market?: string
}

export interface StockSearchResponse {
  query: string
  results: StockSearchResult[]
}
