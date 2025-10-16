import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface Log {
  id: string;
  time: string;
  vehicle: string;
  guard: string;
  action: 'in' | 'out';
}

interface LogsState {
  logs: Log[];
  loading: boolean;
  error: string | null;
}

const initialState: LogsState = {
  logs: [],
  loading: false,
  error: null,
};

export const fetchLogs = createAsyncThunk('logs/fetchLogs', async (params: { date?: string; guard?: string; vehicle?: string }) => {
  const response = await axios.get('/api/admin/logs', { params });
  return response.data;
});

export const exportLogs = createAsyncThunk('logs/exportLogs', async () => {
  const response = await axios.get('/api/admin/logs/export', { responseType: 'blob' });
  return response.data;
});

const logsSlice = createSlice({
  name: 'logs',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchLogs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLogs.fulfilled, (state, action) => {
        state.loading = false;
        state.logs = action.payload;
      })
      .addCase(fetchLogs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch logs';
      });
  },
});

export default logsSlice.reducer;