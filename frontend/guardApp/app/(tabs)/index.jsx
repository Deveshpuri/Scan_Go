import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { apiService } from '../../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [lastScan, setLastScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsResponse, lastScanResponse] = await Promise.all([
        apiService.dashboard.getStats(),
        apiService.dashboard.getLastScan()
      ]);
      
      setStats(statsResponse.stats);
      setLastScan(lastScanResponse.last_scan);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      Alert.alert('Error', 'Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Pull to refresh
  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  const statsData = stats ? [
    { title: 'Total Scans', value: stats.total_scans?.toString() || '0', icon: 'scan', color: '#007AFF' },
    { title: "Today's Scans", value: stats.today_scans?.toString() || '0', icon: 'today', color: '#34C759' },
    { title: 'Total Entries', value: stats.total_entries?.toString() || '0', icon: 'log-in', color: '#FF9500' },
    { title: 'Total Exits', value: stats.total_exits?.toString() || '0', icon: 'log-out', color: '#FF3B30' },
  ] : [];

  const quickActions = [
    { title: 'Quick Scan', icon: 'qr-code', screen: 'scan' },
    { title: 'View Logs', icon: 'document-text', screen: 'logs' },
    { title: 'My Profile', icon: 'person', screen: 'profile' },
  ];

  const getScanStatusColor = (result) => {
    switch (result) {
      case 'success': return '#34C759';
      case 'not_found': return '#FF9500';
      case 'error': return '#FF3B30';
      default: return '#666';
    }
  };

  const getScanStatusText = (result) => {
    switch (result) {
      case 'success': return 'Success';
      case 'not_found': return 'Not Found';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Dashboard</Text>
          <Text style={styles.headerSubtitle}>Welcome back, Guard!</Text>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsContainer}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Overview</Text>
            <TouchableOpacity onPress={fetchDashboardData}>
              <Ionicons name="refresh" size={20} color="#007AFF" />
            </TouchableOpacity>
          </View>
          <View style={styles.statsGrid}>
            {statsData.map((stat, index) => (
              <View key={index} style={styles.statCard}>
                <View style={[styles.statIcon, { backgroundColor: `${stat.color}20` }]}>
                  <Ionicons name={stat.icon} size={24} color={stat.color} />
                </View>
                <Text style={styles.statValue}>{stat.value}</Text>
                <Text style={styles.statTitle}>{stat.title}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.actionsContainer}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.actionsGrid}>
            {quickActions.map((action, index) => (
              <TouchableOpacity 
                key={index} 
                style={styles.actionCard}
                onPress={() => router.push(`/(tabs)/${action.screen}`)}
              >
                <View style={styles.actionIcon}>
                  <Ionicons name={action.icon} size={32} color="#007AFF" />
                </View>
                <Text style={styles.actionTitle}>{action.title}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Last Scan Activity */}
        <View style={styles.activityContainer}>
          <Text style={styles.sectionTitle}>Last Scan</Text>
          {lastScan ? (
            <View style={styles.lastScanCard}>
              <View style={styles.lastScanHeader}>
                <View style={styles.licensePlateContainer}>
                  <Ionicons name="car" size={20} color="#666" />
                  <Text style={styles.licensePlate}>
                    {lastScan.license_plate || 'UNKNOWN'}
                  </Text>
                </View>
                <View style={[
                  styles.statusBadge,
                  { backgroundColor: `${getScanStatusColor(lastScan.result)}20` }
                ]}>
                  <Text style={[styles.statusText, { color: getScanStatusColor(lastScan.result) }]}>
                    {getScanStatusText(lastScan.result)}
                  </Text>
                </View>
              </View>

              <View style={styles.scanDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Action:</Text>
                  <Text style={styles.detailValue}>
                    {lastScan.action === 'scan' ? 'Scan' : lastScan.action}
                  </Text>
                </View>
                
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Time:</Text>
                  <Text style={styles.detailValue}>
                    {formatTimestamp(lastScan.timestamp)}
                  </Text>
                </View>

                {lastScan.notes && (
                  <View style={styles.notesContainer}>
                    <Text style={styles.notesLabel}>Notes:</Text>
                    <Text style={styles.notesText}>{lastScan.notes}</Text>
                  </View>
                )}
              </View>

              <TouchableOpacity 
                style={styles.viewAllButton}
                onPress={() => router.push('/(tabs)/logs')}
              >
                <Text style={styles.viewAllText}>View All Scans</Text>
                <Ionicons name="arrow-forward" size={16} color="#007AFF" />
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.noDataCard}>
              <Ionicons name="scan-outline" size={48} color="#ccc" />
              <Text style={styles.noDataText}>No scans yet</Text>
              <Text style={styles.noDataSubtext}>Start scanning to see activity here</Text>
              <TouchableOpacity 
                style={styles.startScanButton}
                onPress={() => router.push('/(tabs)/scan')}
              >
                <Text style={styles.startScanText}>Start Scanning</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Recent Activity Summary */}
        {stats && stats.today_scans > 0 && (
          <View style={styles.summaryContainer}>
            <Text style={styles.sectionTitle}>Today's Summary</Text>
            <View style={styles.summaryGrid}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{stats.today_scans}</Text>
                <Text style={styles.summaryLabel}>Scans Today</Text>
              </View>
              <View style={styles.summaryDivider} />
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{stats.total_entries}</Text>
                <Text style={styles.summaryLabel}>Entries</Text>
              </View>
              <View style={styles.summaryDivider} />
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{stats.total_exits}</Text>
                <Text style={styles.summaryLabel}>Exits</Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 20,
  },
  header: {
    backgroundColor: '#007AFF',
    padding: 20,
    paddingTop: 60,
    paddingBottom: 30,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 5,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
  },
  statsContainer: {
    padding: 20,
    paddingBottom: 10,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  statTitle: {
    fontSize: 14,
    color: '#666',
  },
  actionsContainer: {
    padding: 20,
    paddingTop: 0,
  },
  actionsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '31%',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionIcon: {
    marginBottom: 10,
  },
  actionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
  activityContainer: {
    padding: 20,
    paddingTop: 0,
  },
  lastScanCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  lastScanHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  licensePlateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  licensePlate: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 8,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  scanDetails: {
    marginBottom: 15,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  detailValue: {
    fontSize: 14,
    color: '#333',
    fontWeight: '600',
  },
  notesContainer: {
    marginTop: 10,
    padding: 12,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
  },
  notesLabel: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
    marginBottom: 4,
  },
  notesText: {
    fontSize: 12,
    color: '#666',
    lineHeight: 16,
  },
  viewAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  viewAllText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
    marginRight: 5,
  },
  noDataCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  noDataText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 10,
  },
  noDataSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    marginTop: 5,
    marginBottom: 20,
  },
  startScanButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  startScanText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  summaryContainer: {
    padding: 20,
    paddingTop: 0,
  },
  summaryGrid: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
  },
  summaryDivider: {
    width: 1,
    backgroundColor: '#e0e0e0',
  },
});