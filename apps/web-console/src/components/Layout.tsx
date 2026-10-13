import { NavLink, Outlet } from 'react-router-dom'
import { useHealth } from '../hooks/useApi'
import { useAppStore } from '../store/appStore'
import { useEffect } from 'react'

const NAV = [
  { to: '/',        icon: '🏠', label: 'Dashboard'  },
  { to: '/projects',icon: '📁', label: 'Projects'   },
  { to: '/draw',    icon: '📐', label: 'Drawing Gen' },
  { to: '/qa',      icon: '✅', label: 'QA Check'   },
  { to: '/boq',     icon: '💰', label: 'BOQ'        },
  { to: '/export',  icon: '📦', label: 'Export'     },
]

export default function Layout() {
  const { data: health } = useHealth()
  const setApiOnline  = useAppStore((s) => s.setApiOnline)
  const setApiVersion = useAppStore((s) => s.setApiVersion)
  const online        = useAppStore((s) => s.apiOnline)
  const version       = useAppStore((s) => s.apiVersion)

  useEffect(() => {
    if (health) {
      setApiOnline(health.status === 'ok')
      setApiVersion(health.version)
    }
  }, [health, setApiOnline, setApiVersion])

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────── */}
      <aside className="w-56 bg-slate-900 flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-slate-700">
          <div className="text-white font-bold text-lg leading-tight">🌉 BridgeCAD</div>
          <div className="text-slate-400 text-xs mt-0.5">Enterprise Suite</div>
        </div>

        <nav className="flex-1 py-4 space-y-0.5 px-2">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                ${isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <span className="text-base">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>

        {/* API status badge */}
        <div className="px-4 py-4 border-t border-slate-700">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${online ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-xs text-slate-400">
              API {online ? `v${version}` : 'offline'}
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main content ───────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
