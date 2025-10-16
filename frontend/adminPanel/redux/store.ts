import { configureStore } from '@reduxjs/toolkit';
import metricsReducer from './slices/metricsSlice';
import vehiclesReducer from './slices/vehiclesSlice';
import usersReducer from './slices/usersSlice';
import guardsReducer from './slices/guardsSlice';
import requestsReducer from './slices/requestsSlice';
import logsReducer from './slices/logsSlice';
import duesReducer from './slices/duesSlice';
import auditReducer from './slices/auditSlice';
import settingsReducer from './slices/settingsSlice';
import authReducer from './slices/authSlice';

export const store = configureStore({
  reducer: {
    metrics: metricsReducer,
    vehicles: vehiclesReducer,
    users: usersReducer,
    guards: guardsReducer,
    requests: requestsReducer,
    logs: logsReducer,
    dues: duesReducer,
    audit: auditReducer,
    settings: settingsReducer,
    auth: authReducer,
  },
  middleware: (getDefaultMiddleware) => getDefaultMiddleware(),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;