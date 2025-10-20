import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function Scan() {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);

  const handleScan = () => {
    setIsScanning(true);
    // Simulate scan process
    setTimeout(() => {
      setIsScanning(false);
      const result = {
        id: 'SCAN_' + Date.now(),
        type: 'QR Code',
        data: 'Visitor ID: V12345',
        timestamp: new Date().toLocaleString(),
        status: 'success'
      };
      setScanResult(result);
      Alert.alert('Scan Successful', `Visitor ID: V12345 scanned successfully!`);
    }, 2000);
  };

  const closeResult = () => {
    setScanResult(null);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Scanner Preview */}
        <View style={styles.scannerContainer}>
          <View style={styles.scannerFrame}>
            <View style={styles.cornerTL} />
            <View style={styles.cornerTR} />
            <View style={styles.cornerBL} />
            <View style={styles.cornerBR} />
          </View>
          
          {isScanning && (
            <View style={styles.scanningLine} />
          )}
        </View>

        {/* Instructions */}
        <View style={styles.instructions}>
          <Text style={styles.instructionTitle}>Position QR Code</Text>
          <Text style={styles.instructionText}>
            Align the QR code within the frame to scan
          </Text>
        </View>

        {/* Scan Button */}
        <TouchableOpacity
          style={[styles.scanButton, isScanning && styles.scanButtonDisabled]}
          onPress={handleScan}
          disabled={isScanning}
        >
          <Ionicons 
            name={isScanning ? "scan" : "camera"} 
            size={24} 
            color="white" 
          />
          <Text style={styles.scanButtonText}>
            {isScanning ? 'Scanning...' : 'Start Scanning'}
          </Text>
        </TouchableOpacity>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.quickAction}>
            <Ionicons name="flashlight" size={20} color="#007AFF" />
            <Text style={styles.quickActionText}>Flash</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickAction}>
            <Ionicons name="images" size={20} color="#007AFF" />
            <Text style={styles.quickActionText}>Gallery</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Scan Result Modal */}
      <Modal
        visible={!!scanResult}
        animationType="slide"
        transparent={true}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Scan Result</Text>
              <TouchableOpacity onPress={closeResult}>
                <Ionicons name="close" size={24} color="#333" />
              </TouchableOpacity>
            </View>
            
            {scanResult && (
              <View style={styles.resultContent}>
                <View style={styles.successIcon}>
                  <Ionicons name="checkmark-circle" size={64} color="#34C759" />
                </View>
                <Text style={styles.resultTitle}>Scan Successful!</Text>
                <View style={styles.resultDetails}>
                  <Text style={styles.resultLabel}>Visitor ID:</Text>
                  <Text style={styles.resultValue}>V12345</Text>
                  
                  <Text style={styles.resultLabel}>Time:</Text>
                  <Text style={styles.resultValue}>{scanResult.timestamp}</Text>
                  
                  <Text style={styles.resultLabel}>Status:</Text>
                  <Text style={[styles.resultValue, styles.statusSuccess]}>Verified</Text>
                </View>
                
                <TouchableOpacity style={styles.doneButton} onPress={closeResult}>
                  <Text style={styles.doneButtonText}>Done</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  scannerContainer: {
    width: 300,
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 40,
    position: 'relative',
  },
  scannerFrame: {
    width: 250,
    height: 250,
    borderWidth: 2,
    borderColor: '#fff',
    borderRadius: 20,
    position: 'relative',
  },
  cornerTL: {
    position: 'absolute',
    top: -2,
    left: -2,
    width: 30,
    height: 30,
    borderTopWidth: 4,
    borderLeftWidth: 4,
    borderColor: '#007AFF',
    borderRadius: 2,
  },
  cornerTR: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 30,
    height: 30,
    borderTopWidth: 4,
    borderRightWidth: 4,
    borderColor: '#007AFF',
    borderRadius: 2,
  },
  cornerBL: {
    position: 'absolute',
    bottom: -2,
    left: -2,
    width: 30,
    height: 30,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
    borderColor: '#007AFF',
    borderRadius: 2,
  },
  cornerBR: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 30,
    height: 30,
    borderBottomWidth: 4,
    borderRightWidth: 4,
    borderColor: '#007AFF',
    borderRadius: 2,
  },
  scanningLine: {
    width: 200,
    height: 2,
    backgroundColor: '#007AFF',
    position: 'absolute',
  },
  instructions: {
    alignItems: 'center',
    marginBottom: 40,
  },
  instructionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  instructionText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
  },
  scanButton: {
    flexDirection: 'row',
    backgroundColor: '#007AFF',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
    alignItems: 'center',
    marginBottom: 20,
  },
  scanButtonDisabled: {
    backgroundColor: '#666',
  },
  scanButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 10,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 40,
  },
  quickAction: {
    alignItems: 'center',
  },
  quickActionText: {
    color: 'white',
    fontSize: 12,
    marginTop: 5,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    padding: 20,
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 20,
    width: '100%',
    maxWidth: 400,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  resultContent: {
    alignItems: 'center',
  },
  successIcon: {
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  resultDetails: {
    width: '100%',
    marginBottom: 30,
  },
  resultLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  resultValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  statusSuccess: {
    color: '#34C759',
  },
  doneButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 40,
    paddingVertical: 12,
    borderRadius: 25,
    width: '100%',
    alignItems: 'center',
  },
  doneButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});