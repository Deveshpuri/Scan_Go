import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface AuditLog {
  id: string;
  time: string;
  user: string;
  action: string;
  details: string;
}

interface AuditState {
  logs: AuditLog[];
  loading: boolean;
  error: string | null;
}

const initialState: AuditState = {
  logs: [],
  loading: false,
  error: null,
};

export const fetchAuditLogs = createAsyncThunk('audit/fetchAuditLogs', async (params: { date?: string; action?: string }) => {
  const response = await axios.get('/api/admin/audit', { params });
  return response.data;
});

const auditSlice = createSlice({
  name: 'audit',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAuditLogs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAuditLogs.fulfilled, (state, action) => {
        state.loading = false;
        state.logs = action.payload;
      })
      .addCase(fetchAuditLogs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch audit logs';
      });
  },
});

export default auditSlice.reducer;