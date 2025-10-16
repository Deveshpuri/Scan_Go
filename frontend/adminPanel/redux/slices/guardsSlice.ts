import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface Guard {
  id: string;
  name: string;
  gate: string;
  status: 'active' | 'inactive';
}

interface GuardsState {
  guards: Guard[];
  loading: boolean;
  error: string | null;
}

const initialState: GuardsState = {
  guards: [],
  loading: false,
  error: null,
};

export const fetchGuards = createAsyncThunk('guards/fetchGuards', async () => {
  const response = await axios.get('/api/admin/guards');
  return response.data;
});

export const createGuard = createAsyncThunk('guards/createGuard', async (data: { name: string; gate: string }) => {
  const response = await axios.post('/api/admin/guards', data);
  return response.data;
});

export const assignGate = createAsyncThunk('guards/assignGate', async ({ id, gate }: { id: string; gate: string }) => {
  const response = await axios.patch(`/api/admin/guards/${id}/assign`, { gate });
  return response.data;
});

const guardsSlice = createSlice({
  name: 'guards',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchGuards.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchGuards.fulfilled, (state, action) => {
        state.loading = false;
        state.guards = action.payload;
      })
      .addCase(fetchGuards.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch guards';
      })
      .addCase(createGuard.fulfilled, (state, action) => {
        state.guards.push(action.payload);
      })
      .addCase(assignGate.fulfilled, (state, action) => {
        const guard = state.guards.find((g) => g.id === action.payload.id);
        if (guard) guard.gate = action.payload.gate;
      });
  },
});

export default guardsSlice.reducer;