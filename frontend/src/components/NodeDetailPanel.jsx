import { useDispatch, useSelector } from 'react-redux'
import { clearSelectedNode, selectSelectedNode } from '../store/uiSlice'
import { selectTransactions } from '../store/fraudSlice'
import { RING_COLORS } from '../utils/graphHelpers'

function PatternBadge({ pattern }) {
  const isCycle = pattern.includes('cycle')
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-bold font-mono border transition-all ${
        isCycle
          ? 'bg-danger/25 border-danger/70 text-danger'
          : 'bg-warn/25 border-warn/70 text-warn'
      }`}
    >
      {pattern.replace(/_/g, ' ')}
    </span>
  )
}

export default function NodeDetailPanel() {
  const dispatch = useDispatch()
  const node     = useSelector(selectSelectedNode)
  const txns     = useSelector(selectTransactions)

  if (!node) return null

  const nodeTxns = txns.filter((t) => t.sender_id === node.id || t.receiver_id === node.id)
  const sent     = nodeTxns.filter((t) => t.sender_id === node.id)
  const recv     = nodeTxns.filter((t) => t.receiver_id === node.id)
  const totalVol = nodeTxns.reduce((s, t) => s + (t.amount || 0), 0)

  const borderColor = node.ring?.col || (node.susp ? '#F59E0B' : '#10B981')

  return (
    <aside
      className="w-72 shrink-0 border-l border-emerald-600/30 bg-surface overflow-y-auto flex flex-col gap-4 p-4 animate-fadeSlide backdrop-blur-sm"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-muted tracking-widest" style={{ fontSize: 9 }}>NODE DETAILS</p>
        <button
          onClick={() => dispatch(clearSelectedNode())}
          className="text-muted hover:text-ink text-lg leading-none transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Account ID */}
      <div>
        <p className="text-muted mb-1" style={{ fontSize: 9 }}>ACCOUNT ID</p>
        <div
          className="p-3 rounded-lg bg-card font-black text-sm break-all transition-all hover:shadow-lg hover:shadow-sage-900/30"
          style={{ border: `1px solid ${borderColor}`, color: borderColor }}
        >
          {node.id}
        </div>
      </div>

      {/* Status */}
      <div>
        <p className="text-muted mb-2" style={{ fontSize: 9 }}>STATUS</p>
        {node.ring ? (
          <span
            className="inline-block px-3 py-1 rounded font-bold text-xs border transition-all"
            style={{ background: node.ring.col + '22', border: `1px solid ${node.ring.col}`, color: node.ring.col }}
          >
            FRAUD RING MEMBER
          </span>
        ) : node.susp ? (
          <span className="inline-block px-3 py-1 rounded font-bold text-xs border border-warn/70 bg-warn/25 text-warn transition-all">
            SUSPICIOUS
          </span>
        ) : (
          <span className="inline-block px-3 py-1 rounded font-bold text-xs border border-emerald-500/70 bg-emerald-600/15 text-emerald-400 transition-all">
            NORMAL
          </span>
        )}
      </div>

      {/* Suspicion score */}
      {node.score > 0 && (
        <div>
          <p className="text-muted mb-2" style={{ fontSize: 9 }}>SUSPICION SCORE</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-emerald-900/40 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${node.score}%`,
                  background: 'linear-gradient(90deg, #F59E0B, #EF4444)',
                }}
              />
              />
            </div>
            <span className="text-danger font-black text-base">{node.score}</span>
          </div>
        </div>
      )}

      {/* Ring membership */}
      {node.ring && (
        <div>
          <p className="text-muted mb-2" style={{ fontSize: 9 }}>RING MEMBERSHIP</p>
          <div
            className="p-3 rounded-lg transition-all hover:shadow-lg hover:shadow-emerald-600/20"
            style={{ background: node.ring.col + '15', border: `1px solid ${node.ring.col}` }}
          >
            <p className="font-black text-sm" style={{ color: node.ring.col }}>
              {node.ring.ring.ring_id}
            </p>
            <p className="text-muted text-xs mt-1">
              {node.ring.ring.member_accounts.length} members · risk score {node.ring.ring.risk_score}
            </p>
            <div className="flex flex-wrap gap-1 mt-2">
              {node.ring.ring.member_accounts.map((a) => (
                <span
                  key={a}
                  className="px-1.5 py-0.5 rounded text-xs bg-card transition-all hover:bg-card/80"
                  style={{
                    border: `1px solid ${node.ring.col}55`,
                    color:  a === node.id ? node.ring.col : '#E8F4DC',
                    fontWeight: a === node.id ? 900 : 400,
                  }}
                >
                  {a}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Detected patterns */}
      {node.susp?.detected_patterns?.length > 0 && (
        <div>
          <p className="text-muted mb-2" style={{ fontSize: 9 }}>DETECTED PATTERNS</p>
          <div className="flex flex-wrap gap-1">
            {node.susp.detected_patterns.map((p) => (
              <PatternBadge key={p} pattern={p} />
            ))}
          </div>
        </div>
      )}

      {/* Transaction stats */}
      <div>
        <div className="flex gap-4 mb-2" style={{ fontSize: 9 }}>
          <span className="text-muted">
            SENT: <b className="text-cyan-400">{sent.length}</b>
          </span>{'\n'}
          <span className="text-muted">
            RECV: <b className="text-emerald-400">{recv.length}</b>
          </span>
          <span className="text-muted">
            VOL: <b className="text-warn">{totalVol.toLocaleString()}</b>
          </span>
        </div>

        <div className="flex flex-col gap-1 max-h-48 overflow-y-auto">
          {nodeTxns.slice(0, 30).map((t) => {
            const isOut = t.sender_id === node.id
            return (
              <div
                key={t.transaction_id}
                className="flex items-center gap-2 px-2 py-1.5 rounded border border-emerald-600/30 bg-card hover:bg-card/80 transition-all"
              >
                <span className={`text-xs font-bold shrink-0 ${isOut ? 'text-danger' : 'text-emerald-400'}`}>
                  {isOut ? '↑ OUT' : '↓ IN'}
                </span>
                <span className="text-ink text-xs flex-1 truncate">
                  {isOut ? t.receiver_id : t.sender_id}
                </span>
                <span className="text-warn font-bold text-xs shrink-0">
                  {t.amount?.toLocaleString()}
                </span>
              </div>
            )
          })}
          {nodeTxns.length > 30 && (
            <p className="text-muted text-center text-xs py-1">
              +{nodeTxns.length - 30} more transactions
            </p>
          )}
        </div>
      </div>
    </aside>
  )
}
