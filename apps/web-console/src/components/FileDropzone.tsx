/**
 * Reusable file dropzone — accepts .xlsx files for all pages.
 *
 * The selected file is owned by the parent page and passed back in via `file`,
 * so each page reflects its own state rather than a shared global.
 */
import { useCallback, useRef, useState } from 'react'

interface Props {
  onFile: (f: File) => void
  file?: File | null
  label?: string
  accept?: string
}

export default function FileDropzone({ onFile, file = null, label = 'Drop BridgeCAD Excel here', accept = '.xlsx' }: Props) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const openPicker = useCallback(() => inputRef.current?.click(), [])

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={label}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault(); setDragging(false)
        const f = e.dataTransfer.files[0]
        if (f) onFile(f)
      }}
      onClick={openPicker}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openPicker() }
      }}
      className={`
        border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
        ${dragging
          ? 'border-blue-500 bg-blue-50 scale-[1.01] shadow-md'
          : 'border-slate-300 hover:border-blue-400 bg-white lift'}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onFile(f)
          e.target.value = ''   // allow re-selecting the same file
        }}
      />
      <div className="text-3xl mb-2" aria-hidden="true">📂</div>
      {file
        ? <p className="text-sm font-medium text-slate-700">📄 {file.name}</p>
        : <p className="text-sm text-slate-500">{label}</p>
      }
      <p className="text-xs text-slate-400 mt-1">or click to browse</p>
    </div>
  )
}
