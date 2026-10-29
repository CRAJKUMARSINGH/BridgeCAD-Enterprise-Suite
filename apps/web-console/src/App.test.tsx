import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'

// Unit tests must not hit the network: stub the API hooks so no XHR is issued.
vi.mock('./hooks/useApi', () => ({
  useHealth: () => ({ data: undefined, isError: true, isPending: false }),
  usePlugins: () => ({ data: undefined }),
  useParseBridge: () => ({}),
  useValidateBridge: () => ({}),
  useDrawGAD: () => ({}),
  useGenerateBill: () => ({}),
  useQAReport: () => ({}),
  useExportBundle: () => ({}),
}))

function renderAt(path: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('App routing', () => {
  it('renders the dashboard at /', () => {
    renderAt('/')
    expect(screen.getByRole('heading', { name: /BridgeCAD Enterprise/ })).toBeInTheDocument()
  })

  it('renders a 404 page for unknown routes', () => {
    renderAt('/does-not-exist')
    expect(screen.getByText(/404 — Page not found/)).toBeInTheDocument()
  })
})
