import { useDispatch, useSelector } from 'react-redux'
import { reset, selectStep, selectReportId } from '../store/fraudSlice'
import { fraudApi } from '../api/fraudApi'

export default function Header({ showUpload }) {
  const dispatch  = useDispatch()
  const step      = useSelector(selectStep)
  const reportId  = useSelector(selectReportId)

  const STATUS = {
    idle:      { label: 'STANDBY',    cls: 'border-muted text-muted' },
    uploading: { label: 'UPLOADING',  cls: 'border-emerald-500 text-emerald-400 animate-pulse' },
    analyzing: { label: 'ANALYZING', cls: 'border-warn text-warn animate-pulse' },
    done:      { label: 'COMPLETE',   cls: 'border-emerald-500 text-emerald-400' },
    error:     { label: 'ERROR',      cls: 'border-danger text-danger' },
  }

  const { label, cls } = STATUS[step] || STATUS.idle

  const handleDownload = async () => {
    if (!reportId) return
    try {
      const data = await fraudApi.downloadJson(reportId)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url  = URL.createObjectURL(blob)
      Object.assign(document.createElement('a'), { href: url, download: `${reportId}.json` }).click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error('Download failed', e)
    }
  }

  return (
    <header className={`sticky top-0 z-50 flex items-center justify-between px-6 py-3 border-b transition-all duration-300 ${
      showUpload 
        ? 'bg-surface/80 border-emerald-600/20 backdrop-blur-lg shadow-lg shadow-black/20' 
        : 'bg-surface border-emerald-600/20 backdrop-blur-sm'
    }`}>
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg bg-gradient-to-br from-emerald-600 to-cyan-500 font-mono font-black text-white shadow-lg shadow-emerald-600/30">
          ⬡
        </div>
        <div>
          <p className="text-emerald-400 font-black tracking-widest text-sm">RIFT FORENSICS ENGINE</p>
          <p className="text-muted tracking-widest" style={{ fontSize: 9 }}>
            MONEY MULING DETECTION · GRAPH THEORY TRACK 2026
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {step === 'done' && (
          <button
            onClick={handleDownload}
            className="px-3 py-1.5 text-xs font-bold tracking-widest border border-emerald-500/70 text-emerald-400 rounded-md bg-emerald-600/10 hover:bg-emerald-600/20 transition-all hover:shadow-lg hover:shadow-emerald-600/20"
          >
            ⬇ DOWNLOAD JSON
          </button>
        )}
        {step === 'done' && (
          <button
            onClick={() => dispatch(reset())}
            className="px-3 py-1.5 text-xs font-bold tracking-widest border border-muted/40 text-muted rounded-md hover:bg-emerald-600/10 hover:border-emerald-500/40 transition-all"
          >
            ↺ RESET
          </button>
        )}
        <span className={`px-3 py-1 text-xs font-bold tracking-widest border rounded ${cls}`}>
          {label}
        </span>
      </div>
    </header>
  )
}
