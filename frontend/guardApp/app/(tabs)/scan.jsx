


import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Modal,
  TextInput,
  ScrollView,
  ActivityIndicator,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { apiService } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function Scan() {
  const [facing, setFacing] = useState('back');
  const [permission, requestPermission] = useCameraPermissions();
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [ocrData, setOcrData] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const cameraRef = useRef(null);

  // Request camera permissions
  useEffect(() => {
    if (!permission) {
      requestPermission();
    }
  }, [permission]);

  // Get auth token from storage
  const getAuthToken = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      return token;
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  };

  // Take picture function
  const takePicture = async () => {
    if (cameraRef.current) {
      setIsScanning(true);
      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.7,
          base64: true,
          exif: false
        });
        setCapturedImage(photo.uri);
        await processImage(photo.base64);
      } catch (error) {
        console.error('Error taking picture:', error);
        Alert.alert('Error', 'Failed to take picture');
        setIsScanning(false);
      }
    }
  };

  // Pick image from gallery
  const pickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.7,
        base64: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        setCapturedImage(result.assets[0].uri);
        await processImage(result.assets[0].base64);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  // Process image with OCR API - FIXED VERSION
  const processImage = async (base64Image) => {
    setLoading(true);
    try {
      const authToken = await getAuthToken();
      
      if (!authToken) {
        Alert.alert('Error', 'Authentication required. Please login again.');
        setLoading(false);
        setIsScanning(false);
        return;
      }

      // FIX: Proper base64 format
      const imageData = `data:image/jpeg;base64,${base64Image}`;

      // Call OCR API
      const ocrResult = await apiService.ocr.processImage(imageData, authToken);
      
      // Handle OCR response - FIXED response structure
      if (ocrResult && ocrResult.success) {
        setOcrData(ocrResult.data);
        setFormData(prev => ({
          ...prev,
          numberPlate: ocrResult.data.numberPlate || '',
          vehicleType: ocrResult.data.vehicleType || '',
          ownerName: ocrResult.data.ownerName || ''
        }));
        setScanResult('success');
        Alert.alert('Success', 'Number plate detected successfully!');
      } else {
        // If OCR fails, show manual entry form
        setOcrData(null);
        setScanResult('manual_entry');
        
        Alert.alert(
          'OCR Failed', 
          ocrResult?.message || 'Could not automatically read number plate. Please enter details manually.',
          [{ text: 'OK' }]
        );
      }
      
    } catch (error) {
      console.error('OCR Error:', error);
      
      // Fallback to manual entry on any error
      setOcrData(null);
      setScanResult('manual_entry');
      
      Alert.alert(
        'Processing Failed', 
        error.message || 'Failed to process image. Please enter details manually.',
        [{ text: 'OK' }]
      );
    } finally {
      setLoading(false);
      setIsScanning(false);
    }
  };

  // Handle form input changes
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Submit form data
  const handleSubmit = async () => {
    // Validate required fields
    if (!formData.numberPlate || !formData.vehicleType) {
      Alert.alert('Error', 'Number Plate and Vehicle Type are required fields');
      return;
    }

    setLoading(true);
    try {
      // Call your vehicle registration API
      await apiService.vehicle.register(formData);
      Alert.alert('Success', 'Vehicle data submitted successfully!');
      resetScanner();
    } catch (error) {
      console.error('Submit Error:', error);
      Alert.alert('Error', error.message || 'Failed to submit data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Reset scanner to initial state
  const resetScanner = () => {
    setCapturedImage(null);
    setOcrData(null);
    setFormData({});
    setScanResult(null);
    setIsScanning(false);
  };

  // Toggle camera facing
  const toggleCameraFacing = () => {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  };

  if (!permission) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionText}>Requesting camera permission...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionText}>We need your permission to use the camera</Text>
          <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
            <Text style={styles.permissionButtonText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {!capturedImage ? (
        // Camera View
        <View style={styles.cameraContainer}>
          <CameraView
            ref={cameraRef}
            style={styles.camera}
            facing={facing}
            mode="picture"
          >
            <View style={styles.cameraOverlay}>
              {/* Scanner Frame */}
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
          </CameraView>

          {/* Camera Controls */}
          <View style={styles.controlsContainer}>
            <TouchableOpacity style={styles.galleryButton} onPress={pickImage}>
              <Ionicons name="images" size={24} color="white" />
              <Text style={styles.galleryText}>Gallery</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.captureButton, isScanning && styles.captureButtonDisabled]}
              onPress={takePicture}
              disabled={isScanning}
            >
              {isScanning ? (
                <ActivityIndicator color="white" />
              ) : (
                <View style={styles.captureButtonInner} />
              )}
            </TouchableOpacity>

            <TouchableOpacity style={styles.flipButton} onPress={toggleCameraFacing}>
              <Ionicons name="camera-reverse" size={24} color="white" />
              <Text style={styles.flipText}>Flip</Text>
            </TouchableOpacity>
          </View>

          {/* Instructions */}
          <View style={styles.instructions}>
            <Text style={styles.instructionTitle}>Position Number Plate</Text>
            <Text style={styles.instructionText}>
              Align the vehicle number plate within the frame
            </Text>
          </View>
        </View>
      ) : (
        // Form View after image capture
        <View style={styles.formContainer}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            {/* Captured Image Preview */}
            <View style={styles.imagePreviewContainer}>
              <Image source={{ uri: capturedImage }} style={styles.capturedImage} />
              <TouchableOpacity style={styles.retakeButton} onPress={resetScanner}>
                <Ionicons name="camera" size={20} color="white" />
                <Text style={styles.retakeText}>Retake</Text>
              </TouchableOpacity>
            </View>

            {/* OCR Extracted Data */}
            {ocrData && scanResult === 'success' && (
              <View style={styles.ocrSection}>
                <Text style={styles.sectionTitle}>Extracted Data</Text>
                <View style={styles.ocrData}>
                  <Text style={styles.ocrText}>
                    Number Plate: <Text style={styles.ocrValue}>{ocrData.numberPlate}</Text>
                  </Text>
                  <Text style={styles.ocrText}>
                    Vehicle Type: <Text style={styles.ocrValue}>{ocrData.vehicleType}</Text>
                  </Text>
                  {ocrData.ownerName && (
                    <Text style={styles.ocrText}>
                      Owner: <Text style={styles.ocrValue}>{ocrData.ownerName}</Text>
                    </Text>
                  )}
                </View>
              </View>
            )}

            {scanResult === 'manual_entry' && (
              <View style={styles.manualEntrySection}>
                <Ionicons name="information-circle" size={24} color="#FF9500" />
                <Text style={styles.manualEntryText}>
                  Could not automatically read number plate. Please enter details below.
                </Text>
              </View>
            )}

            {/* Editable Form */}
            <View style={styles.formSection}>
              <Text style={styles.sectionTitle}>Vehicle Information</Text>
              
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Number Plate *</Text>
                <TextInput
                  style={styles.input}
                  value={formData.numberPlate || ''}
                  onChangeText={(text) => handleInputChange('numberPlate', text)}
                  placeholder="Enter number plate"
                  autoCapitalize="characters"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Vehicle Type *</Text>
                <TextInput
                  style={styles.input}
                  value={formData.vehicleType || ''}
                  onChangeText={(text) => handleInputChange('vehicleType', text)}
                  placeholder="e.g., Car, Bike, Truck"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Owner Name</Text>
                <TextInput
                  style={styles.input}
                  value={formData.ownerName || ''}
                  onChangeText={(text) => handleInputChange('ownerName', text)}
                  placeholder="Enter owner name"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Vehicle Model</Text>
                <TextInput
                  style={styles.input}
                  value={formData.vehicleModel || ''}
                  onChangeText={(text) => handleInputChange('vehicleModel', text)}
                  placeholder="Enter vehicle model"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Color</Text>
                <TextInput
                  style={styles.input}
                  value={formData.color || ''}
                  onChangeText={(text) => handleInputChange('color', text)}
                  placeholder="Enter vehicle color"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Registration Date</Text>
                <TextInput
                  style={styles.input}
                  value={formData.registrationDate || ''}
                  onChangeText={(text) => handleInputChange('registrationDate', text)}
                  placeholder="YYYY-MM-DD"
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Expiry Date</Text>
                <TextInput
                  style={styles.input}
                  value={formData.expiryDate || ''}
                  onChangeText={(text) => handleInputChange('expiryDate', text)}
                  placeholder="YYYY-MM-DD"
                />
              </View>
            </View>

            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity 
                style={[styles.button, styles.cancelButton]} 
                onPress={resetScanner}
                disabled={loading}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.button, styles.submitButton, 
                  (!formData.numberPlate || !formData.vehicleType) && styles.submitButtonDisabled
                ]} 
                onPress={handleSubmit}
                disabled={loading || !formData.numberPlate || !formData.vehicleType}
              >
                {loading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text style={styles.submitButtonText}>Submit</Text>
                )}
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      )}

      {/* Loading Modal */}
      <Modal visible={loading} transparent animationType="fade">
        <View style={styles.loadingModal}>
          <View style={styles.loadingContent}>
            <ActivityIndicator size="large" color="#007AFF" />
            <Text style={styles.loadingText}>Processing image...</Text>
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
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  permissionText: {
    color: 'white',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
  },
  permissionButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  cameraContainer: {
    flex: 1,
  },
  camera: {
    flex: 1,
  },
  cameraOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'transparent',
  },
  scannerFrame: {
    width: 300,
    height: 200,
    borderWidth: 2,
    borderColor: '#fff',
    borderRadius: 12,
    position: 'relative',
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  cornerTL: {
    position: 'absolute',
    top: -2,
    left: -2,
    width: 25,
    height: 25,
    borderTopWidth: 3,
    borderLeftWidth: 3,
    borderColor: '#007AFF',
  },
  cornerTR: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 25,
    height: 25,
    borderTopWidth: 3,
    borderRightWidth: 3,
    borderColor: '#007AFF',
  },
  cornerBL: {
    position: 'absolute',
    bottom: -2,
    left: -2,
    width: 25,
    height: 25,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
    borderColor: '#007AFF',
  },
  cornerBR: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 25,
    height: 25,
    borderBottomWidth: 3,
    borderRightWidth: 3,
    borderColor: '#007AFF',
  },
  scanningLine: {
    width: 280,
    height: 2,
    backgroundColor: '#007AFF',
    position: 'absolute',
  },
  controlsContainer: {
    position: 'absolute',
    bottom: 40,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  galleryButton: {
    alignItems: 'center',
  },
  galleryText: {
    color: 'white',
    fontSize: 12,
    marginTop: 5,
  },
  captureButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: 'white',
  },
  captureButtonDisabled: {
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  captureButtonInner: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'white',
  },
  flipButton: {
    alignItems: 'center',
  },
  flipText: {
    color: 'white',
    fontSize: 12,
    marginTop: 5,
  },
  instructions: {
    position: 'absolute',
    top: 100,
    left: 0,
    right: 0,
    alignItems: 'center',
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
    paddingHorizontal: 40,
  },
  formContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  imagePreviewContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  capturedImage: {
    width: '100%',
    height: 200,
    borderRadius: 12,
    marginBottom: 10,
  },
  retakeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  retakeText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 5,
  },
  ocrSection: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  manualEntrySection: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3CD',
    padding: 15,
    borderRadius: 12,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#FFA000',
  },
  manualEntryText: {
    flex: 1,
    marginLeft: 10,
    color: '#856404',
    fontSize: 14,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  ocrData: {
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
  },
  ocrText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  ocrValue: {
    fontWeight: '600',
    color: '#333',
  },
  formSection: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  inputGroup: {
    marginBottom: 15,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 15,
  },
  button: {
    flex: 1,
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#007AFF',
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingModal: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  loadingContent: {
    backgroundColor: 'white',
    padding: 30,
    borderRadius: 12,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#333',
  },
});