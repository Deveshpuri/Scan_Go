import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";

// Base URL - replace with your actual API base URL
const BASE_URL = "https://monitor-renewing-oarfish.ngrok-free.app";

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // Increased timeout for image processing
});

// Request interceptor to add auth token if available
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem("authToken");
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
    console.log("API Error:", error.response?.data || error.message);

    // Handle specific error cases
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      AsyncStorage.removeItem("authToken");
    }

    return Promise.reject(error.response?.data || { message: error.message });
  }
);

// API Service functions
export const apiService = {
  // Auth APIs
  auth: {
    login: async (email, password) => {
      try {
        const response = await api.post("/auth/guard/login", {
          email,
          password,
        });
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    logout: async () => {
      try {
        const response = await api.post("/auth/logout");
        return response.data;
      } catch (error) {
        throw error;
      }
    },
  },

  // OCR APIs - FIXED VERSION
  ocr: {
    processImage: async (imageData, authToken) => {
      try {
        console.log("Sending OCR request...");

        const response = await api.post(
          "/guard/scan/ocr",
          {
            image_data: imageData,
          },
          {
            headers: {
              Authorization: `Bearer ${authToken}`,
              "Content-Type": "application/json",
            },
          }
        );

        console.log("OCR Response:", response.data);
        return response.data;
      } catch (error) {
        console.error("OCR API Error:", error);
        throw error;
      }
    },
  },

  // Vehicle APIs - FIXED VERSION
  vehicle: {
    register: async (vehicleData) => {
      try {
        const authToken = await AsyncStorage.getItem("authToken");
        console.log("Registering vehicle:", vehicleData);

        const response = await api.post("/guard/scan/register", vehicleData, {
          headers: {
            Authorization: `Bearer ${authToken}`,
            "Content-Type": "application/json",
          },
        });

        return response.data;
      } catch (error) {
        console.error("Vehicle registration error:", error);
        throw error;
      }
    },
  },

  // Quick Verify API (Alternative to OCR)
  scan: {
    quickVerify: async (imageData, authToken) => {
      try {
        const response = await api.post(
          "/guard/scan/quick-verify",
          {
            image_data: imageData,
          },
          {
            headers: {
              Authorization: `Bearer ${authToken}`,
            },
          }
        );
        return response.data;
      } catch (error) {
        throw error;
      }
    },

    manualEntry: async (licensePlate, notes = "") => {
      try {
        const authToken = await AsyncStorage.getItem("authToken");
        const response = await api.post(
          "/guard/scan/manual-entry",
          {
            license_plate: licensePlate,
            notes: notes,
          },
          {
            headers: {
              Authorization: `Bearer ${authToken}`,
            },
          }
        );
        return response.data;
      } catch (error) {
        throw error;
      }
    },
  },

  // Add these to your existing apiService in services/api.js

  // Dashboard APIs
  dashboard: {
    getStats: async () => {
      try {
        const authToken = await AsyncStorage.getItem("authToken");
        const response = await api.get("/guard/dashboard/stats", {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        });
        return response.data;
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },

    getLastScan: async () => {
      try {
        const authToken = await AsyncStorage.getItem("authToken");
        const response = await api.get("/guard/dashboard/last-scan", {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        });
        return response.data;
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },
  },
};

export default apiService;
