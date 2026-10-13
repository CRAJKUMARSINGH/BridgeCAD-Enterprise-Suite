/**
 * BridgeCAD API client — typed wrappers around all FastAPI endpoints.
 * Base URL defaults to http://localhost:8000 (override via VITE_API_URL).
 */

import axios, { type AxiosInstance, type AxiosProgressEvent } from 'axios'

export const BASE_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000'

const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,         // 2 min — DXF generation can take time
  headers: { 'Content-Type': 'application/json' },
})

/** Attach API-key header when stored in localStorage */
http.interceptors.request.use((config) => {
  const key = localStorage.getItem('bridgecad_api_key')
  if (key) config.headers['X-API-Key'] = key
  return config
})

// ─── Types ────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  version: string
  packages_loaded: string[]
}

export interface ProjectSummary {
  project_title: string
  bridge_name: string
  chainage_km: number
  total_length_m: number
  span_count: number
  overall_width_m: number
}

export interface ParseResult {
  status: string
  project: ProjectSummary
}

export interface QAFinding {
  check_id: string
  severity: string
  passed: boolean
  description: string
  message: string
}

export interface ValidateResult {
  status: string
  score: number
  grade: string
  critical_fails: number
  warning_fails: number
  findings: QAFinding[]
}

export interface BOQSection {
  code: string
  title: string
  total: number
  items: BOQItem[]
}

export interface BOQItem {
  code: string
  desc: string
  unit: string
  qty: number
  rate: number | null
  amount: number
}

export interface BOQResult {
  project_name: string
  subtotal: number
  contingency_pct: number
  contingency_amount: number
  grand_total: number
  sections: BOQSection[]
}

export interface Plugin {
  id: string
  name: string
  version: string
  bridge_types: string[]
  span_range_m: [number, number]
  description: string
}

export interface PluginDetail extends Plugin {
  typical_values: Record<string, unknown>
}

// ─── API functions ─────────────────────────────────────────────────────────

export const api = {
  /** GET /health */
  health: (): Promise<HealthResponse> =>
    http.get('/health').then((r) => r.data),

  /** GET /version */
  version: (): Promise<{ version: string; codename: string }> =>
    http.get('/version').then((r) => r.data),

  /** POST /bridges/parse — upload xlsx, get project summary */
  parseBridge: (file: File): Promise<ParseResult> => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/bridges/parse', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },

  /** POST /bridges/validate — upload xlsx, get QA report JSON */
  validateBridge: (file: File): Promise<ValidateResult> => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/bridges/validate', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },

  /** POST /draw/gad — upload xlsx, download DXF ZIP */
  drawGAD: (
    file: File,
    scale = 100,
    prefix = 'GAD',
    onProgress?: (pct: number) => void,
  ): Promise<Blob> => {
    const fd = new FormData()
    fd.append('file', file)
    return http
      .post(`/draw/gad?scale=${scale}&prefix=${prefix}`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
        onUploadProgress: (e: AxiosProgressEvent) => {
          if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
        },
      })
      .then((r) => r.data)
  },

  /** POST /bills/generate — upload xlsx, get BOQ JSON */
  generateBill: (file: File, state?: string): Promise<BOQResult> => {
    const fd = new FormData()
    fd.append('file', file)
    const url = state ? `/bills/generate?state=${state}` : '/bills/generate'
    return http.post(url, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },

  /** POST /qa/report — upload xlsx, get HTML blob */
  qaReport: (file: File): Promise<string> => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/qa/report', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'text',
    }).then((r) => r.data)
  },

  /** POST /exports/bundle — upload xlsx, download ZIP */
  exportBundle: (file: File, state?: string, scale = 100): Promise<Blob> => {
    const fd = new FormData()
    fd.append('file', file)
    const params = new URLSearchParams({ scale: String(scale) })
    if (state) params.set('state', state)
    return http
      .post(`/exports/bundle?${params}`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob',
      })
      .then((r) => r.data)
  },

  /** GET /plugins/ */
  listPlugins: (): Promise<{ count: number; plugins: Plugin[] }> =>
    http.get('/plugins/').then((r) => r.data),

  /** GET /plugins/{id} */
  getPlugin: (id: string): Promise<PluginDetail> =>
    http.get(`/plugins/${id}`).then((r) => r.data),
}

/** Save a Blob as a file download */
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
