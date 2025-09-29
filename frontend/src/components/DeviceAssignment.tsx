/**
 * Device Assignment Component for Settings Tab
 * Assign timer and sensor devices to bridge configuration
 */

import React, { useState, useEffect } from 'react';

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

export const DeviceAssignment: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [bridgeConfig, setBridgeConfig] = useState<BridgeConfig | null>(null);
  const [selectedTimer, setSelectedTimer] = useState<string>('');
  const [selectedSensors, setSelectedSensors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' }>({ text: '', type: 'info' });

  const API_BASE = `${window.location.protocol}//${window.location.hostname}:8001`;

  // Show message with auto-clear
  const showMessage = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
    setMessage({ text, type });
    if (type !== 'error') {
      setTimeout(() => setMessage({ text: '', type: 'info' }), 5000);
    }
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
      showMessage('Failed to load devices', 'error');
    }
  };

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        await Promise.all([loadBridgeConfig(), loadDevices()]);
        showMessage('Device assignment loaded successfully', 'success');
      } catch (error) {
        console.error('Load error:', error);
        showMessage('Failed to load device data', 'error');
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
        showMessage(`✅ Assignment saved: ${selectedTimer ? '1 timer' : 'no timer'}, ${selectedSensors.length} sensors`, 'success');
        await loadBridgeConfig();
      } else {
        const error = await response.json();
        showMessage(`❌ Save failed: ${error.error || 'Unknown error'}`, 'error');
      }
    } catch (error) {
      console.error('Save error:', error);
      showMessage('❌ Save failed: Network error', 'error');
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
        showMessage('🗑️ All assignments cleared', 'success');
        setSelectedTimer('');
        setSelectedSensors([]);
        await loadBridgeConfig();
      } else {
        const error = await response.json();
        showMessage(`❌ Clear failed: ${error.error}`, 'error');
      }
    } catch (error) {
      console.error('Clear error:', error);
      showMessage('❌ Clear failed: Network error', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading device assignment...</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">🎯 Device Assignment</h2>
      <p className="text-gray-600 mb-6">Assign timer and sensor devices to bridge configuration</p>

      {/* Status Message */}
      {message.text && (
        <div className={`p-4 rounded-lg mb-6 ${
          message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
          message.type === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
          'bg-blue-50 text-blue-800 border border-blue-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* Current Configuration */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h3 className="font-medium mb-3">Current Bridge Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">⏱️ Timer Device:</span>
            <div className="flex items-center space-x-2">
              <span className="font-mono text-sm">{bridgeConfig?.timer?.address || 'None assigned'}</span>
              {bridgeConfig?.timer?.status === 'configured' ? (
                <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">configured</span>
              ) : (
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">not configured</span>
              )}
            </div>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">📡 Sensors:</span>
            <span className="text-sm text-gray-600">{bridgeConfig?.sensors?.length || 0} sensors assigned</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timer Assignment */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">⏱️ Timer Device</h3>
          
          <select
            value={selectedTimer}
            onChange={(e) => setSelectedTimer(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
          <h3 className="text-lg font-medium text-gray-900 mb-3">📡 Impact Sensors</h3>
          
          <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-gray-50">
            {sensorDevices.length === 0 ? (
              <p className="text-gray-500 text-sm">No sensor devices available</p>
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
                    className="flex items-center space-x-3 p-2 bg-white border rounded cursor-pointer hover:bg-blue-50"
                    onClick={() => handleSensorToggle(sensor.address)}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleSensorToggle(sensor.address)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm">{name}</div>
                      <div className="text-xs text-gray-500">
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
      <div className="mt-6 flex space-x-4">
        <button
          onClick={saveAssignment}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {saving ? '💾 Saving...' : '💾 Save Assignment'}
        </button>
        <button
          onClick={clearAssignment}
          disabled={saving}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          🗑️ Clear All
        </button>
      </div>

      {/* Instructions */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">📋 Instructions</h4>
        <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
          <li>Select your AMG Timer device from the dropdown</li>
          <li>Check the BT50 sensor devices you want to use for impact detection</li>
          <li>Click "Save Assignment" to update bridge configuration</li>
          <li>The bridge will automatically connect to assigned devices</li>
        </ol>
      </div>
    </div>
  );
};