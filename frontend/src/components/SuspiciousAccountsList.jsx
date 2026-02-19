import React, { useState } from 'react';
import '../styles/components.css';

function SuspiciousAccountsList({ accounts, onSelectAccount, selectedAccount }) {
  const [sortBy, setSortBy] = useState('score'); // 'score' or 'patterns'
  const [filterRing, setFilterRing] = useState(null);

  if (!accounts || accounts.length === 0) {
    return (
      <div className="no-data">
        <p>No suspicious accounts found</p>
      </div>
    );
  }

  const sortedAccounts = [...accounts].sort((a, b) => {
    if (sortBy === 'score') {
      return b.suspicion_score - a.suspicion_score;
    } else {
      return b.detected_patterns.length - a.detected_patterns.length;
    }
  });

  const filteredAccounts = filterRing
    ? sortedAccounts.filter(acc => acc.ring_id === filterRing)
    : sortedAccounts;

  const rings = [...new Set(accounts.map(acc => acc.ring_id).filter(Boolean))];

  return (
    <div className="suspicious-accounts">
      <div className="list-controls">
        <div className="control-group">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="score">Suspicion Score</option>
            <option value="patterns">Pattern Count</option>
          </select>
        </div>
        {rings.length > 0 && (
          <div className="control-group">
            <label>Filter by ring:</label>
            <select value={filterRing || ''} onChange={(e) => setFilterRing(e.target.value || null)}>
              <option value="">All Rings</option>
              {rings.map(ring => (
                <option key={ring} value={ring}>{ring}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="accounts-list-container">
        {filteredAccounts.map((account, idx) => (
          <div
            key={idx}
            className={`account-card ${selectedAccount === account.account_id ? 'selected' : ''}`}
            onClick={() => onSelectAccount(account.account_id)}
          >
            <div className="account-header">
              <div className="account-id">{account.account_id}</div>
              <div className="account-ring">{account.ring_id}</div>
            </div>

            <div className="score-section">
              <div className="score-label">Suspicion Score</div>
              <div className="score-bar">
                <div
                  className="score-fill"
                  style={{
                    width: `${account.suspicion_score}%`,
                    backgroundColor:
                      account.suspicion_score > 80
                        ? 'var(--danger-color)'
                        : account.suspicion_score > 50
                        ? 'var(--warning-color)'
                        : 'var(--success-color)',
                  }}
                ></div>
              </div>
              <div className="score-value">{account.suspicion_score.toFixed(1)}/100</div>
            </div>

            {account.detected_patterns.length > 0 && (
              <div className="patterns-section">
                <div className="section-label">Detected Patterns ({account.detected_patterns.length})</div>
                <div className="patterns">
                  {account.detected_patterns.map((pattern, i) => (
                    <span key={i} className={`pattern-tag pattern-${pattern}`}>
                      {pattern.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default SuspiciousAccountsList;
