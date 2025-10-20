// import { Stack, useRouter, useSegments } from 'expo-router';
// import { useEffect } from 'react';
// import { View } from 'react-native';
// import tw from 'twrnc';

// // Mock authentication hook (replace with real auth logic)
// const useAuth = () => {
//   // Simulate logged-in state (replace with actual auth check)
//   const isAuthenticated = false; // Change to true for testing protected routes
//   return { isAuthenticated };
// };

// export default function RootLayout() {
//   // const { isAuthenticated } = useAuth();
//   // const segments = useSegments();
//   // const router = useRouter();

//   // useEffect(() => {
//   //   // Redirect based on authentication status
//   //   const inAuthGroup = segments[0] === '(auth)';
//   //   if (!isAuthenticated && !inAuthGroup) {
//   //     router.replace('/login');
//   //   } else if (isAuthenticated && inAuthGroup) {
//   //     router.replace('/home');
//   //   }
//   // }, [isAuthenticated, segments]);

//   return (
//     <View style={tw`flex-1 bg-gray-100`}>
//       <Stack
//         screenOptions={{
//           headerStyle: tw`bg-blue-600`,
//           headerTintColor: '#fff',
//           headerTitleStyle: tw`font-bold`,
//         }}
//       />
//     </View>
//   );
// }

import React from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useFonts } from "expo-font";
import Toast from "react-native-toast-message";
import { UserProvider } from "../contexts/UserContext";

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    Lexend: require("../assets/fonts/Lexend-Regular.ttf"),
  });

  return (
    <>
      <UserProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="login" />
          <Stack.Screen name="signup" />
          <Stack.Screen
            name="(tabs)"
            options={{ headerShown: false }}
          ></Stack.Screen>
        </Stack>
        <Toast />
        <StatusBar backgroundColor="white" style="dark" />
      </UserProvider>
    </>
  );
}
