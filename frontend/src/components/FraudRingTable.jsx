import React from 'react';
import '../styles/components.css';

function FraudRingTable({ rings }) {
  if (!rings || rings.length === 0) {
    return (
      <div className="no-data">
        <p>No fraud rings detected</p>
      </div>
    );
  }

  return (
    <div className="fraud-ring-table">
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Ring ID</th>
              <th>Pattern Type</th>
              <th>Members</th>
              <th>Risk Score</th>
              <th>Member Accounts</th>
            </tr>
          </thead>
          <tbody>
            {rings.map((ring, idx) => (
              <tr key={idx} className={`severity-${ring.pattern_type}`}>
                <td className="ring-id">
                  <span className="badge">{ring.ring_id}</span>
                </td>
                <td className="pattern-type">
                  <span className="pattern-badge">{ring.pattern_type}</span>
                </td>
                <td className="member-count">
                  <strong>{ring.member_accounts.length}</strong>
                </td>
                <td className="risk-score">
                  <div className="score-bar">
                    <div
                      className="score-fill"
                      style={{
                        width: `${Math.min(ring.risk_score, 100)}%`,
                        backgroundColor:
                          ring.risk_score > 80
                            ? 'var(--danger-color)'
                            : ring.risk_score > 50
                            ? 'var(--warning-color)'
                            : 'var(--success-color)',
                      }}
                    ></div>
                  </div>
                  <span>{ring.risk_score.toFixed(1)}</span>
                </td>
                <td className="member-accounts">
                  <div className="accounts-list">
                    {ring.member_accounts.map((acc, i) => (
                      <span key={i} className="account-tag">{acc}</span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default FraudRingTable;
