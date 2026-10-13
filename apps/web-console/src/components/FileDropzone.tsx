/**
 * Reusable file dropzone — accepts .xlsx files for all pages.
 */
import { useCallback, useRef, useState } from 'react'
import { useAppStore } from '../store/appStore'

interface Props {
  onFile: (f: File) => void
  label?: string
  accept?: string
}

export default function FileDropzone({ onFile, label = 'Drop BridgeCAD Excel here', accept = '.xlsx' }: Props) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const activeFile = useAppStore((s) => s.activeFile)

  const handle = useCallback((f: File) => {
    useAppStore.getState().setActiveFile(f)
    onFile(f)
  }, [onFile])

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault(); setDragging(false)
        const f = e.dataTransfer.files[0]
        if (f) handle(f)
      }}
      onClick={() => inputRef.current?.click()}
      className={`
        border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
        ${dragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-blue-400 bg-white'}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handle(f) }}
      />
      <div className="text-3xl mb-2">📂</div>
      {activeFile
        ? <p className="text-sm font-medium text-slate-700">📄 {activeFile.name}</p>
        : <p className="text-sm text-slate-500">{label}</p>
      }
      <p className="text-xs text-slate-400 mt-1">or click to browse</p>
    </div>
  )
}
