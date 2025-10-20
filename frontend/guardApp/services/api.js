import axios from 'axios';
import AsyncStorage from "@react-native-async-storage/async-storage";
// Base URL - replace with your actual API base URL
const BASE_URL = 'https://bear-mint-impala.ngrok-free.app';

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to add auth token if available
api.interceptors.request.use(
async  (config) => {
    // You can add auth token here if needed
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.log('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API Service functions
export const apiService = {
  // Auth APIs
  auth: {
    login: async (email, password) => {
      try {
        const response = await api.post('/auth/guard/login', {
          email,
          password,
        });
        return response.data;
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },

    logout: async () => {
      try {
        const response = await api.post('/auth/guard/logout');
        return response.data;
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },

    forgotPassword: async (email) => {
      try {
        const response = await api.post('/auth/guard/forgot-password', { email });
        return response.data;
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },

    resetPassword: async (token, newPassword) => {
      try {
        const response = await api.post('/auth/guard/reset-password', {
          token,
          newPassword,
        });
        return response.data;
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },
  },

  // Profile APIs
  profile: {
    getProfile: async () => {
      try {
        const response = await api.get('/auth/guard/profile');
        return response.data;
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },

    updateProfile: async (profileData) => {
      try {
        const response = await api.put('/auth/guard/profile', profileData);
        return response.data;
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },
  },

  // Other API groups can be added here
  // posts: { ... },
  // notifications: { ... },
};

export default apiService;