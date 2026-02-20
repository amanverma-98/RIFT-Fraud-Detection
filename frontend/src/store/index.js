import { configureStore } from '@reduxjs/toolkit'
import fraudReducer from './fraudSlice'
import uiReducer    from './uiSlice'

export const store = configureStore({
  reducer: {
    fraud: fraudReducer,
    ui:    uiReducer,
  },
})
