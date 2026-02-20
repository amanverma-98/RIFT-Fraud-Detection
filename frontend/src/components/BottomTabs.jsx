import { useDispatch, useSelector } from 'react-redux'
import { setActiveTab, selectActiveTab } from '../store/uiSlice'
import { selectLogs } from '../store/fraudSlice'
import FraudRingsTable from './FraudRingsTable'
import SuspiciousAccountsTable from './SuspiciousAccountsTable'

const LOG_COLORS = {
  ok:   'text-emerald-400',
  warn: 'text-warn',
  err:  'text-danger',
  info: 'text-cyan-400',
}

const TABS = [
  { key: 'rings',    label: 'FRAUD RING SUMMARY' },
  { key: 'accounts', label: 'SUSPICIOUS ACCOUNTS' },
  { key: 'log',      label: 'PIPELINE LOG' },
]

export default function BottomTabs() {
  const dispatch   = useDispatch()
  const activeTab  = useSelector(selectActiveTab)
  const logs       = useSelector(selectLogs)

  return (
    <div>
      {/* Tab bar */}
      <div className="flex gap-0 border-b border-emerald-600/30 mb-4">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => dispatch(setActiveTab(key))}
            className={`px-5 py-2 text-xs font-bold tracking-widest border-b-2 -mb-px transition-all ${
              activeTab === key
                ? 'border-emerald-500 text-emerald-400 bg-emerald-600/10'
                : 'border-transparent text-muted hover:text-ink hover:bg-emerald-600/10'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div className="animate-fadeIn">
        {activeTab === 'rings'    && <FraudRingsTable />}
        {activeTab === 'accounts' && <SuspiciousAccountsTable />}
        {activeTab === 'log'      && (
          <div className="bg-black/40 border border-emerald-600/30 rounded-xl p-4 max-h-64 overflow-y-auto font-mono text-xs backdrop-blur-sm">
            {logs.length === 0 && (
              <p className="text-muted text-center py-6">No logs yet.</p>
            )}
            {logs.map((l) => (
              <div
                key={l.id}
                className="flex gap-3 leading-loose border-b border-emerald-600/20 last:border-0"
              >
                <span className="text-muted shrink-0 w-20">{l.time}</span>
                <span className={LOG_COLORS[l.type] || 'text-ink'}>{l.msg}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
