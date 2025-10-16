import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface Request {
  id: string;
  vehicle: string;
  owner: string;
  status: 'pending' | 'approved' | 'rejected';
}

interface RequestsState {
  requests: Request[];
  loading: boolean;
  error: string | null;
}

const initialState: RequestsState = {
  requests: [],
  loading: false,
  error: null,
};

export const fetchRequests = createAsyncThunk('requests/fetchRequests', async (params: { status?: string }) => {
  const response = await axios.get('/api/admin/requests', { params });
  return response.data;
});

export const approveRequest = createAsyncThunk('requests/approveRequest', async (id: string) => {
  const response = await axios.patch(`/api/admin/requests/${id}/approve`);
  return response.data;
});

export const rejectRequest = createAsyncThunk('requests/rejectRequest', async ({ id, reason }: { id: string; reason: string }) => {
  const response = await axios.patch(`/api/admin/requests/${id}/reject`, { reason });
  return response.data;
});

const requestsSlice = createSlice({
  name: 'requests',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchRequests.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRequests.fulfilled, (state, action) => {
        state.loading = false;
        state.requests = action.payload;
      })
      .addCase(fetchRequests.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch requests';
      })
      .addCase(approveRequest.fulfilled, (state, action) => {
        const request = state.requests.find((r) => r.id === action.payload.id);
        if (request) request.status = 'approved';
      })
      .addCase(rejectRequest.fulfilled, (state, action) => {
        const request = state.requests.find((r) => r.id === action.payload.id);
        if (request) request.status = 'rejected';
      });
  },
});

export default requestsSlice.reducer;