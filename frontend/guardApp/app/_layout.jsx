
import React from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
// import { useFonts } from "expo-font";
import Toast from "react-native-toast-message";
// import { UserProvider } from "../contexts/UserContext";

export default function RootLayout() {

  return (
    <>
      {/* <UserProvider> */}
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="Login" />
          <Stack.Screen
            name="(tabs)"
            options={{ headerShown: false }}
          ></Stack.Screen>
        </Stack>
        <Toast />
        <StatusBar backgroundColor="white" style="dark" />
      {/* </UserProvider> */}
    </>
  );
}
