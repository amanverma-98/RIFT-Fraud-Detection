import { useEffect, useRef } from 'react'
import { useSelector } from 'react-redux'
import { selectLogs, selectError } from '../store/fraudSlice'

const LOG_COLORS = {
  ok:   'text-emerald-400',
  warn: 'text-warn',
  err:  'text-danger',
  info: 'text-cyan-400',
}

export default function LogTerminal({ maxHeight = 220 }) {
  const logs  = useSelector(selectLogs)
  const error = useSelector(selectError)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  if (logs.length === 0) return null

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-emerald-400 font-bold text-sm px-2">Analysis Log</h3>
      <div
        className="rounded-2xl border border-emerald-600/30 bg-surface/30 overflow-y-auto p-4 backdrop-blur-lg shadow-2xl shadow-black/20"
        style={{ maxHeight, fontFamily: "'Courier New', monospace" }}
      >
        {logs.map((l) => (
          <div key={l.id} className="flex gap-3 text-xs leading-loose border-b border-emerald-600/20 last:border-0 py-2">
            <span className="text-muted/70 shrink-0 w-[72px] font-medium">[{l.time}]</span>
            <span className={LOG_COLORS[l.type] || 'text-ink font-medium'}>{l.msg}</span>
          </div>
        ))}
        <div ref={endRef} />

        {error && (
          <div className="mt-4 p-4 rounded-xl border border-danger/50 bg-red-950/30 text-danger text-xs backdrop-blur-lg shadow-lg shadow-red-900/20 space-y-2">
            <div className="font-bold flex items-center gap-2">
              <span>⚠️</span> Analysis Error
            </div>
            <p className="text-muted/80">
              The backend service may be temporarily unavailable. Please wait 30 seconds and try again.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
