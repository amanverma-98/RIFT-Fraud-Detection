import { useSelector } from 'react-redux'
import { selectReport } from '../store/fraudSlice'
import { RING_COLORS } from '../utils/graphHelpers'

export default function FraudRingsTable() {
  const report = useSelector(selectReport)
  if (!report?.fraud_rings?.length) return (
    <div className="text-muted text-sm text-center py-10">No fraud rings detected.</div>
  )

  return (
    <div className="bg-card border border-emerald-600/30 rounded-xl overflow-auto shadow-lg shadow-emerald-600/10 backdrop-blur-sm">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="bg-surface border-b border-emerald-600/30">
            {['RING ID', 'PATTERN TYPE', 'MEMBER COUNT', 'RISK SCORE', 'MEMBER ACCOUNT IDs'].map((h) => (
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
          {report.fraud_rings.map((ring, i) => {
            const col = RING_COLORS[i % RING_COLORS.length]
            return (
              <tr
                key={ring.ring_id}
                className="border-b border-emerald-600/20 hover:bg-emerald-600/10 transition-all"
              >
                {/* Ring ID */}
                <td className="px-4 py-3">
                  <span
                    className="px-2 py-1 rounded font-bold text-xs transition-all hover:shadow-lg"
                    style={{ background: col + '18', border: `1px solid ${col}66`, color: col }}
                  >
                    {ring.ring_id}
                  </span>
                </td>

                {/* Pattern */}
                <td className="px-4 py-3 text-ink font-mono">
                  {ring.pattern_type.toUpperCase()}
                </td>

                {/* Member count */}
                <td className="px-4 py-3">
                  <span
                    className="text-2xl font-black"
                    style={{ color: ring.member_accounts.length >= 4 ? '#ff2d55' : '#ffaa00' }}
                  >
                    {ring.member_accounts.length}
                  </span>
                </td>

                {/* Risk score bar */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-emerald-900/50 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${ring.risk_score}%`,
                          background: 'linear-gradient(90deg, #FFB347, #ff2d55)',
                        }}
                      />
                    </div>
                    <span className="text-danger font-black">{ring.risk_score}</span>
                  </div>
                </td>

                {/* Members */}
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {ring.member_accounts.map((a) => (
                      <span
                        key={a}
                        className="px-2 py-0.5 rounded text-xs bg-emerald-900/30 text-ink border border-emerald-600/30 hover:bg-emerald-600/20 transition-all"
                      >
                        {a}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
