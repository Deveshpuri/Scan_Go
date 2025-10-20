import { View, Text, TouchableOpacity } from 'react-native';
import tw from 'twrnc';
import { useRouter } from 'expo-router';

export default function Profile() {
  const router = useRouter();

  // Mock user data (replace with API call)
  const user = {
    name: 'John Doe',
    email: 'john.doe@example.com',
    vehicle: { plate: 'ABC123', status: 'Approved' },
  };

  const handleLogout = () => {
    // Mock logout logic (replace with actual logout)
    console.log('Logging out');
    router.replace('/login');
  };

  return (
    <View style={tw`flex-1 p-4 bg-gray-100`}>
      <Text style={tw`text-2xl font-bold mb-4`}>Profile</Text>
      <View style={tw`bg-white p-4 rounded-lg shadow mb-4`}>
        <Text style={tw`text-lg font-semibold`}>User Information</Text>
        <Text style={tw`text-gray-600`}>Name: {user.name}</Text>
        <Text style={tw`text-gray-600`}>Email: {user.email}</Text>
        <Text style={tw`text-gray-600`}>Vehicle Plate: {user.vehicle.plate}</Text>
        <Text style={tw`text-gray-600`}>Status: {user.vehicle.status}</Text>
      </View>
      <TouchableOpacity
        style={tw`bg-red-600 p-3 rounded-lg`}
        onPress={handleLogout}
      >
        <Text style={tw`text-white text-center font-semibold`}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
}