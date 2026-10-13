import { useState } from 'react'
import FileDropzone from '../components/FileDropzone'
import { useExportBundle } from '../hooks/useApi'

const STATES = ['', 'MH', 'GJ', 'RJ', 'UP', 'MP', 'KA', 'TN']

export default function ExportPage() {
  const bundle   = useExportBundle()
  const [file,   setFile]  = useState<File | null>(null)
  const [state,  setState] = useState('')
  const [scale,  setScale] = useState(100)

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold text-slate-800 mb-1">📦 Export Bundle</h1>
      <p className="text-slate-500 text-sm mb-6">
        One click: 7-sheet DXF drawings + priced BOQ (xlsx+csv) + QA HTML report → ZIP.
      </p>

      <FileDropzone onFile={(f) => setFile(f)} />

      <div className="mt-4 grid grid-cols-2 gap-4">
        <label className="block">
          <span className="text-xs font-medium text-slate-600">Drawing scale (1 : N)</span>
          <input
            type="number"
            value={scale}
            onChange={(e) => setScale(Number(e.target.value))}
            className="mt-1 block w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-slate-600">State (PWD rates)</span>
          <select
            value={state}
            onChange={(e) => setState(e.target.value)}
            className="mt-1 block w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
          >
            {STATES.map((s) => <option key={s} value={s}>{s || 'National'}</option>)}
          </select>
        </label>
      </div>

      <button
        disabled={!file || bundle.isPending}
        onClick={() => file && bundle.mutate({ file, state: state || undefined, scale })}
        className="mt-5 w-full bg-purple-600 hover:bg-purple-700 disabled:bg-slate-300 text-white font-semibold py-3 rounded-xl transition-colors"
      >
        {bundle.isPending ? '⏳ Running full pipeline…' : '⚡ Export Full Bundle'}
      </button>

      {bundle.isError && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          ❌ {String(bundle.error)}
        </div>
      )}
      {bundle.isSuccess && (
        <div className="mt-4 bg-purple-50 border border-purple-200 rounded-xl p-4 text-purple-700 text-sm">
          ✅ Bundle downloaded: <strong>bridgecad_bundle.zip</strong>
        </div>
      )}

      {/* Bundle contents info */}
      <div className="mt-8 bg-slate-50 border border-slate-200 rounded-xl p-5">
        <h3 className="font-semibold text-slate-700 mb-3 text-sm">What's inside the ZIP</h3>
        <ul className="space-y-2 text-sm text-slate-600">
          {[
            ['📁 drawings/',  '7 × .dxf files  (Plan / Long-section / Cross / Foundation / Pier / Bearings / BOQ)'],
            ['📁 bill/',      'BOQ.xlsx + BOQ.csv  (priced against MORTH 2024-25 rates)'],
            ['📁 qa/',        'QA_Report.html  (30-check IRC:SP:55 compliance report)'],
            ['📄 manifest.json','Bundle metadata: project, timestamp, contents list'],
          ].map(([k, v]) => (
            <li key={String(k)} className="flex gap-3">
              <span className="font-mono text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded shrink-0">{k}</span>
              <span className="text-slate-500 text-xs">{v}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
