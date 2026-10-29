/**
 * BridgeCAD Enterprise — React Dashboard (M7 / Production)
 * Routes: Dashboard | Projects | Drawing Gen | QA | BOQ | Export
 */
import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Layout        from './components/Layout'
import Dashboard     from './pages/Dashboard'
import Projects      from './pages/Projects'
import DrawPage      from './pages/DrawPage'
import QAPage        from './pages/QAPage'
import BOQPage       from './pages/BOQPage'
import ExportPage    from './pages/ExportPage'

function NotFound() {
  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">404 — Page not found</h1>
      <p className="text-slate-500 text-sm mb-6">That route does not exist in the console.</p>
      <Link to="/" className="text-blue-600 hover:underline text-sm font-medium">← Back to Dashboard</Link>
    </div>
  )
}

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state: { error: Error | null } = { error: null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('BridgeCAD UI error:', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="p-6">
          <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-red-700 text-sm">
            <div className="font-semibold mb-1">Something went wrong.</div>
            <div className="font-mono text-xs">{this.state.error.message}</div>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="draw" element={<DrawPage />} />
          <Route path="qa" element={<QAPage />} />
          <Route path="boq" element={<BOQPage />} />
          <Route path="export" element={<ExportPage />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  )
}
