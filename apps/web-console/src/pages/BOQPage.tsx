import { useState } from 'react'
import FileDropzone from '../components/FileDropzone'
import { useGenerateBill } from '../hooks/useApi'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const STATES = ['', 'MH', 'GJ', 'RJ', 'UP', 'MP', 'KA', 'TN', 'AP', 'TS', 'UK', 'HP']

export default function BOQPage() {
  const bill     = useGenerateBill()
  const [file,   setFile]  = useState<File | null>(null)
  const [state,  setState] = useState('')

  const result = bill.data

  const chartData = result?.sections.map((s) => ({
    name: s.code,
    amount: Math.round(s.total / 100_000) / 10,  // crores
  })) ?? []

  const fmt = (n: number) =>
    n >= 1e7
      ? `₹${(n / 1e7).toFixed(2)} Cr`
      : `₹${(n / 1e5).toFixed(1)} L`

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold text-slate-800 mb-1">💰 Bill of Quantities</h1>
      <p className="text-slate-500 text-sm mb-6">
        Extract quantities and price against MORTH 2024-25 schedule rates.
      </p>

      <FileDropzone onFile={(f) => setFile(f)} />

      <div className="mt-4 flex items-center gap-4">
        <label className="text-xs font-medium text-slate-600">
          State (PWD rate override)
          <select
            value={state}
            onChange={(e) => setState(e.target.value)}
            className="mt-1 block w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
          >
            {STATES.map((s) => <option key={s} value={s}>{s || 'National (default)'}</option>)}
          </select>
        </label>
      </div>

      <button
        disabled={!file || bill.isPending}
        onClick={() => file && bill.mutate({ file, state: state || undefined })}
        className="mt-5 w-full bg-yellow-500 hover:bg-yellow-600 disabled:bg-slate-300 text-white font-semibold py-3 rounded-xl transition-colors"
      >
        {bill.isPending ? '⏳ Extracting quantities…' : '💰 Generate BOQ'}
      </button>

      {bill.isError && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          ❌ {String(bill.error)}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-5">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Sub-total',    val: fmt(result.subtotal)           },
              { label: `Contingency (${result.contingency_pct}%)`, val: fmt(result.contingency_amount) },
              { label: 'Grand Total',  val: fmt(result.grand_total)        },
            ].map((s) => (
              <div key={s.label} className="bg-white border border-slate-200 rounded-xl p-4 text-center">
                <div className="text-lg font-bold text-slate-800">{s.val}</div>
                <div className="text-xs text-slate-400 mt-1">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Bar chart */}
          {chartData.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Cost by Chapter (₹ Crores)</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} unit=" Cr" />
                  <Tooltip formatter={(v: number) => [`₹${v} Cr`, 'Amount']} />
                  <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Item table */}
          {result.sections.map((sec) => (
            <div key={sec.code} className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <div className="px-5 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-700">{sec.code} — {sec.title}</span>
                <span className="text-sm font-bold text-blue-600">{fmt(sec.total)}</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="text-slate-400 uppercase">
                    <tr>
                      <th className="px-4 py-2 text-left">Code</th>
                      <th className="px-4 py-2 text-left">Description</th>
                      <th className="px-4 py-2">Unit</th>
                      <th className="px-4 py-2 text-right">Qty</th>
                      <th className="px-4 py-2 text-right">Rate</th>
                      <th className="px-4 py-2 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 text-slate-600">
                    {sec.items.map((item) => (
                      <tr key={item.code}>
                        <td className="px-4 py-1.5 font-mono">{item.code}</td>
                        <td className="px-4 py-1.5 max-w-xs">{item.desc}</td>
                        <td className="px-4 py-1.5 text-center">{item.unit}</td>
                        <td className="px-4 py-1.5 text-right">{item.qty.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                        <td className="px-4 py-1.5 text-right">{item.rate ? `₹${item.rate.toLocaleString('en-IN')}` : '—'}</td>
                        <td className="px-4 py-1.5 text-right font-medium">{item.amount ? `₹${item.amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
