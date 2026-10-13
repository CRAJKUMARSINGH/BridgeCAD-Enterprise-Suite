/**
 * Global Zustand store — API connectivity, active project, API key.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  apiKey: string
  apiOnline: boolean
  apiVersion: string
  activeFile: File | null
  activeProjectName: string
  setApiKey: (key: string) => void
  setApiOnline: (v: boolean) => void
  setApiVersion: (v: string) => void
  setActiveFile: (f: File | null) => void
  setActiveProjectName: (n: string) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      apiKey: '',
      apiOnline: false,
      apiVersion: '',
      activeFile: null,
      activeProjectName: '',
      setApiKey: (key) => {
        localStorage.setItem('bridgecad_api_key', key)
        set({ apiKey: key })
      },
      setApiOnline: (v) => set({ apiOnline: v }),
      setApiVersion: (v) => set({ apiVersion: v }),
      setActiveFile: (f) => set({ activeFile: f, activeProjectName: f?.name ?? '' }),
      setActiveProjectName: (n) => set({ activeProjectName: n }),
    }),
    {
      name: 'bridgecad-app',
      partialize: (s) => ({ apiKey: s.apiKey }),   // only persist API key
    },
  ),
)
