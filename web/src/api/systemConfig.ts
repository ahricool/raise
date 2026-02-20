import http from './http'
import type {
  SystemConfigResponse,
  SystemConfigSchemaResponse,
  SystemConfigUpdateItem,
  ValidateSystemConfigResponse,
  UpdateSystemConfigResponse,
  ConfigValidationIssue,
} from '@/types/systemConfig'

export class SystemConfigValidationError extends Error {
  constructor(public issues: ConfigValidationIssue[]) {
    super('配置验证失败')
    this.name = 'SystemConfigValidationError'
  }
}

export class SystemConfigConflictError extends Error {
  constructor(public currentConfigVersion: string) {
    super('配置版本冲突，请刷新后重试')
    this.name = 'SystemConfigConflictError'
  }
}

export const systemConfigApi = {
  async getConfig(includeSchema = true): Promise<SystemConfigResponse> {
    const res = await http.get('/api/v1/system/config', {
      params: { include_schema: includeSchema },
    })
    return res.data
  },

  async getSchema(): Promise<SystemConfigSchemaResponse> {
    const res = await http.get('/api/v1/system/config/schema')
    return res.data
  },

  async validate(payload: {
    items: SystemConfigUpdateItem[]
  }): Promise<ValidateSystemConfigResponse> {
    const res = await http.post('/api/v1/system/config/validate', payload)
    return res.data
  },

  async update(payload: {
    items: SystemConfigUpdateItem[]
    configVersion?: string
  }): Promise<UpdateSystemConfigResponse> {
    try {
      const res = await http.put('/api/v1/system/config', payload)
      return res.data
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const e = err as { response: { status: number; data: { issues: ConfigValidationIssue[]; currentConfigVersion: string } } }
        if (e.response?.status === 400) {
          throw new SystemConfigValidationError(e.response.data.issues ?? [])
        }
        if (e.response?.status === 409) {
          throw new SystemConfigConflictError(e.response.data.currentConfigVersion ?? '')
        }
      }
      throw err
    }
  },
}
