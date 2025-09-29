/**
 * Device Assignment Page - Assign timer and sensor devices to bridge configuration
 */

import React, { useState, useEffect } from 'react';
import { ArrowLeftIcon, ClockIcon, WifiIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';

interface Device {
  address: string;
  label?: string;
  rssi?: number;
  battery?: number;
  type?: string;
  status?: string;
}

interface BridgeConfig {
  timer?: {
    address: string;
    status: string;
  };
  sensors?: {
    address: string;
    status: string;
  }[];
}

interface Notification {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

export const DeviceAssignmentPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [bridgeConfig, setBridgeConfig] = useState<BridgeConfig | null>(null);
  const [selectedTimer, setSelectedTimer] = useState<string>('');
  const [selectedSensors, setSelectedSensors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const API_BASE = `${window.location.protocol}//${window.location.hostname}:8001`;

  // Show notification
  const showNotification = (message: string, type: Notification['type'] = 'info') => {
    const notification: Notification = {
      id: Date.now(),
      message,
      type
    };
    
    setNotifications(prev => [...prev, notification]);
    
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  // Fetch JSON with error handling
  const fetchJSON = async (url: string) => {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Fetch error:', error);
      return null;
    }
  };

  // Load current bridge configuration
  const loadBridgeConfig = async () => {
    const config = await fetchJSON(`${API_BASE}/api/admin/bridge/config`);
    if (config) {
      setBridgeConfig(config);
      setSelectedTimer(config.timer?.address || '');
      setSelectedSensors(config.sensors?.map((s: any) => s.address) || []);
    }
  };

  // Load available devices
  const loadDevices = async () => {
    const data = await fetchJSON(`${API_BASE}/api/admin/devices`);
    if (data && data.devices) {
      setDevices(data.devices);
      console.log('Loaded devices:', data.devices);
    } else {
      showNotification('Failed to load devices', 'error');
    }
  };

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        await Promise.all([loadBridgeConfig(), loadDevices()]);
        showNotification('Device assignment interface ready', 'success');
      } catch (error) {
        console.error('Load error:', error);
        showNotification('Failed to load data', 'error');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, []);

  // Filter devices by type
  const timerDevices = devices.filter(d => {
    const isTimerByLabel = d.label?.toLowerCase().includes('timer');
    const isTimerByAddress = d.address === '60:09:C3:1F:DC:1A'; // Known AMG Timer
    return isTimerByLabel || isTimerByAddress;
  });

  const sensorDevices = devices.filter(d => {
    const isTimerByLabel = d.label?.toLowerCase().includes('timer');
    const isTimerByAddress = d.address === '60:09:C3:1F:DC:1A';
    return !(isTimerByLabel || isTimerByAddress);
  });

  // Handle sensor checkbox change
  const handleSensorToggle = (address: string) => {
    setSelectedSensors(prev => 
      prev.includes(address) 
        ? prev.filter(s => s !== address)
        : [...prev, address]
    );
  };

  // Save assignment
  const saveAssignment = async () => {
    setSaving(true);
    
    try {
      const response = await fetch(`${API_BASE}/api/admin/bridge/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timer: selectedTimer || null,
          sensors: selectedSensors
        })
      });
      
      if (response.ok) {
        showNotification(`✅ Assignment saved: ${selectedTimer ? '1 timer' : 'no timer'}, ${selectedSensors.length} sensors`, 'success');
        await loadBridgeConfig();
      } else {
        const error = await response.json();
        showNotification(`❌ Save failed: ${error.error || 'Unknown error'}`, 'error');
      }
    } catch (error) {
      console.error('Save error:', error);
      showNotification('❌ Save failed: Network error', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Clear assignments
  const clearAssignment = async () => {
    if (!confirm('Clear all device assignments from bridge configuration?')) {
      return;
    }
    
    setSaving(true);
    
    try {
      const response = await fetch(`${API_BASE}/api/admin/bridge/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timer: null,
          sensors: []
        })
      });
      
      if (response.ok) {
        showNotification('🗑️ All assignments cleared', 'success');
        setSelectedTimer('');
        setSelectedSensors([]);
        await loadBridgeConfig();
      } else {
        const error = await response.json();
        showNotification(`❌ Clear failed: ${error.error}`, 'error');
      }
    } catch (error) {
      console.error('Clear error:', error);
      showNotification('❌ Clear failed: Network error', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Refresh data
  const refreshData = async () => {
    setLoading(true);
    try {
      await Promise.all([loadBridgeConfig(), loadDevices()]);
      showNotification('🔄 Data refreshed', 'success');
    } catch (error) {
      console.error('Refresh error:', error);
      showNotification('❌ Refresh failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading device assignment interface...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Notifications */}
      <div className="fixed top-4 right-4 space-y-2 z-50">
        {notifications.map(notification => (
          <div
            key={notification.id}
            className={`px-4 py-2 rounded-lg shadow-lg transition-all ${
              notification.type === 'success' ? 'bg-green-500 text-white' :
              notification.type === 'error' ? 'bg-red-500 text-white' :
              notification.type === 'warning' ? 'bg-yellow-500 text-black' :
              'bg-blue-500 text-white'
            }`}
          >
            {notification.message}
          </div>
        ))}
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow border mb-6 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
                🎯 Device Assignment
              </h1>
              <p className="text-gray-600">Assign timer and sensor devices to bridge configuration</p>
            </div>
            <Link 
              to="/" 
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors"
            >
              <ArrowLeftIcon className="h-5 w-5 mr-2" />
              Back to Dashboard
            </Link>
          </div>
        </div>

        {/* Current Assignment Status */}
        <div className="bg-white rounded-lg shadow border mb-6">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900">Current Bridge Configuration</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="font-medium flex items-center">
                  <ClockIcon className="h-5 w-5 mr-2 text-blue-600" />
                  Timer Device:
                </span>
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-sm">
                    {bridgeConfig?.timer?.address || 'None assigned'}
                  </span>
                  {bridgeConfig?.timer?.status === 'configured' ? (
                    <CheckCircleIcon className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircleIcon className="h-5 w-5 text-gray-400" />
                  )}
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-medium flex items-center">
                  <WifiIcon className="h-5 w-5 mr-2 text-green-600" />
                  Sensor Devices:
                </span>
                <span className="text-gray-600">
                  {bridgeConfig?.sensors?.length || 0} sensors assigned
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Device Assignment Interface */}
        <div className="bg-white rounded-lg shadow border mb-6">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900">Assign Devices</h2>
            <p className="text-sm text-gray-600 mt-1">Select devices from the pool to assign to bridge</p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Timer Assignment */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <ClockIcon className="h-6 w-6 mr-2 text-blue-600" />
                  Timer Device
                </h3>
                
                <select
                  value={selectedTimer}
                  onChange={(e) => setSelectedTimer(e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
                >
                  <option value="">No timer assigned</option>
                  {timerDevices.map(timer => {
                    const name = timer.label || 'AMG Timer';
                    const addr = timer.address.slice(-8);
                    const signal = timer.rssi ? `${timer.rssi} dBm` : 'N/A';
                    return (
                      <option key={timer.address} value={timer.address}>
                        {name} ({addr}) - Signal: {signal}
                      </option>
                    );
                  })}
                </select>
                
                <p className="text-sm text-gray-500 mt-2">Select the AMG Timer device for match timing</p>
              </div>

              {/* Sensor Assignment */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <WifiIcon className="h-6 w-6 mr-2 text-green-600" />
                  Impact Sensors
                </h3>
                
                <div className="space-y-3 max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50">
                  {sensorDevices.length === 0 ? (
                    <p className="text-gray-500">No sensor devices available</p>
                  ) : (
                    sensorDevices.map(sensor => {
                      const name = sensor.label || 'BT50 Sensor';
                      const addr = sensor.address.slice(-8);
                      const signal = sensor.rssi ? `${sensor.rssi} dBm` : 'N/A';
                      const battery = sensor.battery ? `${sensor.battery}%` : 'N/A';
                      const isSelected = selectedSensors.includes(sensor.address);
                      
                      return (
                        <div
                          key={sensor.address}
                          className="flex items-center space-x-3 p-3 bg-white border rounded-lg cursor-pointer hover:bg-blue-50 transition-colors"
                          onClick={() => handleSensorToggle(sensor.address)}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleSensorToggle(sensor.address)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <div className="flex-1">
                            <div className="font-medium text-gray-900">{name}</div>
                            <div className="text-sm text-gray-500">
                              {addr} • Signal: {signal} • Battery: {battery}
                            </div>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
                
                <p className="text-sm text-gray-500 mt-2">Select BT50 sensors for target impact detection</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-8 flex items-center space-x-4">
              <button
                onClick={saveAssignment}
                disabled={saving}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-base"
              >
                {saving ? '💾 Saving...' : '💾 Save Assignment'}
              </button>
              <button
                onClick={clearAssignment}
                disabled={saving}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-base"
              >
                🗑️ Clear All
              </button>
              <button
                onClick={refreshData}
                disabled={loading}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-base"
              >
                {loading ? '🔄 Refreshing...' : '🔄 Refresh'}
              </button>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">📋 Instructions</h3>
          <ol className="list-decimal list-inside space-y-2 text-blue-800">
            <li><strong>Timer Assignment:</strong> Select your AMG Timer device from the dropdown</li>
            <li><strong>Sensor Assignment:</strong> Check the BT50 sensor devices you want to use</li>
            <li><strong>Save Configuration:</strong> Click "Save Assignment" to update bridge config</li>
            <li><strong>Bridge Integration:</strong> The bridge will connect to assigned devices automatically</li>
          </ol>
          <div className="mt-4 p-3 bg-blue-100 rounded text-sm">
            <strong>Note:</strong> Make sure devices are paired and showing in the device pool before assigning them.
          </div>
        </div>
      </div>
    </div>
  );
};