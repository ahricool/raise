import type { SystemConfigCategory } from '@/types/systemConfig'

const CATEGORY_TITLES: Record<string, string> = {
  base: '基础配置',
  data_source: '数据源',
  ai_model: 'AI 模型',
  notification: '通知渠道',
  system: '系统设置',
  backtest: '回测配置',
  uncategorized: '其他',
}

const CATEGORY_DESCS: Record<string, string> = {
  base: '股票列表、运行模式等基础参数',
  data_source: '行情数据获取来源配置',
  ai_model: 'Gemini / OpenAI 模型及参数',
  notification: '推送通知渠道配置',
  system: '日志、并发、代理等系统参数',
  backtest: '历史预测回测评估参数',
}

export function getCategoryTitleZh(cat: SystemConfigCategory, fallback?: string): string {
  return CATEGORY_TITLES[cat] ?? fallback ?? cat
}

export function getCategoryDescriptionZh(cat: SystemConfigCategory, fallback?: string): string {
  return CATEGORY_DESCS[cat] ?? fallback ?? ''
}

export function getFieldTitleZh(key: string, fallback?: string): string {
  return fallback ?? key
}

export function getFieldDescriptionZh(key: string, fallback?: string): string {
  return fallback ?? ''
}
