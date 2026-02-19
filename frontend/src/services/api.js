import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

export default {
  // Upload CSV file
  uploadCSV: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/fraud/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Analyze CSV
  analyzeCSV: (filename) => {
    return api.post(`/fraud/analyze?filename=${encodeURIComponent(filename)}`);
  },

  // Get full report
  getReport: (reportId) => {
    return api.get(`/fraud/report/${reportId}`);
  },

  // Get report summary
  getReportSummary: (reportId) => {
    return api.get(`/fraud/report/${reportId}/summary`);
  },

  // Download report as JSON
  downloadReport: (reportId) => {
    return api.get(`/fraud/report/${reportId}/download-json`, {
      responseType: 'blob',
    }).then(response => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `fraud_report_${reportId}.json`);
      document.body.appendChild(link);
      link.click();
      link.parentChild.removeChild(link);
    });
  },

  // List all reports
  listReports: (limit = 10) => {
    return api.get(`/fraud/reports?limit=${limit}`);
  },

  // Health check
  healthCheck: () => {
    return api.get('/health');
  },
};
