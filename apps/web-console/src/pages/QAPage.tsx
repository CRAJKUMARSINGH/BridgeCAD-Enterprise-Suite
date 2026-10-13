import { useState } from 'react'
import FileDropzone from '../components/FileDropzone'
import { useValidateBridge } from '../hooks/useApi'
import type { QAFinding } from '../api/client'

const GRADE_COLOR: Record<string, string> = {
  'A+': 'text-green-600',  A: 'text-green-500',
  B:    'text-yellow-500', C: 'text-orange-500',
  D:    'text-red-500',    F: 'text-red-700',
}

export default function QAPage() {
  const validate = useValidateBridge()
  const [file,    setFile]   = useState<File | null>(null)

  const result = validate.data

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold text-slate-800 mb-1">✅ QA Compliance Check</h1>
      <p className="text-slate-500 text-sm mb-6">
        Runs 30 checks (25 Critical + 5 Warning) mapped to IRC:5, IRC:112, IRC SP:55, MORTH.
      </p>

      <FileDropzone onFile={(f) => { setFile(f) }} />

      <button
        disabled={!file || validate.isPending}
        onClick={() => file && validate.mutate(file)}
        className="mt-5 w-full bg-green-600 hover:bg-green-700 disabled:bg-slate-300 text-white font-semibold py-3 rounded-xl transition-colors"
      >
        {validate.isPending ? '⏳ Running 30 checks…' : '🔍 Validate Now'}
      </button>

      {validate.isError && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          ❌ {String(validate.error)}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-5">
          {/* Score card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 flex items-center gap-6">
            <div className="text-center">
              <div className={`text-5xl font-black ${GRADE_COLOR[result.grade] ?? 'text-slate-700'}`}>
                {result.score}
              </div>
              <div className="text-xs text-slate-400 mt-1">/ 100</div>
            </div>
            <div className="flex-1">
              <div className={`text-2xl font-bold ${GRADE_COLOR[result.grade]}`}>Grade {result.grade}</div>
              <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
                <div><span className="text-red-600 font-semibold">{result.critical_fails}</span> Critical fails</div>
                <div><span className="text-yellow-500 font-semibold">{result.warning_fails}</span> Warning fails</div>
              </div>
            </div>
          </div>

          {/* Findings table */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-100 text-sm font-semibold text-slate-700">
              Check Results ({result.findings.length} total)
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-4 py-2 text-left">ID</th>
                    <th className="px-4 py-2 text-left">Severity</th>
                    <th className="px-4 py-2 text-left">Description</th>
                    <th className="px-4 py-2 text-left">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {result.findings.map((f: QAFinding) => (
                    <tr key={f.check_id} className={!f.passed ? 'bg-red-50' : ''}>
                      <td className="px-4 py-2 font-mono text-xs">{f.check_id}</td>
                      <td className="px-4 py-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          f.severity === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                          f.severity === 'WARNING'  ? 'bg-yellow-100 text-yellow-700' :
                          'bg-slate-100 text-slate-600'
                        }`}>{f.severity}</span>
                      </td>
                      <td className="px-4 py-2 text-slate-600 max-w-xs truncate">{f.description}</td>
                      <td className="px-4 py-2">
                        {f.passed
                          ? <span className="text-green-600 font-semibold">✓ PASS</span>
                          : <span className="text-red-600 font-semibold">✗ FAIL</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
