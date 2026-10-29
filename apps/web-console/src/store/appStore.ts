/**
 * Global Zustand store — API connectivity and API key.
 *
 * The API key is held here as the single source of truth: the axios request
 * interceptor reads it, and `persist` is what writes it to localStorage.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  apiKey: string
  apiOnline: boolean
  apiVersion: string
  setApiKey: (key: string) => void
  setApiOnline: (v: boolean) => void
  setApiVersion: (v: string) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      apiKey: '',
      apiOnline: false,
      apiVersion: '',
      setApiKey: (key) => set({ apiKey: key }),
      setApiOnline: (v) => set({ apiOnline: v }),
      setApiVersion: (v) => set({ apiVersion: v }),
    }),
    {
      name: 'bridgecad-app',
      partialize: (s) => ({ apiKey: s.apiKey }),   // only persist API key
    },
  ),
)
