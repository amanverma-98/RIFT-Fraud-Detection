import axios from 'axios'

const BASE = 'https://rift-fraud-detection.onrender.com'

const http = axios.create({
  baseURL: BASE,
  timeout: 60_000,
})

export const fraudApi = {
  /** POST /api/fraud/upload */
  uploadFraud: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await http.post('/api/fraud/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  /** POST /api/transactions/upload-transactions */
  uploadTransactions: async (file) => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await http.post('/api/transactions/upload-transactions', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  /** POST /api/fraud/analyze?filename=... */
  analyze: async (filename) => {
    const { data } = await http.post('/api/fraud/analyze', null, {
      params: { filename },
    })
    return data
  },

  /** GET /api/fraud/report/{report_id} */
  getReport: async (reportId) => {
    const { data } = await http.get(`/api/fraud/report/${reportId}`)
    return data
  },

  /** GET /api/fraud/report/{report_id}/download-json */
  downloadJson: async (reportId) => {
    const { data } = await http.get(`/api/fraud/report/${reportId}/download-json`)
    return data
  },

  /** GET /api/transactions/batch/{upload_id} */
  getTransactionBatch: async (uploadId) => {
    const { data } = await http.get(`/api/transactions/batch/${uploadId}`)
    return data
  },

  /** GET /api/fraud/reports?limit=10 */
  getReports: async (limit = 10) => {
    const { data } = await http.get('/api/fraud/reports', { params: { limit } })
    return data
  },
}
