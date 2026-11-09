/**
 * BridgeCAD API client — typed wrappers around all FastAPI endpoints.
 *
 * Requests go to a same-origin `/api` prefix by default, which is proxied to
 * the FastAPI gateway in every environment (Vite dev server, and the nginx
 * reverse proxy in production). Override with VITE_API_URL only when the API
 * lives on a different origin.
 */

import axios, { type AxiosInstance, type AxiosProgressEvent } from 'axios'
import { useAppStore } from '../store/appStore'

export const BASE_URL = (import.meta.env.VITE_API_URL as string) || '/api'

const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,         // 2 min — DXF generation can take time
  headers: { 'Content-Type': 'application/json' },
})

/** Attach API-key header when one is stored in the app store */
http.interceptors.request.use((config) => {
  const key = useAppStore.getState().apiKey
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

  /** POST /draw/gad — upload xlsx, download DXF ZIP.
   *  Omit `scale` to use each sheet's standard scale (recommended). */
  drawGAD: (
    file: File,
    scale?: number | null,
    prefix = 'GAD',
    onProgress?: (pct: number) => void,
  ): Promise<Blob> => {
    const fd = new FormData()
    fd.append('file', file)
    const params = new URLSearchParams({ prefix })
    if (scale != null) params.set('scale', String(scale))
    return http
      .post(`/draw/gad?${params}`, fd, {
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

  /** POST /exports/bundle — upload xlsx, download ZIP.
   *  Omit `scale` to use each sheet's standard scale (recommended). */
  exportBundle: (file: File, state?: string, scale?: number | null): Promise<Blob> => {
    const fd = new FormData()
    fd.append('file', file)
    const params = new URLSearchParams()
    if (scale != null) params.set('scale', String(scale))
    if (state) params.set('state', state)
    const qs = params.toString()
    return http
      .post(`/exports/bundle${qs ? `?${qs}` : ''}`, fd, {
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

/** Save a Blob as a file download. */
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.rel = 'noopener'
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  // Revoke on the next macrotask: revoking synchronously can abort the
  // download before the browser has started fetching the object URL.
  setTimeout(() => URL.revokeObjectURL(url), 0)
}

// ─── Project session (patch mechanic) ─────────────────────────────────────

export interface PatchCheck {
  id: string
  parameter: string
  value: string
  limit: string
  ok: boolean
}

export interface PatchResult {
  section: string
  field: string
  value: unknown
  checks: PatchCheck[]
  qa: { score: number | null; failures: number | null; error?: string }
}

export interface ProjectLoadResult {
  token: string
  summary: ProjectSummary
}

export const projectApi = {
  /** POST /project/load — upload xlsx, get a patch token */
  load: (file: File): Promise<ProjectLoadResult> => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/project/load', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },

  /** PATCH /project/{token}/{section}/{field} — atomic single-field patch */
  patch: (token: string, section: string, field: string, value: number | string): Promise<PatchResult> =>
    http
      .patch(`/project/${token}/${section}/${field}`, { value })
      .then((r) => r.data),
}
