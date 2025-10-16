import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface Vehicle {
  id: string;
  plate: string;
  owner: string;
  status: 'active' | 'blocked';
}

interface VehiclesState {
  vehicles: Vehicle[];
  loading: boolean;
  error: string | null;
  qrData: string | null;
}

const initialState: VehiclesState = {
  vehicles: [],
  loading: false,
  error: null,
  qrData: null,
};

export const fetchVehicles = createAsyncThunk('vehicles/fetchVehicles', async (params: { search?: string }) => {
  const response = await axios.get('/api/admin/vehicles', { params });
  return response.data;
});

export const blockVehicle = createAsyncThunk('vehicles/blockVehicle', async (id: string) => {
  const response = await axios.patch(`/api/admin/vehicles/${id}/block`);
  return response.data;
});

export const fetchQrCode = createAsyncThunk('vehicles/fetchQrCode', async (id: string) => {
  const response = await axios.get(`/api/admin/vehicles/${id}/qr`);
  return response.data.qr;
});

const vehiclesSlice = createSlice({
  name: 'vehicles',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchVehicles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchVehicles.fulfilled, (state, action) => {
        state.loading = false;
        state.vehicles = action.payload;
      })
      .addCase(fetchVehicles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch vehicles';
      })
      .addCase(blockVehicle.fulfilled, (state, action) => {
        const vehicle = state.vehicles.find((v) => v.id === action.payload.id);
        if (vehicle) vehicle.status = action.payload.status;
      })
      .addCase(fetchQrCode.fulfilled, (state, action) => {
        state.qrData = action.payload;
      });
  },
});

export default vehiclesSlice.reducer;