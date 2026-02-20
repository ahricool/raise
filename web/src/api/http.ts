import axios from 'axios'
import camelcaseKeys from 'camelcase-keys'
import { API_BASE_URL } from '@/utils/constants'

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.response.use((response) => {
  if (response.data && typeof response.data === 'object') {
    response.data = camelcaseKeys(response.data, { deep: true })
  }
  return response
})

export default http
