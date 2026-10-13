/**
 * BridgeCAD Enterprise — React Dashboard (M7 / Production)
 * Routes: Dashboard | Projects | Drawing Gen | QA | BOQ | Export
 */
import { Routes, Route } from 'react-router-dom'
import Layout        from './components/Layout'
import Dashboard     from './pages/Dashboard'
import Projects      from './pages/Projects'
import DrawPage      from './pages/DrawPage'
import QAPage        from './pages/QAPage'
import BOQPage       from './pages/BOQPage'
import ExportPage    from './pages/ExportPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index          element={<Dashboard />}  />
        <Route path="projects"element={<Projects />}   />
        <Route path="draw"    element={<DrawPage />}   />
        <Route path="qa"      element={<QAPage />}     />
        <Route path="boq"     element={<BOQPage />}    />
        <Route path="export"  element={<ExportPage />} />
      </Route>
    </Routes>
  )
}
