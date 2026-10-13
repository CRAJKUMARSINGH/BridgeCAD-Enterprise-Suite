import { useState } from 'react'
import FileDropzone from '../components/FileDropzone'
import { useDrawGAD } from '../hooks/useApi'

export default function DrawPage() {
  const draw     = useDrawGAD()
  const [scale,  setScale]  = useState(100)
  const [prefix, setPrefix] = useState('GAD')
  const [file,   setFile]   = useState<File | null>(null)

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold text-slate-800 mb-1">📐 Drawing Generator</h1>
      <p className="text-slate-500 text-sm mb-6">
        Upload a BridgeCAD Excel workbook and download a 7-sheet DXF GAD package.
      </p>

      <FileDropzone onFile={(f) => setFile(f)} />

      <div className="mt-5 grid grid-cols-2 gap-4">
        <label className="block">
          <span className="text-xs font-medium text-slate-600">Plot scale (1 : N)</span>
          <input
            type="number"
            value={scale}
            onChange={(e) => setScale(Number(e.target.value))}
            className="mt-1 block w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-slate-600">File prefix</span>
          <input
            type="text"
            value={prefix}
            onChange={(e) => setPrefix(e.target.value)}
            className="mt-1 block w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
          />
        </label>
      </div>

      <button
        disabled={!file || draw.isPending}
        onClick={() => file && draw.mutate({ file, scale, prefix })}
        className="mt-5 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-semibold py-3 rounded-xl transition-colors"
      >
        {draw.isPending ? '⏳ Generating…' : '🚀 Generate 7-Sheet DXF Package'}
      </button>

      {draw.isError && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          ❌ {String(draw.error)}
        </div>
      )}
      {draw.isSuccess && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-xl p-4 text-green-700 text-sm">
          ✅ DXF package downloaded successfully!
        </div>
      )}

      <div className="mt-8 bg-slate-50 border border-slate-200 rounded-xl p-5">
        <h3 className="font-semibold text-slate-700 mb-3 text-sm">Sheets in the package</h3>
        <ol className="space-y-1 text-sm text-slate-600">
          {[
            'Plan View',
            'Longitudinal Section',
            'Typical Mid-Span Cross Section',
            'Foundation Details',
            'Pier & Abutment Details',
            'Bearings & Expansion Joints Schedule',
            'Abstract Bill of Quantities',
          ].map((s, i) => (
            <li key={i} className="flex items-center gap-2">
              <span className="text-blue-500 font-mono text-xs w-5">S{i + 1}</span>
              {s}
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
