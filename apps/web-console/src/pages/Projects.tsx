import { useState } from 'react'
import FileDropzone from '../components/FileDropzone'
import { useParseBridge } from '../hooks/useApi'
import type { ProjectSummary } from '../api/client'

export default function Projects() {
  const parser = useParseBridge()
  const [summary, setSummary] = useState<ProjectSummary | null>(null)

  const handleFile = (file: File) => {
    parser.mutate(file, {
      onSuccess: (data) => setSummary(data.project),
    })
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold text-slate-800 mb-1">📁 Projects</h1>
      <p className="text-slate-500 text-sm mb-6">Upload a BridgeCAD Excel workbook to inspect its metadata.</p>

      <FileDropzone onFile={handleFile} label="Drop BridgeCAD .xlsx workbook here" />

      {parser.isPending && (
        <div className="mt-6 text-slate-500 text-sm animate-pulse">Parsing workbook…</div>
      )}
      {parser.isError && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          ❌ {String(parser.error)}
        </div>
      )}

      {summary && (
        <div className="mt-6 bg-white border border-slate-200 rounded-xl p-6 space-y-3">
          <h2 className="font-semibold text-slate-800">✅ Project Parsed</h2>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Project Title',  summary.project_title ],
              ['Bridge Name',    summary.bridge_name   ],
              ['Chainage',       `${summary.chainage_km} km`],
              ['Total Length',   `${summary.total_length_m} m`],
              ['Spans',          summary.span_count    ],
              ['Overall Width',  `${summary.overall_width_m} m`],
            ].map(([k, v]) => (
              <div key={String(k)}>
                <dt className="text-slate-400 text-xs uppercase tracking-wide">{k}</dt>
                <dd className="font-medium text-slate-800">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  )
}
