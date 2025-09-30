/**
 * Device Management Component
 * Handles BLE device discovery, pairing, assignment, and health monitoring
 */

import React, { useState, useEffect } from 'react';
import { endpointConfig } from '../config/endpoints';

interface Device {
  id?: number;
  address: string;
  label?: string;
  name?: string;
  type: string;
  vendor?: string;
  battery?: number;
  rssi?: number;
  last_seen?: string;
  target_id?: number;
  target_name?: string;
  status: 'connected' | 'offline' | 'low_battery' | 'weak_signal' | 'never_connected' | 'discovering' | 'pairable';
  discovered_at?: string;
}

interface Assignment {
  sensor_id: number;
  sensor_address: string;
  sensor_label: string;
  target_id: number;
  target_label: string;
  status: string;
}

export const DeviceManager: React.FC = () => {
  const [pairedDevices, setPairedDevices] = useState<Device[]>([]);
  const [discoveredDevices, setDiscoveredDevices] = useState<Device[]>([]);
  const [assignments, setAssignments] = useState<Record<string, Assignment>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveryProgress, setDiscoveryProgress] = useState(0);
  const [discoveryTimeLeft, setDiscoveryTimeLeft] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'paired' | 'discover' | 'assignments'>('paired');

  // Load paired devices on component mount
  useEffect(() => {
    loadPairedDevices();
    loadAssignments();
  }, []);

  const loadPairedDevices = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${endpointConfig.getApiUrl()}/admin/devices`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setPairedDevices(data.devices || []);
    } catch (err) {
      setError(`Failed to load devices: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAssignments = async () => {
    try {
      const response = await fetch(`${endpointConfig.getApiUrl()}/admin/devices/assignments`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setAssignments(data.assignments || {});
    } catch (err) {
      console.error('Failed to load assignments:', err);
    }
  };

  const discoverDevices = async () => {
    setIsDiscovering(true);
    setError(null);
    setDiscoveryProgress(0);
    setDiscoveryTimeLeft(45); // Updated to match actual API duration
    
    // Start progress timer - update every second for 45 seconds
    const progressInterval = setInterval(() => {
      setDiscoveryProgress(prev => {
        const newProgress = prev + (100 / 45); // Increment by ~2.22% each second
        return newProgress > 100 ? 100 : newProgress;
      });
      setDiscoveryTimeLeft(prev => {
        const newTime = prev - 1;
        return newTime < 0 ? 0 : newTime;
      });
    }, 1000);
    
    try {
      const response = await fetch(`${endpointConfig.getApiUrl()}/admin/devices/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 45 }) // Updated to match actual scan time
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      console.log('Discovery API response:', data); // Debug logging
      
      // Filter out devices that are already paired
      const pairedAddresses = new Set(pairedDevices.map(d => d.address));
      console.log('Paired addresses to filter:', Array.from(pairedAddresses)); // Debug logging
      
      const newDevices = (data.discovered_devices || []).filter(
        (device: Device) => !pairedAddresses.has(device.address)
      );
      console.log('Filtered discoverable devices:', newDevices); // Debug logging
      
      setDiscoveredDevices(newDevices);
      setActiveTab('discover');
    } catch (err) {
      setError(`Discovery failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      clearInterval(progressInterval);
      setIsDiscovering(false);
      setDiscoveryProgress(0);
      setDiscoveryTimeLeft(0);
    }
  };

  const pairDevice = async (address: string, label: string) => {
    try {
      const response = await fetch(`${endpointConfig.getApiUrl()}/admin/devices/pair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mac_address: address, label })
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const result = await response.json();
      if (result.status === 'paired') {
        // Remove from discovered devices and refresh paired devices
        setDiscoveredDevices(prev => prev.filter(d => d.address !== address));
        await loadPairedDevices();
        await loadAssignments();
      }
      return result;
    } catch (err) {
      throw new Error(`Pairing failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const removeDevice = async (sensorId: number) => {
    try {
      const response = await fetch(`${endpointConfig.getApiUrl()}/admin/devices/${sensorId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      await loadPairedDevices();
      await loadAssignments();
    } catch (err) {
      setError(`Remove failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'connected': return '🟢';
      case 'offline': return '⚫';
      case 'low_battery': return '🟡';
      case 'weak_signal': return '🟠';
      case 'never_connected': return '⚪';
      case 'pairable': return '🔵';
      default: return '❓';
    }
  };

  const getDeviceTypeIcon = (deviceType: string, vendor?: string): string => {
    // SpecialPie shot timers
    if (deviceType === 'shot_timer' || (vendor && vendor.toLowerCase().includes('specialpie'))) {
      return '⏱️';
    }
    // Standard timers (AMG)
    if (deviceType === 'timer') {
      return '⏰';
    }
    // BT50 accelerometer sensors
    if (deviceType === 'accelerometer' || deviceType === 'sensor') {
      return '📳';
    }
    // Unknown devices
    return '🔌';
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'connected': return 'Connected';
      case 'offline': return 'Offline';
      case 'low_battery': return 'Low Battery';
      case 'weak_signal': return 'Weak Signal';
      case 'never_connected': return 'Never Connected';
      case 'pairable': return 'Available to Pair';
      default: return 'Unknown';
    }
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-medium">⚠️ Device Management Error</h3>
        <p className="text-red-700 mt-1">{error}</p>
        <button
          onClick={() => { setError(null); loadPairedDevices(); }}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Discovery Button */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold">📡 Device Management</h2>
          <p className="text-gray-600 text-sm">Manage BLE sensors and device assignments</p>
        </div>
        <div className="flex flex-col items-end space-y-2">
          <button
            onClick={discoverDevices}
            disabled={isDiscovering}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center space-x-2"
          >
            {isDiscovering ? (
              <>
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                <span>Discovering... ({discoveryTimeLeft}s)</span>
              </>
            ) : (
              <>
                <span>🔍</span>
                <span>Discover Devices</span>
              </>
            )}
          </button>
          
          {isDiscovering && (
            <div className="w-48">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Scanning for BT50 & AMG devices</span>
                <span>{Math.round(discoveryProgress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${discoveryProgress}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'paired', label: `📱 Paired Devices (${pairedDevices.length})` },
            { id: 'discover', label: `🔍 Discovered (${discoveredDevices.length})` },
            { id: 'assignments', label: `🎯 Assignments (${Object.keys(assignments).length})` }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {activeTab === 'paired' && (
          <div className="space-y-4">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full"></div>
              </div>
            ) : pairedDevices.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>📱 No devices paired yet</p>
                <p className="text-sm">Use the "Discover Devices" button to find and pair sensors</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {pairedDevices.map((device) => (
                  <div key={device.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-xl">{getDeviceTypeIcon(device.type, device.vendor)}</span>
                          <h3 className="font-medium">{device.label}</h3>
                          <span className="text-xs bg-gray-100 px-2 py-1 rounded">{device.address}</span>
                          <span className="text-xs" title={getStatusText(device.status)}>
                            {getStatusIcon(device.status)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{getStatusText(device.status)}</p>
                        <div className="flex space-x-4 text-xs text-gray-500 mt-2">
                          {device.battery && <span>🔋 {device.battery}%</span>}
                          {device.rssi && <span>📶 {device.rssi} dBm</span>}
                          {device.target_name && <span>🎯 → {device.target_name}</span>}
                        </div>
                      </div>
                      <button
                        onClick={() => device.id && removeDevice(device.id)}
                        className="px-3 py-1 text-red-600 hover:bg-red-50 rounded text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'discover' && (
          <div className="space-y-4">
            {discoveredDevices.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>🔍 No devices discovered</p>
                <p className="text-sm">Click "Discover Devices" to scan for available BLE sensors</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {discoveredDevices.map((device) => (
                  <DiscoveredDeviceCard
                    key={device.address}
                    device={device}
                    onPair={pairDevice}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'assignments' && (
          <div className="space-y-4">
            {Object.keys(assignments).length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>🎯 No sensor assignments</p>
                <p className="text-sm">Pair devices and assign them to targets</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {Object.entries(assignments).map(([targetKey, assignment]) => (
                  <div key={targetKey} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="font-medium">🎯 {assignment.target_label}</h3>
                        <p className="text-sm text-gray-600">
                          📱 {assignment.sensor_label} ({assignment.sensor_address})
                        </p>
                        <span className={`inline-block px-2 py-1 rounded text-xs mt-1 ${
                          assignment.status === 'connected' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {getStatusText(assignment.status)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Component for discovered device cards
const DiscoveredDeviceCard: React.FC<{
  device: Device;
  onPair: (address: string, label: string) => Promise<any>;
}> = ({ device, onPair }) => {
  const [isPairing, setIsPairing] = useState(false);
  const [label, setLabel] = useState(device.name || `Sensor-${device.address.slice(-4)}`);

  const handlePair = async () => {
    setIsPairing(true);
    try {
      await onPair(device.address, label);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Pairing failed');
    } finally {
      setIsPairing(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="text-xl">{getDeviceTypeIcon(device.type, device.vendor)}</span>
            <h3 className="font-medium">{device.name || 'Unknown Device'}</h3>
            <span className="text-xs bg-gray-100 px-2 py-1 rounded">{device.address}</span>
            {device.pairable && <span className="text-xs">🔵</span>}
          </div>
          <div className="flex space-x-4 text-xs text-gray-500 mt-2">
            <span>📶 {device.rssi} dBm</span>
            <span>🏷️ {device.type} ({device.vendor})</span>
            {device.battery && <span>🔋 {device.battery}%</span>}
          </div>
          {device.pairable && (
            <div className="mt-3">
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="Device label"
                className="px-3 py-1 border border-gray-300 rounded text-sm mr-2"
              />
              <button
                onClick={handlePair}
                disabled={isPairing || !label.trim()}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:bg-gray-400"
              >
                {isPairing ? 'Pairing...' : 'Pair Device'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};