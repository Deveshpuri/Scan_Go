import { useState, useEffect } from 'react';
import axios from 'axios';

// Base URL for your backend API (replace with your actual API URL)
const BASE_URL = 'https://bear-mint-impala.ngrok-free.app'; // Update this

const useApi = (endpoint, method = 'GET', options = {}) => {
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setErr(null);

      try {
        const config = {
          method: method.toUpperCase(),
          url: `${BASE_URL}${endpoint}`,
          ...options, // Spread additional options (e.g., headers, data, params)
        };

        const response = await axios(config);
        setRes(response.data);
      } catch (error) {
        setErr(error.response?.data || error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint, method, JSON.stringify(options)]); // Re-run if endpoint, method, or options change

  return { res, loading, err };
};

export default useApi;