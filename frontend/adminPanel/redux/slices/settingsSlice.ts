import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface Settings {
  qrExpiry: number;
  ocrEnabled: boolean;
  notificationTemplate: string;
}

interface SettingsState {
  settings: Settings | null;
  loading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  settings: null,
  loading: false,
  error: null,
};

export const fetchSettings = createAsyncThunk('settings/fetchSettings', async () => {
  const response = await axios.get('/api/admin/settings');
  return response.data;
});

export const updateSettings = createAsyncThunk('settings/updateSettings', async (data: Partial<Settings>) => {
  const response = await axios.patch('/api/admin/settings', data);
  return response.data;
});

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSettings.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSettings.fulfilled, (state, action) => {
        state.loading = false;
        state.settings = action.payload;
      })
      .addCase(fetchSettings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch settings';
      })
      .addCase(updateSettings.fulfilled, (state, action) => {
        state.settings = { ...state.settings, ...action.payload };
      });
  },
});

export default settingsSlice.reducer;