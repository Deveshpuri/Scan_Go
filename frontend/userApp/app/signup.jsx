import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  Button,
  StyleSheet,
  Alert,
  ScrollView,
} from "react-native";
import { Picker } from "@react-native-picker/picker"; // Updated import
import { useRouter } from "expo-router";
import { useUser } from "../contexts/UserContext"; // Adjust path based on your project structure
import axios from "axios";

// Base URL for API
const BASE_URL = " https://bear-mint-impala.ngrok-free.app";

// Helper function to fetch buildings
const performApiCall = async (endpoint, method = "GET", options = {}) => {
  try {
    const config = {
      method: method.toUpperCase(),
      url: `${BASE_URL}${endpoint}`,
      ...options,
    };
    const response = await axios(config);
    return { res: response.data, err: null };
  } catch (error) {
    return { res: null, err: error.response?.data?.message || error.message };
  }
};

const Signup = () => {
  const router = useRouter();
  const [userName, setUserName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [buildingId, setBuildingId] = useState(""); // Stores selected building ID
  const [buildingNumber, setBuildingNumber] = useState("");
  const [flatNumber, setFlatNumber] = useState("");
  const [wing, setWing] = useState("");
  const [buildings, setBuildings] = useState([]); // Stores fetched buildings
  const [formLoading, setFormLoading] = useState(false);
  const [buildingsLoading, setBuildingsLoading] = useState(true);
  const { signup, loading: contextLoading } = useUser();
  const isLoading = formLoading || contextLoading || buildingsLoading;

  // Fetch buildings on mount
  useEffect(() => {
    const fetchBuildings = async () => {
      setBuildingsLoading(true);
      const { res, err } = await performApiCall("/buildings", "GET");
      if (err) {
        Alert.alert("Error", "Failed to load buildings: " + err);
      } else if (res && res.buildings) {
        setBuildings(res.buildings);
        // Set default building (first one, if available)
        if (res.buildings.length > 0) {
          setBuildingId(res.buildings[0].id.toString());
        }
      }
      setBuildingsLoading(false);
    };
    fetchBuildings();
  }, []);

  const handleSignup = async () => {
    if (
      !userName ||
      !email ||
      !password ||
      !phoneNumber ||
      !buildingId ||
      !buildingNumber ||
      !flatNumber ||
      !wing
    ) {
      Alert.alert(
        "Error",
        "Please fill in all fields, including selecting a building"
      );
      return;
    }

    setFormLoading(true);
    const result = await signup(
      userName,
      email,
      password,
      phoneNumber,
      buildingId,
      buildingNumber,
      flatNumber,
      wing
    );
    setFormLoading(false);
    console.log(result.data);
    
    if (!result.success) {
      Alert.alert(
        "Signup Failed",
        result.error || "Could not create account. Please try again."
      );
    } else {
      Alert.alert("Success", "Account created successfully!");
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Sign Up</Text>

      <Text style={styles.label}>Username</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g., devesh#4597"
        value={userName}
        onChangeText={setUserName}
        autoCapitalize="none"
      />

      <Text style={styles.label}>Email</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g., deveshgoswami1911@gmail.com"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />

      <Text style={styles.label}>Password</Text>
      <TextInput
        style={styles.input}
        placeholder="Enter your password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />

      <Text style={styles.label}>Phone Number</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g., 1234567890"
        value={phoneNumber}
        onChangeText={setPhoneNumber}
        keyboardType="phone-pad"
      />

      <Text style={styles.label}>Building Name</Text>
      <Picker
        selectedValue={buildingId}
        onValueChange={(itemValue) => setBuildingId(itemValue)}
        style={styles.picker}
        enabled={!isLoading}
      >
        {buildings.length === 0 ? (
          <Picker.Item label="Loading buildings..." value="" />
        ) : (
          buildings.map((building) => (
            <Picker.Item
              key={building.id}
              label={building.name}
              value={building.id.toString()}
            />
          ))
        )}
      </Picker>

      <Text style={styles.label}>Building Number</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g., A-101"
        value={buildingNumber}
        onChangeText={setBuildingNumber}
      />

      <Text style={styles.label}>Flat Number</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g., 101"
        value={flatNumber}
        onChangeText={setFlatNumber}
      />

      <Text style={styles.label}>Wing</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g., A"
        value={wing}
        onChangeText={setWing}
      />

      <Button
        title={isLoading ? "Signing up..." : "Sign Up"}
        onPress={handleSignup}
        disabled={isLoading}
      />

      <View style={styles.loginSection}>
        <Text style={styles.loginText}>
          Already have an account?{" "}
          <Text style={styles.link} onPress={() => router.push("/login")}>
            Log In
          </Text>
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 20,
    backgroundColor: "#f5f5f5",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
    textAlign: "center",
  },
  label: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 5,
    color: "#333",
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    padding: 12,
    marginBottom: 15,
    borderRadius: 5,
    backgroundColor: "#fff",
    fontSize: 16,
  },
  picker: {
    borderWidth: 1,
    borderColor: "#ccc",
    padding: 12,
    marginBottom: 15,
    borderRadius: 5,
    backgroundColor: "#fff",
    fontSize: 16,
  },
  loginSection: {
    marginTop: 20,
  },
  loginText: {
    textAlign: "center",
    fontSize: 16,
    color: "#666",
  },
  link: {
    color: "#007AFF",
    fontWeight: "bold",
  },
});

export default Signup;
