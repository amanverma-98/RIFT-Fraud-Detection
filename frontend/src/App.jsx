import React, { useState, useCallback } from 'react';
import FileUpload from './components/FileUpload';
import GraphVisualization from './components/GraphVisualization';
import FraudRingTable from './components/FraudRingTable';
import SuspiciousAccountsList from './components/SuspiciousAccountsList';
import Header from './components/Header';
import LoadingSpinner from './components/LoadingSpinner';
import api from './services/api';
import './styles/App.css';

function App() {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [graphData, setGraphData] = useState(null);

  const handleFileUpload = async (file) => {
    setLoading(true);
    setError(null);
    try {
      // Step 1: Upload CSV
      const uploadRes = await api.uploadCSV(file);
      const filename = uploadRes.data.filename;

      // Step 2: Analyze fraud patterns
      const analysisRes = await api.analyzeCSV(filename);
      const reportId = analysisRes.data.report_id;

      // Step 3: Get full report
      const reportRes = await api.getReport(reportId);
      const report = reportRes.data;

      setReportData(report);

      // Build graph data from report
      const nodes = new Set();
      const links = [];

      // Extract nodes and edges from fraud rings
      if (report.fraud_rings) {
        report.fraud_rings.forEach(ring => {
          ring.member_accounts.forEach(account => {
            nodes.add(account);
          });
        });
      }

      // Create links from suspicious accounts (we'll infer from the data)
      // For now, just create nodes
      const graphNodes = Array.from(nodes).map(id => ({
        id,
        name: id,
        isSuspicious: report.suspicious_accounts?.some(acc => acc.account_id === id) || false,
        suspicionScore: report.suspicious_accounts?.find(acc => acc.account_id === id)?.suspicion_score || 0,
        ringId: report.suspicious_accounts?.find(acc => acc.account_id === id)?.ring_id || null
      }));

      setGraphData({ nodes: graphNodes, links });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error processing file');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadJSON = async () => {
    try {
      if (reportData?.report_id) {
        await api.downloadReport(reportData.report_id);
      }
    } catch (err) {
      setError('Error downloading report');
      console.error('Error:', err);
    }
  };

  const handleReset = () => {
    setReportData(null);
    setGraphData(null);
    setSelectedAccount(null);
    setError(null);
  };

  return (
    <div className="app">
      <Header onReset={handleReset} />

      <main className="main-content">
        {!reportData ? (
          // Upload Screen
          <div className="upload-section">
            <div className="upload-container">
              <div className="upload-header">
                <h1>Money Muling Detection Engine</h1>
                <p>Upload transaction data to detect fraudulent activity patterns</p>
              </div>

              {error && (
                <div className="error-banner">
                  <span>⚠️ {error}</span>
                  <button onClick={() => setError(null)}>✕</button>
                </div>
              )}

              <FileUpload onUpload={handleFileUpload} loading={loading} />

              {loading && <LoadingSpinner message="Analyzing transactions..." />}

              <div className="upload-info">
                <h3>Expected CSV Format</h3>
                <table className="format-table">
                  <thead>
                    <tr>
                      <th>Column Name</th>
                      <th>Data Type</th>
                      <th>Example</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>transaction_id</td>
                      <td>String</td>
                      <td>TXN001</td>
                    </tr>
                    <tr>
                      <td>sender_id</td>
                      <td>String</td>
                      <td>Alice</td>
                    </tr>
                    <tr>
                      <td>receiver_id</td>
                      <td>String</td>
                      <td>Bob</td>
                    </tr>
                    <tr>
                      <td>amount</td>
                      <td>Float</td>
                      <td>1000.50</td>
                    </tr>
                    <tr>
                      <td>timestamp</td>
                      <td>DateTime</td>
                      <td>2026-02-19 10:00:00</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          // Results Screen
          <div className="results-section">
            <div className="results-header">
              <h2>Analysis Results</h2>
              <div className="results-actions">
                <button className="btn-download" onClick={handleDownloadJSON}>
                  ⬇️ Download JSON Report
                </button>
                <button className="btn-reset" onClick={handleReset}>
                  ⟲ Analyze Another File
                </button>
              </div>
            </div>

            <div className="results-grid">
              <div className="summary-cards">
                <div className="summary-card">
                  <div className="card-value">{reportData.summary.total_accounts_analyzed}</div>
                  <div className="card-label">Total Accounts</div>
                </div>
                <div className="summary-card suspicious">
                  <div className="card-value">{reportData.summary.suspicious_accounts_flagged}</div>
                  <div className="card-label">Suspicious Accounts</div>
                </div>
                <div className="summary-card danger">
                  <div className="card-value">{reportData.summary.fraud_rings_detected}</div>
                  <div className="card-label">Fraud Rings Detected</div>
                </div>
                <div className="summary-card">
                  <div className="card-value">{reportData.summary.processing_time_seconds}s</div>
                  <div className="card-label">Processing Time</div>
                </div>
              </div>

              {graphData && (
                <div className="graph-section">
                  <h3>Transaction Network Visualization</h3>
                  <GraphVisualization
                    data={graphData}
                    onNodeClick={setSelectedAccount}
                    selectedAccount={selectedAccount}
                  />
                </div>
              )}

              <div className="rings-section">
                <h3>Detected Fraud Rings</h3>
                <FraudRingTable rings={reportData.fraud_rings} />
              </div>

              <div className="accounts-section">
                <h3>Suspicious Accounts ({reportData.suspicious_accounts.length})</h3>
                <SuspiciousAccountsList
                  accounts={reportData.suspicious_accounts}
                  onSelectAccount={setSelectedAccount}
                  selectedAccount={selectedAccount}
                />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
