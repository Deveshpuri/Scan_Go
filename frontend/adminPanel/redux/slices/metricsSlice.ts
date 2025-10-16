import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface MetricsState {
  totalVehicles: number;
  currentlyInside: number;
  visitorsToday: number;
  pendingRequests: number;
  recentRequests: Array<{ id: string; vehicle: string; status: string }>;
  loading: boolean;
  error: string | null;
}

const initialState: MetricsState = {
  totalVehicles: 0,
  currentlyInside: 0,
  visitorsToday: 0,
  pendingRequests: 0,
  recentRequests: [],
  loading: false,
  error: null,
};

export const fetchMetrics = createAsyncThunk('metrics/fetchMetrics', async () => {
  const response = await axios.get('/api/admin/metrics');
  return response.data;
});

const metricsSlice = createSlice({
  name: 'metrics',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchMetrics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMetrics.fulfilled, (state, action) => {
        state.loading = false;
        state.totalVehicles = action.payload.totalVehicles;
        state.currentlyInside = action.payload.currentlyInside;
        state.visitorsToday = action.payload.visitorsToday;
        state.pendingRequests = action.payload.pendingRequests;
        state.recentRequests = action.payload.recentRequests;
      })
      .addCase(fetchMetrics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch metrics';
      });
  },
});

export default metricsSlice.reducer;