export type SystemConfigCategory =
  | 'base'
  | 'data_source'
  | 'ai_model'
  | 'notification'
  | 'system'
  | 'backtest'
  | 'uncategorized'

export type SystemConfigDataType = 'string' | 'integer' | 'float' | 'boolean' | 'list'

export type SystemConfigUIControl =
  | 'text'
  | 'password'
  | 'number'
  | 'select'
  | 'textarea'
  | 'switch'
  | 'time'

export interface SystemConfigFieldSchema {
  key: string
  title?: string
  description?: string
  category: SystemConfigCategory
  dataType: SystemConfigDataType
  uiControl: SystemConfigUIControl
  isSensitive: boolean
  isRequired: boolean
  isEditable: boolean
  defaultValue?: string | null
  options: string[]
  validation: Record<string, unknown>
  displayOrder: number
}

export interface SystemConfigCategorySchema {
  category: SystemConfigCategory
  title: string
  description?: string
  fields: SystemConfigFieldSchema[]
}

export interface SystemConfigItem {
  key: string
  value: string
  rawValueExists: boolean
  isMasked: boolean
  schema?: SystemConfigFieldSchema
}

export interface SystemConfigUpdateItem {
  key: string
  value: string
}

export interface ConfigValidationIssue {
  key: string
  code: string
  message: string
  severity: 'error' | 'warning'
  expected?: string
  actual?: string
}

export interface SystemConfigResponse {
  items: SystemConfigItem[]
  configVersion: string
}

export interface SystemConfigSchemaResponse {
  categories: SystemConfigCategorySchema[]
}

export interface ValidateSystemConfigResponse {
  valid: boolean
  issues: ConfigValidationIssue[]
}

export interface UpdateSystemConfigResponse {
  success: boolean
  configVersion: string
  updatedCount: number
  issues: ConfigValidationIssue[]
}
