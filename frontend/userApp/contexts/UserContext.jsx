import { createContext, useContext, useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import axios from "axios";

// Base URL for your backend API
const BASE_URL = "https://bear-mint-impala.ngrok-free.app";

// Create User Context
const UserContext = createContext();

// Helper function to perform API calls
const performApiCall = async (endpoint, method = "GET", options = {}) => {
  try {
    const config = {
      method: method.toUpperCase(),
      url: `${BASE_URL}${endpoint}`,
      ...options, // Spread additional options (e.g., headers, data, params)
    };
    const response = await axios(config);
    return { res: response.data, err: null };
  } catch (error) {
    return { res: null, err: error.response?.data?.message || error.message };
  }
};

// User Provider Component
export const UserProvider = ({ children }) => {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Load token and fetch user data on mount
  useEffect(() => {
    const loadTokenAndUser = async () => {
      try {
        const storedToken = await AsyncStorage.getItem("authToken");
        if (storedToken) {
          setToken(storedToken);
          setIsAuthenticated(true);
          // Fetch user data using performApiCall
          const { res, err } = await performApiCall("/user", "GET", {
            headers: { Authorization: `Bearer ${storedToken}` },
          });
          if (err) {
            console.error("Error fetching user data:", err);
            setIsAuthenticated(false);
            await AsyncStorage.removeItem("authToken");
          } else if (res) {
            setUser(res); // Assuming res is the user object
          }
        }
      } catch (error) {
        console.error("Error loading token or user data:", error);
      } finally {
        setLoading(false);
      }
    };
    loadTokenAndUser();
  }, []);

  // Helper function to determine login payload
  const getLoginPayload = (identifier, password) => {
    if (identifier.includes("@")) {
      return { email: identifier, password };
    } else {
      // Basic validation for phone
      if (!/^\d{10,15}$/.test(identifier.replace(/\s/g, ""))) {
        throw new Error(
          "Invalid phone number format. Please enter a valid 10-15 digit number."
        );
      }
      return { phone_number: identifier, password };
    }
  };

  // Login function
  const login = async (identifier, password) => {
    try {
      const payload = getLoginPayload(identifier, password);
      const { res, err } = await performApiCall("/auth/user/login", "POST", {
        data: payload,
      });
      if (err) {
        throw new Error(err);
      }
      if (res) {
        const { access_token: token, user } = res;
        await AsyncStorage.setItem("authToken", token);
        await AsyncStorage.setItem("userData", user);
        setToken(token);
        setUser(user); // Store user data
        setIsAuthenticated(true);
        router.replace("/(tabs)/dashboard");
        return { success: true };
      }
    } catch (error) {
      console.error("Login error:", error);
      return { success: false, error: error.message };
    }
  };

  // Signup function
  const signup = async (
    user_name,
    email,
    password,
    phone_number,
    building_id,
    building_number,
    flat_number,
    wing
  ) => {
    try {
      // Basic validation
      if (
        !user_name ||
        !email ||
        !password ||
        !phone_number ||
        !building_id ||
        !building_number ||
        !flat_number ||
        !wing
      ) {
        throw new Error("All fields are required");
      }
      if (!email.includes("@")) {
        throw new Error("Invalid email format");
      }
      if (!/^\d{10,15}$/.test(phone_number.replace(/\s/g, ""))) {
        throw new Error(
          "Invalid phone number format. Please enter a valid 10-15 digit number"
        );
      }
      const { res, err } = await performApiCall("/auth/user/register", "POST", {
        data: {
          user_name,
          email,
          password,
          phone_number,
          building_id: Number(building_id), // Ensure building_id is a number
          building_number,
          flat_number,
          wing,
        },
      });
      if (err) {
        throw new Error(err);
      }
      if (res) {
        setIsAuthenticated(true);
        router.replace('/login');
        return { success: true };
      }
    } catch (error) {
      console.error("Signup error:", error);
      return { success: false, error: error.message };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await AsyncStorage.removeItem("authToken");
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
      router.replace("/login");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  return (
    <UserContext.Provider
      value={{ token, user, isAuthenticated, loading, login, signup, logout }}
    >
      {children}
    </UserContext.Provider>
  );
};

// Custom hook to use UserContext
export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
};
