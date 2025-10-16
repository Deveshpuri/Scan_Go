import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface Due {
  id: string;
  vehicle: string;
  amount: number;
  dueDate: string;
  status: 'pending' | 'paid';
}

interface DuesState {
  dues: Due[];
  loading: boolean;
  error: string | null;
}

const initialState: DuesState = {
  dues: [],
  loading: false,
  error: null,
};

export const fetchDues = createAsyncThunk('dues/fetchDues', async () => {
  const response = await axios.get('/api/admin/dues');
  return response.data;
});

export const markDuePaid = createAsyncThunk('dues/markDuePaid', async (id: string) => {
  const response = await axios.patch(`/api/admin/dues/${id}/paid`);
  return response.data;
});

export const blockVehicleForDue = createAsyncThunk('dues/blockVehicleForDue', async (id: string) => {
  const response = await axios.patch(`/api/admin/vehicles/${id}/block`);
  return response.data;
});

const duesSlice = createSlice({
  name: 'dues',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDues.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDues.fulfilled, (state, action) => {
        state.loading = false;
        state.dues = action.payload;
      })
      .addCase(fetchDues.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch dues';
      })
      .addCase(markDuePaid.fulfilled, (state, action) => {
        const due = state.dues.find((d) => d.id === action.payload.id);
        if (due) due.status = 'paid';
      });
  },
});

export default duesSlice.reducer;