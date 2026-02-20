// import { useState, useCallback } from 'react'
// import { useDispatch, useSelector } from 'react-redux'
// import { runFullPipeline, selectStep } from '../store/fraudSlice'

// export default function UploadZone() {
//   const dispatch = useDispatch()
//   const step     = useSelector(selectStep)
//   const [drag, setDrag] = useState(false)
//   const [file, setFile] = useState(null)

//   const accept = useCallback((f) => {
//     if (!f || !f.name.endsWith('.csv')) return
//     setFile(f)
//   }, [])

//   const handleDrop = (e) => {
//     e.preventDefault()
//     setDrag(false)
//     accept(e.dataTransfer.files[0])
//   }

//   const handleRun = () => {
//     if (!file) return
//     dispatch(runFullPipeline(file))
//   }

//   const busy = step === 'uploading' || step === 'analyzing'

//   return (
//     <div className="flex flex-col gap-4">
//       {/* Drop zone */}
//       <div
//         onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
//         onDragLeave={() => setDrag(false)}
//         onDrop={handleDrop}
//         onClick={() => !busy && document.getElementById('csv-input').click()}
//         className={`
//           relative rounded-xl border-2 border-dashed p-10 text-center transition-all cursor-pointer select-none
//           ${drag  ? 'border-accent bg-accent/5'   : ''}
//           ${file && !drag ? 'border-success bg-success/5' : ''}
//           ${!file && !drag ? 'border-border bg-card hover:border-muted' : ''}
//           ${busy ? 'pointer-events-none opacity-60' : ''}
//         `}
//       >
//         <input
//           id="csv-input"
//           type="file"
//           accept=".csv"
//           className="hidden"
//           onChange={(e) => accept(e.target.files[0])}
//         />

//         <div className="text-4xl mb-3">📁</div>

//         <p className={`font-black tracking-widest text-sm ${file ? 'text-success' : 'text-ink'}`}>
//           {file ? `✓  ${file.name}` : 'DROP CSV FILE HERE OR CLICK TO BROWSE'}
//         </p>

//         <p className="text-muted mt-2" style={{ fontSize: 10, letterSpacing: '0.1em' }}>
//           Required columns: transaction_id · sender_id · receiver_id · amount · timestamp
//         </p>

//         {file && !busy && (
//           <p className="text-subtle mt-1" style={{ fontSize: 10 }}>
//             {(file.size / 1024).toFixed(1)} KB · ready to analyze
//           </p>
//         )}
//       </div>

//       {/* Run button */}
//       {file && !busy && (
//         <button
//           onClick={handleRun}
//           className="w-full py-3 text-sm font-black tracking-widest border border-accent text-accent rounded-lg bg-accent/10 hover:bg-accent/20 transition-colors"
//         >
//           ▶ RUN FORENSIC ANALYSIS
//         </button>
//       )}

//       {/* Processing indicator */}
//       {busy && (
//         <div className="flex items-center gap-3 px-4 py-3 rounded-lg border border-border bg-card">
//           <div className="w-3 h-3 rounded-full bg-accent animate-pulse" />
//           <span className="text-accent text-xs tracking-widest">
//             {step === 'uploading' ? 'UPLOADING DATA…' : 'RUNNING GRAPH ANALYSIS…'}
//           </span>
//           <span className="ml-auto text-muted animate-blink">█</span>
//         </div>
//       )}
//     </div>
//   )
// }
import { useState, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { runFullPipeline, selectStep } from '../store/fraudSlice'

export default function UploadZone() {
  const dispatch = useDispatch()
  const step = useSelector(selectStep)
  const [drag, setDrag] = useState(false)
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)

  const accept = useCallback((f) => {
    if (!f || !f.name.endsWith('.csv')) return
    setFile(f)
    setError(null)
  }, [])

  const handleDrop = (e) => {
    e.preventDefault()
    setDrag(false)
    accept(e.dataTransfer.files[0])
  }

  const handleRun = () => {
    if (!file) return
    dispatch(runFullPipeline(file))
  }

  const busy = step === 'uploading' || step === 'analyzing'

  return (
    <div id="upload-section" className="max-w-4xl mx-auto p-6 space-y-8">
      
      {/* Error Message matching screenshot */}
      {error && (
        <div className="bg-red-950/50 border border-danger/50 rounded-xl p-5 flex items-center gap-3 text-danger text-sm backdrop-blur-lg shadow-lg shadow-red-900/20 transition-all">
          <span className="text-lg">⚠️</span>
          <span className="flex-1 font-medium">{error}</span>
          <button onClick={() => setError(null)} className="text-danger/60 hover:text-danger transition-colors font-bold">✕</button>
        </div>
      )}

      {/* Main Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
        onClick={() => !busy && document.getElementById('csv-input').click()}
        className={`
          relative rounded-2xl border-2 border-dashed p-20 flex flex-col items-center justify-center transition-all cursor-pointer backdrop-blur-lg shadow-2xl
          ${drag ? 'border-emerald-500 bg-gradient-to-br from-emerald-600/20 to-cyan-600/20 shadow-emerald-600/40' : 'border-emerald-600/40 bg-gradient-to-br from-emerald-600/10 to-cyan-600/5 hover:from-emerald-600/15 hover:to-cyan-600/10 hover:border-emerald-500/60 hover:shadow-emerald-600/30'}
        `}
      >
        <input id="csv-input" type="file" accept=".csv" className="hidden" onChange={(e) => accept(e.target.files[0])} />
        
        <div className="mb-6 transform transition-transform hover:scale-110 duration-300">
          <svg className="w-16 h-16 text-emerald-500 opacity-90" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
          </svg>
        </div>

        <h2 className="text-ink text-2xl font-bold mb-3 text-center">Drag your CSV file here</h2>
        <p className="text-muted text-sm text-center leading-relaxed max-w-md">
          Upload transaction data for analysis. Accepted format: CSV with columns (transaction_id, sender_id, receiver_id, amount, timestamp)
        </p>
      </div>

      {/* File List Item & Analyze Button */}
      {file && (
        <div className="bg-surface/50 border border-emerald-600/40 rounded-2xl p-6 flex items-center justify-between hover:border-emerald-500/60 transition-all backdrop-blur-lg shadow-2xl shadow-emerald-600/20 hover:shadow-emerald-600/30">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-600/30 to-cyan-600/20 flex items-center justify-center">
              <div className="text-emerald-400 text-2xl font-bold">✓</div>
            </div>
            <div>
              <div className="text-ink font-semibold text-base">{file.name}</div>
              <div className="text-muted text-xs font-medium">{(file.size / 1024).toFixed(0)} KB · Ready to analyze</div>
            </div>
          </div>
          <button
            onClick={handleRun}
            disabled={busy}
            className="bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white px-8 py-3 rounded-lg font-bold text-sm transition-all shadow-xl shadow-emerald-600/40 hover:shadow-emerald-600/60 disabled:opacity-60 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95 duration-200"
          >
            {busy ? '⟳ ANALYZING...' : '▶ Analyze Transactions'}
          </button>
        </div>
      )}

      {/* Expected Format Table matching screenshot */}
      <div className="bg-surface/40 border border-emerald-600/30 rounded-2xl p-10 backdrop-blur-lg shadow-2xl shadow-black/10 hover:border-emerald-600/40 transition-all">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <h3 className="text-emerald-400 font-bold text-lg">Expected CSV Format</h3>
        </div>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-emerald-300 text-xs border-b border-emerald-600/30 font-semibold tracking-wider uppercase">
              <th className="pb-5">Column Name</th>
              <th className="pb-5">Data Type</th>
              <th className="pb-5">Example</th>
            </tr>
          </thead>
          <tbody className="text-ink divide-y divide-emerald-600/20">
            {[
              ['transaction_id', 'String', 'TXN001'],
              ['sender_id', 'String', 'Alice'],
              ['receiver_id', 'String', 'Bob'],
              ['amount', 'Float', '1000.50'],
              ['timestamp', 'DateTime', '2026-02-19 10:00:00']
            ].map(([col, type, ex]) => (
              <tr key={col} className="hover:bg-emerald-600/15 transition-all duration-200">
                <td className="py-5 font-mono text-emerald-300 font-medium">{col}</td>
                <td className="py-5 text-muted">{type}</td>
                <td className="py-5 text-muted/80">{ex}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}