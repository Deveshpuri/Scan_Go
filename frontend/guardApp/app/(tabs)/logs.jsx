import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
  TextInput,
  StatusBar,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function Logs() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');

  const logsData = [
    {
      id: '1',
      visitorId: 'V12345',
      name: 'John Doe',
      purpose: 'Meeting',
      time: '2024-01-15 09:30:00',
      status: 'completed',
      type: 'entry',
    },
    {
      id: '2',
      visitorId: 'V12346',
      name: 'Jane Smith',
      purpose: 'Delivery',
      time: '2024-01-15 10:15:00',
      status: 'completed',
      type: 'entry',
    },
    {
      id: '3',
      visitorId: 'V12347',
      name: 'Mike Johnson',
      purpose: 'Interview',
      time: '2024-01-15 11:00:00',
      status: 'pending',
      type: 'exit',
    },
    {
      id: '4',
      visitorId: 'V12348',
      name: 'Sarah Wilson',
      purpose: 'Client Meeting',
      time: '2024-01-15 14:20:00',
      status: 'completed',
      type: 'entry',
    },
    {
      id: '5',
      visitorId: 'V12349',
      name: 'Robert Brown',
      purpose: 'Maintenance',
      time: '2024-01-15 15:45:00',
      status: 'completed',
      type: 'exit',
    },
  ];

  const filters = [
    { id: 'all', label: 'All' },
    { id: 'completed', label: 'Completed' },
    { id: 'pending', label: 'Pending' },
    { id: 'entry', label: 'Entry' },
    { id: 'exit', label: 'Exit' },
  ];

  const filteredLogs = logsData.filter(log => {
    const matchesSearch = log.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         log.visitorId.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = selectedFilter === 'all' || 
                         log.status === selectedFilter || 
                         log.type === selectedFilter;
    return matchesSearch && matchesFilter;
  });

  const getStatusColor = (status) => {
    return status === 'completed' ? '#34C759' : '#FF9500';
  };

  const getTypeIcon = (type) => {
    return type === 'entry' ? 'log-in' : 'log-out';
  };

  const renderLogItem = ({ item }) => (
    <TouchableOpacity style={styles.logItem}>
      <View style={styles.logIcon}>
        <Ionicons 
          name={getTypeIcon(item.type)} 
          size={20} 
          color={item.type === 'entry' ? '#007AFF' : '#FF9500'} 
        />
      </View>
      <View style={styles.logContent}>
        <View style={styles.logHeader}>
          <Text style={styles.visitorName}>{item.name}</Text>
          <View style={[styles.statusBadge, { backgroundColor: `${getStatusColor(item.status)}20` }]}>
            <Text style={[styles.statusText, { color: getStatusColor(item.status) }]}>
              {item.status}
            </Text>
          </View>
        </View>
        <Text style={styles.visitorId}>ID: {item.visitorId}</Text>
        <Text style={styles.logPurpose}>{item.purpose}</Text>
        <Text style={styles.logTime}>{item.time}</Text>
      </View>
      <Ionicons name="chevron-forward" size={20} color="#ccc" />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="white" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Activity Logs</Text>
        <Text style={styles.headerSubtitle}>Recent scanning activities</Text>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#666" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search logs..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color="#666" />
          </TouchableOpacity>
        )}
      </View>

      {/* Filters */}
      <View style={styles.filtersContainer}>
        <FlatList
          horizontal
          data={filters}
          keyExtractor={(item) => item.id}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filtersList}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[
                styles.filterButton,
                selectedFilter === item.id && styles.filterButtonActive
              ]}
              onPress={() => setSelectedFilter(item.id)}
            >
              <Text
                style={[
                  styles.filterText,
                  selectedFilter === item.id && styles.filterTextActive
                ]}
              >
                {item.label}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Logs List */}
      <View style={styles.logsContainer}>
        <Text style={styles.resultsText}>
          {filteredLogs.length} log{filteredLogs.length !== 1 ? 's' : ''} found
        </Text>
        
        <FlatList
          data={filteredLogs}
          keyExtractor={(item) => item.id}
          renderItem={renderLogItem}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.logsList}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    backgroundColor: 'white',
    padding: 20,
    paddingTop: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 5,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    margin: 20,
    marginBottom: 10,
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  searchIcon: {
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#333',
  },
  filtersContainer: {
    marginHorizontal: 20,
    marginBottom: 10,
  },
  filtersList: {
    paddingVertical: 5,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: 'white',
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  filterButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  filterText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  filterTextActive: {
    color: 'white',
  },
  logsContainer: {
    flex: 1,
    padding: 20,
    paddingTop: 0,
  },
  resultsText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
  },
  logsList: {
    paddingBottom: 20,
  },
  logItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 12,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  logIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  logContent: {
    flex: 1,
  },
  logHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  visitorName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  visitorId: {
    fontSize: 14,
    color: '#666',
    marginBottom: 2,
  },
  logPurpose: {
    fontSize: 14,
    color: '#333',
    marginBottom: 2,
  },
  logTime: {
    fontSize: 12,
    color: '#999',
  },
});