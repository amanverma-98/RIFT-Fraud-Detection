import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { fraudApi } from '../api/fraudApi'

// ── Async Thunks ────────────────────────────────────────────────────────────

export const runFullPipeline = createAsyncThunk(
  'fraud/runFullPipeline',
  async (file, { dispatch, rejectWithValue }) => {
    try {
      dispatch(addLog({ msg: `Loaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, type: 'info' }))

      // Step 1: Fraud upload
      dispatch(setStep('uploading'))
      dispatch(addLog({ msg: '→ Uploading CSV to fraud detection engine…', type: 'info' }))
      const fraudUpload = await fraudApi.uploadFraud(file)
      dispatch(addLog({ msg: `✓ Fraud upload OK — ${fraudUpload.processed_records} records (${fraudUpload.filename})`, type: 'ok' }))

      // Step 2: Transaction upload
      dispatch(addLog({ msg: '→ Uploading to transaction store…', type: 'info' }))
      const txUpload = await fraudApi.uploadTransactions(file)
      dispatch(addLog({ msg: `✓ Transaction upload OK — upload_id: ${txUpload.upload_id}`, type: 'ok' }))
      dispatch(addLog({ msg: `  ${txUpload.unique_accounts} unique accounts · ${txUpload.total_transactions} transactions`, type: 'info' }))

      // Step 3: Analyze
      dispatch(setStep('analyzing'))
      dispatch(addLog({ msg: '→ Running graph cycle / smurfing / shell analysis…', type: 'info' }))
      const analysis = await fraudApi.analyze(fraudUpload.filename)
      dispatch(addLog({ msg: `✓ Report ID: ${analysis.report_id}`, type: 'ok' }))
      dispatch(addLog({ msg: `  🔴 ${analysis.fraud_rings_detected} fraud ring(s) · ⚠ ${analysis.suspicious_accounts_flagged} suspicious accounts`, type: 'warn' }))

      // Step 4: Full report
      dispatch(addLog({ msg: '→ Fetching full report…', type: 'info' }))
      const report = await fraudApi.getReport(analysis.report_id)
      dispatch(addLog({ msg: `✓ Report loaded — ${report.fraud_rings.length} ring(s) confirmed`, type: 'ok' }))

      // Step 5: Transaction graph via batch GET
      dispatch(addLog({ msg: `→ Fetching transaction graph — GET /api/transactions/batch/${txUpload.upload_id}`, type: 'info' }))
      const batch = await fraudApi.getTransactionBatch(txUpload.upload_id)
      const transactions = batch.transactions || []
      dispatch(addLog({ msg: `✓ Graph data ready — ${transactions.length} transaction edges`, type: 'ok' }))

      return { report, transactions, reportId: analysis.report_id }
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Unknown error'
      dispatch(addLog({ msg: `✗ ${msg}`, type: 'err' }))
      return rejectWithValue(msg)
    }
  }
)

// ── Slice ───────────────────────────────────────────────────────────────────

const initialState = {
  // pipeline
  step:    'idle',   // idle | uploading | analyzing | done | error
  logs:    [],
  error:   null,

  // data
  report:       null,
  transactions: [],
  reportId:     null,
}

const fraudSlice = createSlice({
  name: 'fraud',
  initialState,
  reducers: {
    setStep(state, action) {
      state.step = action.payload
    },
    addLog(state, action) {
      state.logs.push({
        ...action.payload,
        time: new Date().toLocaleTimeString(),
        id:   Date.now() + Math.random(),
      })
    },
    reset(state) {
      Object.assign(state, initialState)
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(runFullPipeline.pending, (state) => {
        state.step   = 'uploading'
        state.error  = null
        state.logs   = []
        state.report = null
        state.transactions = []
      })
      .addCase(runFullPipeline.fulfilled, (state, action) => {
        state.step         = 'done'
        state.report       = action.payload.report
        state.transactions = action.payload.transactions
        state.reportId     = action.payload.reportId
      })
      .addCase(runFullPipeline.rejected, (state, action) => {
        state.step  = 'error'
        state.error = action.payload
      })
  },
})

export const { setStep, addLog, reset } = fraudSlice.actions
export default fraudSlice.reducer

// ── Selectors ───────────────────────────────────────────────────────────────
export const selectStep         = (s) => s.fraud.step
export const selectLogs         = (s) => s.fraud.logs
export const selectReport       = (s) => s.fraud.report
export const selectTransactions = (s) => s.fraud.transactions
export const selectReportId     = (s) => s.fraud.reportId
export const selectError        = (s) => s.fraud.error
