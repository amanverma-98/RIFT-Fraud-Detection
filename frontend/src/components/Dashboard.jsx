import { useSelector } from 'react-redux'
import { selectReport, selectTransactions } from '../store/fraudSlice'

function KpiCard({ label, value, color, sub }) {
  const borderColor = {
    accent:  'border-emerald-600/50',
    warn:    'border-warn/40',
    danger:  'border-danger/40',
    success: 'border-emerald-500/50',
  }[color] || 'border-emerald-600/40'

  const textColor = {
    accent:  'text-emerald-400',
    warn:    'text-warn',
    danger:  'text-danger',
    success: 'text-emerald-400',
  }[color] || 'text-ink'

  const bgGradient = {
    accent:  'bg-gradient-to-br from-emerald-900/20 to-emerald-800/10',
    warn:    'bg-gradient-to-br from-warn/15 to-warn/5',
    danger:  'bg-gradient-to-br from-danger/15 to-danger/5',
    success: 'bg-gradient-to-br from-emerald-900/20 to-cyan-900/10',
  }[color] || 'bg-gradient-to-br from-emerald-900/15 to-emerald-800/5'

  return (
    <div className={`flex-1 min-w-0 ${bgGradient} rounded-xl p-4 border ${borderColor} animate-fadeIn backdrop-blur-sm transition-all hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-600/10`}>
      <p className="text-muted mb-2 tracking-widest" style={{ fontSize: 9 }}>{label}</p>
      <p className={`font-black leading-none text-4xl font-mono ${textColor}`}>{value}</p>
      {sub && <p className="text-muted mt-1 text-xs">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const report = useSelector(selectReport)
  const txns   = useSelector(selectTransactions)

  if (!report) return null

  return (
    <div className="flex gap-3">
      <KpiCard
        label="ACCOUNTS ANALYZED"
        value={report.summary.total_accounts_analyzed}
        color="accent"
      />
      <KpiCard
        label="SUSPICIOUS ACCOUNTS"
        value={report.summary.suspicious_accounts_flagged}
        color="warn"
        sub="sorted by score ↓"
      />
      <KpiCard
        label="FRAUD RINGS DETECTED"
        value={report.summary.fraud_rings_detected}
        color="danger"
        sub="cycle / smurfing / shell"
      />
      <KpiCard
        label="TRANSACTION EDGES"
        value={txns.length}
        color="success"
        sub="from batch API"
      />
    </div>
  )
}
