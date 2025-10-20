import { View, Text, Animated, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useEffect, useRef } from 'react';

export default function Index() {
  const router = useRouter();
  const fadeAnim = useRef(new Animated.Value(0)).current; // Initial opacity: 0

  useEffect(() => {
    // Start fade-in animation
    Animated.timing(fadeAnim, {
      toValue: 1, // Fade to full opacity
      duration: 1500, // 1.5 seconds
      useNativeDriver: true,
    }).start();

    // Redirect to login after 2 seconds
    const timer = setTimeout(() => {
      router.replace('/signup');
    }, 2000);

    // Cleanup timer on unmount
    return () => clearTimeout(timer);
  }, [fadeAnim, router]);

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.textContainer, { opacity: fadeAnim }]}>
        <Text style={styles.title}>SCanGo</Text>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#2563EB', // Tailwind's blue-600
  },
  textContainer: {
    // You can add padding/margin/animation-related styles here if needed
  },
  title: {
    fontSize: 32, // Tailwind's text-4xl
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
});
