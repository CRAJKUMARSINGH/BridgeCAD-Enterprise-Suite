/**
 * React-Query hooks wrapping the typed API client.
 */
import { useMutation, useQuery } from '@tanstack/react-query'
import { api, downloadBlob } from '../api/client'

// ─── Health ──────────────────────────────────────────────────────────────
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn:  api.health,
    refetchInterval: 30_000,
    retry: 1,
  })
}

// ─── Plugins ─────────────────────────────────────────────────────────────
export function usePlugins() {
  return useQuery({
    queryKey: ['plugins'],
    queryFn: api.listPlugins,
    staleTime: 5 * 60_000,
  })
}

export function usePluginDetail(id: string) {
  return useQuery({
    queryKey: ['plugin', id],
    queryFn: () => api.getPlugin(id),
    enabled: !!id,
  })
}

// ─── Parse ───────────────────────────────────────────────────────────────
export function useParseBridge() {
  return useMutation({
    mutationFn: (file: File) => api.parseBridge(file),
  })
}

// ─── Validate ────────────────────────────────────────────────────────────
export function useValidateBridge() {
  return useMutation({
    mutationFn: (file: File) => api.validateBridge(file),
  })
}

// ─── Draw ────────────────────────────────────────────────────────────────
export function useDrawGAD() {
  return useMutation({
    mutationFn: ({ file, scale, prefix }: { file: File; scale?: number; prefix?: string }) =>
      api.drawGAD(file, scale, prefix),
    onSuccess: (blob, vars) => {
      downloadBlob(blob, `${vars.prefix ?? 'GAD'}_drawings.zip`)
    },
  })
}

// ─── Bill ─────────────────────────────────────────────────────────────────
export function useGenerateBill() {
  return useMutation({
    mutationFn: ({ file, state }: { file: File; state?: string }) =>
      api.generateBill(file, state),
  })
}

// ─── QA Report ───────────────────────────────────────────────────────────
export function useQAReport() {
  return useMutation({
    mutationFn: (file: File) => api.qaReport(file),
  })
}

// ─── Export Bundle ────────────────────────────────────────────────────────
export function useExportBundle() {
  return useMutation({
    mutationFn: ({ file, state, scale }: { file: File; state?: string; scale?: number }) =>
      api.exportBundle(file, state, scale),
    onSuccess: (blob) => {
      downloadBlob(blob, 'bridgecad_bundle.zip')
    },
  })
}
