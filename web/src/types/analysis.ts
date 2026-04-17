export type SentimentLabel = 'fearful' | 'cautious' | 'neutral' | 'optimistic' | 'greedy'
export type ReportType = 'simple' | 'detailed'

export type AnalysisMode = 'auto' | 'single' | 'multi_agent'

export interface AnalysisRequest {
  stockCode: string
  reportType?: ReportType
  forceRefresh?: boolean
  asyncMode?: boolean
  analysisMode?: AnalysisMode
}

// 多智能体 Agent 进度事件
export interface MultiAgentProgressEvent {
  event: 'init' | 'started' | 'completed' | 'error' | 'done'
  node?: string
  display_name?: string
  step?: number
  total?: number
  message?: string
  result?: MultiAgentResult
}

// 多智能体最终结果
export interface MultiAgentResult {
  code: string
  name: string
  sentiment_score: number
  trend_prediction: string
  operation_advice: string
  decision_type: string
  confidence_level: string
  dashboard?: Record<string, unknown>
  technical_analysis?: string
  fundamental_analysis?: string
  news_summary?: string
  market_sentiment?: string
  analysis_summary?: string
  risk_warning?: string
  data_sources?: string
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
