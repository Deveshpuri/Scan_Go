import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  Button,
  StyleSheet,
  Alert,
  Text as RNText,
} from "react-native";
import { useUser } from "../contexts/UserContext"; // Adjust path based on your project structure
import { useRouter } from "expo-router";

const Login = () => {
  const router = useRouter();

  const [identifier, setIdentifier] = useState(""); // Email or Phone Number
  const [password, setPassword] = useState("");
  const [formLoading, setFormLoading] = useState(false);
  const { login, loading: contextLoading } = useUser();
  const isLoading = formLoading || contextLoading;

  const handleLogin = async () => {
    if (!identifier || !password) {
      Alert.alert("Error", "Please enter your email/phone number and password");
      return;
    }

    setFormLoading(true);
    const result = await login(identifier, password);
    setFormLoading(false);

    if (!result.success) {
      Alert.alert(
        "Login Failed",
        result.error || "Invalid credentials. Please try again."
      );
    } else {
      // Success handled in UserContext (redirects to /home)
      Alert.alert("Success", "Logged in successfully!");
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Login</Text>
      <Text style={styles.label}>Email or Phone Number</Text>
      <TextInput
        style={styles.input}
        placeholder="Enter email (e.g., user@example.com) or phone (e.g., 1234567890)"
        value={identifier}
        onChangeText={setIdentifier}
        keyboardType="email-address" // Defaults to email; changes to numeric if phone detected (optional enhancement)
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
      <Button
        title={isLoading ? "Logging in..." : "Login"}
        onPress={handleLogin}
        disabled={isLoading}
      />
      <View style={styles.signupSection}>
        <RNText style={styles.signupText}>
          Don't have an account?{" "}
          <RNText
            style={styles.link}
            onPress={() => {
              router.push("/signup");
            }}
          >
            Sign Up
          </RNText>
        </RNText>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  signupSection: {
    marginTop: 20,
  },
  signupText: {
    textAlign: "center",
    fontSize: 16,
    color: "#666",
  },
  link: {
    color: "#007AFF",
    fontWeight: "bold",
  },
});

export default Login;
