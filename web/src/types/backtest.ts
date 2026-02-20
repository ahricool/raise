export interface BacktestResultItem {
  analysisHistoryId: number
  code: string
  analysisDate?: string
  evalWindowDays: number
  engineVersion: string
  evalStatus: string
  operationAdvice?: string
  positionRecommendation?: string
  startPrice?: number
  endClose?: number
  maxHigh?: number
  minLow?: number
  stockReturnPct?: number
  directionExpected?: string
  directionCorrect?: boolean
  outcome?: 'win' | 'loss' | 'neutral'
  stopLoss?: number
  takeProfit?: number
  hitStopLoss?: boolean
  hitTakeProfit?: boolean
  firstHit?: string
  firstHitDate?: string
  firstHitTradingDays?: number
  simulatedEntryPrice?: number
  simulatedExitPrice?: number
  simulatedExitReason?: string
  simulatedReturnPct?: number
  evaluatedAt?: string
}

export interface PerformanceMetrics {
  scope: string
  code?: string
  evalWindowDays: number
  engineVersion: string
  computedAt?: string
  totalEvaluations: number
  completedCount: number
  insufficientCount: number
  longCount: number
  cashCount: number
  winCount: number
  lossCount: number
  neutralCount: number
  directionAccuracyPct?: number
  winRatePct?: number
  neutralRatePct?: number
  avgStockReturnPct?: number
  avgSimulatedReturnPct?: number
  stopLossTriggerRate?: number
  takeProfitTriggerRate?: number
  ambiguousRate?: number
  avgDaysToFirstHit?: number
  adviceBreakdownJson?: string
}

export interface BacktestRunResponse {
  evaluated: number
  skipped: number
  failed: number
  total: number
}

export interface BacktestResultsResponse {
  items: BacktestResultItem[]
  total: number
  page: number
  limit: number
  totalPages: number
}
