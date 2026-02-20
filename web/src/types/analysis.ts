export type SentimentLabel = 'fearful' | 'cautious' | 'neutral' | 'optimistic' | 'greedy'
export type ReportType = 'simple' | 'detailed'

export interface AnalysisRequest {
  stockCode: string
  reportType?: ReportType
  forceRefresh?: boolean
  asyncMode?: boolean
}

export interface ReportMeta {
  queryId: string
  stockCode: string
  stockName: string
  reportType: ReportType
  createdAt: string
  currentPrice?: number
  changePct?: number
}

export interface ReportSummary {
  analysisSummary: string
  operationAdvice: string
  trendPrediction: string
  sentimentScore: number
  sentimentLabel?: SentimentLabel
}

export interface ReportStrategy {
  idealBuy?: string
  secondaryBuy?: string
  stopLoss?: string
  takeProfit?: string
}

export interface ReportDetails {
  newsContent?: string
  rawResult?: Record<string, unknown>
  contextSnapshot?: Record<string, unknown>
}

export interface AnalysisReport {
  meta: ReportMeta
  summary: ReportSummary
  strategy?: ReportStrategy
  details?: ReportDetails
}

export interface TaskInfo {
  taskId: string
  stockCode: string
  stockName?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message?: string
  reportType: string
  createdAt: string
  startedAt?: string
  completedAt?: string
  error?: string
}

export interface TaskStatus {
  taskId: string
  status: string
  progress: number
  message?: string
  result?: AnalysisReport
}

export interface TaskListResponse {
  tasks: TaskInfo[]
  processingCount: number
  pendingCount: number
  total: number
}

export interface HistoryItem {
  queryId: string
  stockCode: string
  stockName?: string
  reportType?: string
  sentimentScore?: number
  operationAdvice?: string
  createdAt: string
}

export interface HistoryListResponse {
  items: HistoryItem[]
  total: number
  page: number
  limit: number
  totalPages: number
}

export interface NewsIntelItem {
  title: string
  snippet: string
  url: string
  source?: string
  publishedDate?: string
}

export interface NewsIntelResponse {
  items: NewsIntelItem[]
  total: number
}
