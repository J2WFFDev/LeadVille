/**
 * Custom hook for managing sensor data and assignments
 */

import { useState, useEffect } from 'react';

interface ConnectedDevice {
  address: string;
  name: string;
  batteryLevel?: number;
  signalStrength?: number;
  lastHit?: Date;
  status: 'connected' | 'disconnected' | 'low-battery' | 'error';
}

interface SensorAssignment {
  targetId: string;
  sensorAddress: string;
}

export const useSensorData = () => {
  const [connectedDevices, setConnectedDevices] = useState<ConnectedDevice[]>([]);
  const [sensorAssignments, setSensorAssignments] = useState<Record<string, SensorAssignment>>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load connected devices from API
  const loadConnectedDevices = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://192.168.1.124:8001/api/connected-devices');
      if (!response.ok) {
        throw new Error(`Failed to load devices: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Convert API format to our device format
      const devices: ConnectedDevice[] = data.map((device: any) => ({
        address: device.address,
        name: device.name || device.address,
        batteryLevel: device.battery_level,
        signalStrength: device.signal_strength,
        lastHit: device.last_hit ? new Date(device.last_hit) : undefined,
        status: determineDeviceStatus(device)
      }));
      
      setConnectedDevices(devices);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Error loading connected devices:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Determine device status based on API data
  const determineDeviceStatus = (device: any): ConnectedDevice['status'] => {
    if (!device.connected) return 'disconnected';
    if (device.battery_level && device.battery_level < 20) return 'low-battery';
    if (device.error) return 'error';
    return 'connected';
  };

  // Update sensor assignment
  const updateSensorAssignment = (targetId: string, sensorAddress: string) => {
    if (sensorAddress === '') {
      // Remove assignment
      setSensorAssignments(prev => {
        const newAssignments = { ...prev };
        delete newAssignments[targetId];
        return newAssignments;
      });
    } else {
      // Add or update assignment
      setSensorAssignments(prev => ({
        ...prev,
        [targetId]: { targetId, sensorAddress }
      }));
    }
  };

  // Handle real-time sensor updates via WebSocket or polling
  const handleSensorUpdate = (sensorData: any) => {
    setConnectedDevices(prev => {
      const deviceIndex = prev.findIndex(device => device.address === sensorData.address);
      
      if (deviceIndex !== -1) {
        // Update existing device
        const updatedDevices = [...prev];
        updatedDevices[deviceIndex] = {
          ...updatedDevices[deviceIndex],
          ...sensorData,
          lastHit: sensorData.last_hit ? new Date(sensorData.last_hit) : updatedDevices[deviceIndex].lastHit,
          status: determineDeviceStatus(sensorData)
        };
        return updatedDevices;
      } else {
        // Add new device
        return [...prev, {
          address: sensorData.address,
          name: sensorData.name || sensorData.address,
          batteryLevel: sensorData.battery_level,
          signalStrength: sensorData.signal_strength,
          lastHit: sensorData.last_hit ? new Date(sensorData.last_hit) : undefined,
          status: determineDeviceStatus(sensorData)
        }];
      }
    });
  };

  // Handle hit detection
  const handleHitDetection = (hitData: any) => {
    const { sensorAddress, timestamp } = hitData;
    
    // Update the device's last hit time
    setConnectedDevices(prev => 
      prev.map(device => 
        device.address === sensorAddress 
          ? { ...device, lastHit: new Date(timestamp) }
          : device
      )
    );
  };

  // Load connected devices on mount
  useEffect(() => {
    loadConnectedDevices();
    
    // Set up periodic refresh
    const interval = setInterval(loadConnectedDevices, 5000); // Refresh every 5 seconds
    
    return () => clearInterval(interval);
  }, []);

  // Set up WebSocket connection for real-time updates (if available)
  useEffect(() => {
    let websocket: WebSocket | null = null;
    
    try {
      websocket = new WebSocket('ws://192.168.1.124:8001/ws');
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'sensor_update':
            handleSensorUpdate(data.data);
            break;
          case 'hit_detection':
            handleHitDetection(data.data);
            break;
          default:
            console.log('Unknown WebSocket message type:', data.type);
        }
      };
      
      websocket.onerror = (error) => {
        console.log('WebSocket error, falling back to polling:', error);
      };
      
    } catch (error) {
      console.log('WebSocket not available, using polling only');
    }
    
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  return {
    connectedDevices,
    sensorAssignments,
    isLoading,
    error,
    loadConnectedDevices,
    updateSensorAssignment,
    handleSensorUpdate,
    handleHitDetection
  };
};