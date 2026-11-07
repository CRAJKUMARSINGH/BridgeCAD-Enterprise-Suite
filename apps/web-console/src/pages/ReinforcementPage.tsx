import { useRef, useState } from 'react'
import FileDropzone from '../components/FileDropzone'
import { projectApi, type PatchCheck, type PatchResult } from '../api/client'

const FIELD_SPECS = [
  { section: 'substructure', field: 'abutment_cap_depth_mm', label: 'Cap depth', unit: 'mm', step: 50 },
  { section: 'substructure', field: 'abutment_cap_projection_front_mm', label: 'Cap proj. front', unit: 'mm', step: 50 },
  { section: 'substructure', field: 'abutment_cap_projection_rear_mm', label: 'Cap proj. rear', unit: 'mm', step: 50 },
  { section: 'substructure', field: 'dirt_wall_thickness_mm', label: 'Dirt wall thickness', unit: 'mm', step: 50 },
  { section: 'substructure', field: 'dirt_wall_weep_holes_count', label: 'Weep holes', unit: 'no', step: 1 },
  { section: 'substructure', field: 'abutment_main_bar_dia_mm', label: 'Main bar dia', unit: 'mm', step: 2 },
  { section: 'substructure', field: 'abutment_main_bar_spacing_mm', label: 'Main bar spacing', unit: 'mm', step: 25 },
] as const

export default function ReinforcementPage() {
  const [file, setFile] = useState<File | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [checks, setChecks] = useState<PatchCheck[]>([])
  const [qa, setQa] = useState<PatchResult['qa'] | null>(null)
  const [pending, setPending] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputs = useRef<Record<string, HTMLInputElement | null>>({})

  const handleFile = async (f: File) => {
    setFile(f)
    setError(null)
    try {
      const res = await projectApi.load(f)
      setToken(res.token)
    } catch (e) {
      setError(String(e))
    }
  }

  async function patch(section: string, field: string, raw: string) {
    if (!token) return
    const value = Number(raw)
    if (Number.isNaN(value)) return
    setPending(field)
    setError(null)
    try {
      const res = await projectApi.patch(token, section, field, value)
      setChecks(res.checks)
      setQa(res.qa)
    } catch (e) {
      setError(String(e))
    } finally {
      setPending(null)
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold text-slate-800 mb-1">🧱 Reinforcement & Abutment</h1>
      <p className="text-slate-500 text-sm mb-6">
        Load a workbook, then patch bar and cap fields — checks and QA update in one action.
      </p>

      <FileDropzone file={file} onFile={handleFile} label="Drop BridgeCAD .xlsx workbook here" />
      {error && <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">❌ {error}</div>}

      {token && (
        <div className="rise-in mt-6 glass-panel p-6">
          <h2 className="font-semibold text-slate-800 mb-4">Abutment & reinforcement fields</h2>
          <div className="grid grid-cols-2 gap-3">
            {FIELD_SPECS.map((s) => (
              <label key={s.field} className="flex flex-col text-xs text-slate-600">
                {s.label} <span className="text-slate-400">({s.unit})</span>
                <input
                  type="number"
                  step={s.step}
                  disabled={pending === s.field}
                  ref={(el) => { inputs.current[s.field] = el }}
                  onBlur={(e) => patch(s.section, s.field, e.target.value)}
                  className="border border-slate-300 rounded px-2 py-1 mt-1 disabled:opacity-50"
                />
              </label>
            ))}
          </div>

          {checks.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Checks</h3>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-400 uppercase">
                    <th className="py-1">Rule</th><th>Value</th><th>Limit</th><th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {checks.map((c) => (
                    <tr key={c.id} className="border-t border-slate-100">
                      <td className="py-1 font-mono">{c.id}</td>
                      <td>{c.parameter}: {c.value}</td>
                      <td>{c.limit}</td>
                      <td className={c.ok ? 'text-green-600' : 'text-red-600 font-semibold'}>
                        {c.ok ? 'OK' : 'FAIL'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {qa && (
            <div className="mt-4 text-sm text-slate-600">
              QA score: <span className="font-semibold">{qa.score ?? '—'}</span>
              {qa.failures != null && <> · failures: {qa.failures}</>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
