export function formatDateTime(value: string | Date): string {
  const d = value instanceof Date ? value : new Date(value)
  return d.toLocaleString('zh-CN', { hour12: false })
}

export function formatDate(value: string | Date): string {
  const d = value instanceof Date ? value : new Date(value)
  return d.toLocaleDateString('zh-CN')
}

export function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10)
}

export function getRecentStartDate(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return toDateInputValue(d)
}

export function formatReportType(value?: string): string {
  if (value === 'simple') return '普通'
  if (value === 'detailed') return '标准'
  return value || ''
}

export function formatPct(value?: number | null, decimals = 2): string {
  if (value == null) return '-'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}
