import { View, Text, FlatList, TouchableOpacity } from 'react-native';
import tw from 'twrnc';
import { useState, useEffect } from 'react';

export default function Dashboard() {
  // Mock data for parking history (replace with API call)
  const [parkingHistory, setParkingHistory] = useState([
    { id: '1', plate: 'ABC123', timestamp: '2025-10-19 10:00', action: 'Entry' },
    { id: '2', plate: 'ABC123', timestamp: '2025-10-19 18:00', action: 'Exit' },
  ]);

  // Mock billing data
  const [billing, setBilling] = useState({ month: 'October 2025', amount: 50, status: 'Unpaid' });

  useEffect(() => {
    // Fetch parking history and billing from backend API
    // Example: fetch('/api/parking-history').then(res => res.json()).then(setParkingHistory);
  }, []);

  const renderHistoryItem = ({ item }) => (
    <View style={tw`p-4 border-b border-gray-200`}>
      <Text style={tw`text-lg`}>{item.plate}</Text>
      <Text style={tw`text-gray-600`}>{item.timestamp} - {item.action}</Text>
    </View>
  );

  return (
    <View style={tw`flex-1 p-4 bg-gray-100`}>
      <Text style={tw`text-2xl font-bold mb-4`}>Parking Dashboard</Text>
      
      {/* Billing Section */}
      <View style={tw`bg-white p-4 rounded-lg mb-4 shadow`}>
        <Text style={tw`text-lg font-semibold`}>Billing Status</Text>
        <Text style={tw`text-gray-600`}>Month: {billing.month}</Text>
        <Text style={tw`text-gray-600`}>Amount: ${billing.amount}</Text>
        <Text style={tw`${billing.status === 'Unpaid' ? 'text-red-600' : 'text-green-600'}`}>
          Status: {billing.status}
        </Text>
        <TouchableOpacity style={tw`bg-blue-600 p-2 rounded mt-2`}>
          <Text style={tw`text-white text-center`}>Pay Now</Text>
        </TouchableOpacity>
      </View>

      {/* Parking History Section */}
      <Text style={tw`text-lg font-semibold mb-2`}>Parking History</Text>
      <FlatList
        data={parkingHistory}
        renderItem={renderHistoryItem}
        keyExtractor={(item) => item.id}
        style={tw`bg-white rounded-lg shadow`}
      />
    </View>
  );
}