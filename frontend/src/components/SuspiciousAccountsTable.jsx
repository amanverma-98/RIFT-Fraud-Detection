import { useSelector } from 'react-redux'
import { selectReport } from '../store/fraudSlice'

function PatternBadge({ pattern }) {
  const isCycle = pattern.includes('cycle')
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-bold border font-mono transition-all ${
        isCycle
          ? 'bg-danger/25 border-danger/70 text-danger'
          : 'bg-warn/25 border-warn/70 text-warn'
      }`}
    >
      {pattern.replace(/_/g, ' ')}
    </span>
  )
}

export default function SuspiciousAccountsTable() {
  const report = useSelector(selectReport)
  if (!report?.suspicious_accounts?.length) return (
    <div className="text-muted text-sm text-center py-10">No suspicious accounts detected.</div>
  )

  const sorted = [...report.suspicious_accounts].sort(
    (a, b) => b.suspicion_score - a.suspicion_score
  )

  return (
    <div className="bg-card border border-emerald-600/30 rounded-xl overflow-auto shadow-lg shadow-emerald-600/10 backdrop-blur-sm">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="bg-surface border-b border-emerald-600/30">
            {['ACCOUNT ID', 'SUSPICION SCORE', 'DETECTED PATTERNS', 'RING ID'].map((h) => (
              <th
                key={h}
                className="text-left px-4 py-3 text-muted tracking-widest hover:text-emerald-400 transition-colors"
                style={{ fontSize: 9 }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((acc) => (
            <tr
              key={acc.account_id}
              className="border-b border-emerald-600/20 hover:bg-emerald-600/10 transition-all"
            >
              {/* Account ID */}
              <td className="px-4 py-3 font-bold text-ink">{acc.account_id}</td>

              {/* Score bar */}
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-24 h-1.5 bg-emerald-900/50 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${acc.suspicion_score}%`,
                        background:
                          acc.suspicion_score > 50
                            ? 'linear-gradient(90deg, #FFB347, #ff2d55)'
                            : 'linear-gradient(90deg, #88976C, #FFB347)',
                      }}
                    />
                  </div>
                  <span
                    className="font-black"
                    style={{ color: acc.suspicion_score > 50 ? '#ff2d55' : '#ffaa00' }}
                  >
                    {acc.suspicion_score}
                  </span>
                </div>
              </td>

              {/* Patterns */}
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {acc.detected_patterns.map((p) => (
                    <PatternBadge key={p} pattern={p} />
                  ))}
                </div>
              </td>

              {/* Ring */}
              <td className="px-4 py-3">
                {acc.ring_id ? (
                  <span className="text-danger font-black">{acc.ring_id}</span>
                ) : (
                  <span className="text-muted">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
