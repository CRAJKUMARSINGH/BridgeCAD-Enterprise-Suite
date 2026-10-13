import { useHealth } from '../hooks/useApi'
import { useAppStore } from '../store/appStore'
import { Link } from 'react-router-dom'

const CARDS = [
  { to: '/draw',    icon: '📐', title: 'Drawing Gen',  desc: 'Generate 7-sheet DXF GAD package',  color: 'blue'   },
  { to: '/qa',      icon: '✅', title: 'QA Validate',  desc: 'IRC:SP:55 compliance — 30 checks',  color: 'green'  },
  { to: '/boq',     icon: '💰', title: 'BOQ',          desc: 'Priced MORTH bill of quantities',   color: 'yellow' },
  { to: '/export',  icon: '📦', title: 'Export Bundle',desc: 'Full ZIP: DXF + BOQ + QA report',   color: 'purple' },
  { to: '/projects',icon: '📁', title: 'Projects',     desc: 'Upload & manage bridge workbooks',  color: 'slate'  },
]

const COLOR: Record<string, string> = {
  blue:   'border-blue-200   bg-blue-50   hover:border-blue-400',
  green:  'border-green-200  bg-green-50  hover:border-green-400',
  yellow: 'border-yellow-200 bg-yellow-50 hover:border-yellow-400',
  purple: 'border-purple-200 bg-purple-50 hover:border-purple-400',
  slate:  'border-slate-200  bg-slate-50  hover:border-slate-400',
}

export default function Dashboard() {
  const { data: health, isError } = useHealth()
  const version = useAppStore((s) => s.apiVersion)

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">🌉 BridgeCAD Enterprise</h1>
      <p className="text-slate-500 mb-6 text-sm">AI-powered bridge GAD generation system</p>

      {/* API status banner */}
      {health ? (
        <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl px-5 py-3 mb-8">
          <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
          <div>
            <span className="font-semibold text-green-800 text-sm">API Online</span>
            <span className="text-green-700 text-xs ml-2">v{health.version}</span>
          </div>
          <div className="ml-auto flex gap-1 flex-wrap">
            {health.packages_loaded.map((p) => (
              <span key={p} className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">{p}</span>
            ))}
          </div>
        </div>
      ) : isError ? (
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-3 mb-8 text-red-700 text-sm">
          ⚠️ API offline — start it with <code className="bg-red-100 px-1 rounded">make api</code>
        </div>
      ) : (
        <div className="bg-slate-100 rounded-xl px-5 py-3 mb-8 text-slate-500 text-sm animate-pulse">
          Connecting to API...
        </div>
      )}

      {/* Feature cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
        {CARDS.map((c) => (
          <Link
            key={c.to}
            to={c.to}
            className={`block border-2 rounded-xl p-5 transition-all ${COLOR[c.color]}`}
          >
            <div className="text-2xl mb-2">{c.icon}</div>
            <div className="font-semibold text-slate-800">{c.title}</div>
            <div className="text-sm text-slate-500 mt-1">{c.desc}</div>
          </Link>
        ))}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Enum types',      value: '200+' },
          { label: 'Model fields',    value: '427'  },
          { label: 'DXF sheets',      value: '7'    },
          { label: 'MORTH rate items',value: '90'   },
        ].map((s) => (
          <div key={s.label} className="bg-white border border-slate-200 rounded-xl px-5 py-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{s.value}</div>
            <div className="text-xs text-slate-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
