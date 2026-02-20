import { createSlice } from '@reduxjs/toolkit'

const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    selectedNode: null,
    activeTab:    'rings',    // rings | accounts | log
  },
  reducers: {
    setSelectedNode(state, action) { state.selectedNode = action.payload },
    clearSelectedNode(state)       { state.selectedNode = null },
    setActiveTab(state, action)    { state.activeTab = action.payload },
  },
})

export const { setSelectedNode, clearSelectedNode, setActiveTab } = uiSlice.actions
export default uiSlice.reducer

export const selectSelectedNode = (s) => s.ui.selectedNode
export const selectActiveTab    = (s) => s.ui.activeTab
