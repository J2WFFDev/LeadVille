/**
 * Device Pool Component
 * Shows available sensors and timers that can be dragged to targets
 */

import { useState, useEffect } from 'react';
import { DraggableDevice } from './DraggableDevice.js';
import type { DeviceItem } from '../../hooks/useDragAndDrop.js';

interface DevicePoolProps {
  onDragStart: (device: DeviceItem) => void;
  onDragEnd: () => void;
  draggedItem: DeviceItem | null;
  isDragging: boolean;
}

interface DiscoveredDevice {
  address: string;
  name: string;
  type: string;
  device_type?: string;
  rssi?: number;
  vendor?: string;
}

interface PoolDevice {
  id: number;
  hw_addr: string;
  label: string;
  device_type: string;
  last_seen: string | null;
  battery: number | null;
  rssi: number | null;
}

export const DevicePool = ({
  onDragStart,
  onDragEnd,
  draggedItem,
  isDragging
}: DevicePoolProps) => {
  const [discoveredDevices, setDiscoveredDevices] = useState<DiscoveredDevice[]>([]);
  const [poolDevices, setPoolDevices] = useState<PoolDevice[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveryStatus, setDiscoveryStatus] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Load pool devices on mount
  useEffect(() => {
    loadPoolDevices();
  }, []);

  const loadPoolDevices = async () => {
    try {
      const response = await fetch('/api/admin/pool/devices');
      if (response.ok) {
        const devices = await response.json();
        setPoolDevices(devices);
      } else {
        console.error('Failed to load pool devices');
      }
    } catch (error) {
      console.error('Error loading pool devices:', error);
    }
  };

  const startDeviceDiscovery = async () => {
    setIsDiscovering(true);
    setDiscoveryStatus('Starting device discovery...');
    setError(null);
    setDiscoveredDevices([]);

    try {
      // Try WebSocket discovery first
      const wsUrl = `ws://${window.location.hostname}:8001/ws/device-discovery`;
      const ws = new WebSocket(wsUrl);
      let discoveryTimeout: number;

      ws.onopen = () => {
        setDiscoveryStatus('Scanning for devices...');
        ws.send(JSON.stringify({ action: 'start_discovery', duration: 10 }));
        
        // Set a timeout for discovery
        discoveryTimeout = setTimeout(() => {
          ws.close();
          setIsDiscovering(false);
          setDiscoveryStatus(`Discovery complete. Found ${discoveredDevices.length} devices.`);
        }, 12000);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'device_discovered') {
          const device = data.device;
          setDiscoveredDevices((prev: DiscoveredDevice[]) => {
            // Avoid duplicates
            const exists = prev.some((d: DiscoveredDevice) => d.address === device.address);
            if (!exists) {
              return [...prev, device];
            }
            return prev;
          });
          setDiscoveryStatus(`Found ${discoveredDevices.length + 1} devices...`);
        } else if (data.type === 'discovery_complete') {
          clearTimeout(discoveryTimeout);
          setIsDiscovering(false);
          setDiscoveryStatus(`Discovery complete. Found ${discoveredDevices.length} devices.`);
          ws.close();
        }
      };

      ws.onerror = () => {
        clearTimeout(discoveryTimeout);
        setError('WebSocket connection failed - falling back to standard discovery');
        ws.close();
        fallbackDiscovery();
      };

      ws.onclose = () => {
        clearTimeout(discoveryTimeout);
        setIsDiscovering(false);
      };

    } catch (error) {
      setError('WebSocket not supported - using standard discovery');
      fallbackDiscovery();
    }
  };

  const fallbackDiscovery = async () => {
    try {
      setDiscoveryStatus('Using standard discovery method...');
      const response = await fetch('/api/admin/devices/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 10 })
      });

      if (response.ok) {
        const data = await response.json();
        setDiscoveredDevices(data.discovered_devices || []);
        setDiscoveryStatus(`Discovery complete. Found ${data.discovered_devices?.length || 0} devices.`);
      } else {
        setError('Discovery failed');
      }
    } catch (error) {
      setError('Error during discovery');
    } finally {
      setIsDiscovering(false);
    }
  };

  // Convert devices to common format
  const normalizeDevice = (device: DiscoveredDevice | PoolDevice): DeviceItem => {
    if ('id' in device) {
      // Pool device
      return {
        id: device.id,
        address: device.hw_addr,
        hw_addr: device.hw_addr,
        name: device.label,
        label: device.label,
        type: device.device_type === 'timer' ? 'timer' : 'accelerometer',
        device_type: device.device_type,
        rssi: device.rssi || undefined,
        battery: device.battery || undefined,
        isPoolDevice: true
      };
    } else {
      // Discovered device
      return {
        address: device.address,
        name: device.name,
        type: device.type === 'timer' ? 'timer' : 'accelerometer',
        device_type: device.device_type || device.type,
        rssi: device.rssi,
        isPoolDevice: false
      };
    }
  };

  // Combine and normalize all devices
  const allDevices = [
    ...poolDevices.map(normalizeDevice),
    ...discoveredDevices.map(normalizeDevice)
  ];

  // Remove duplicates by address
  const uniqueDevices = allDevices.filter((device, index, arr) => 
    arr.findIndex(d => d.address === device.address) === index
  );

  const handleRefreshPool = () => {
    loadPoolDevices();
  };

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Device Pool</h2>
            <p className="text-sm text-gray-600">
              Drag devices to assign them to targets
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRefreshPool}
              className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
              title="Refresh pool devices"
            >
              🔄 Refresh Pool
            </button>
            
            <button
              onClick={startDeviceDiscovery}
              disabled={isDiscovering}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                isDiscovering
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isDiscovering ? '🔍 Discovering...' : '🔍 Discover Devices'}
            </button>
          </div>
        </div>

        {/* Discovery Status */}
        {discoveryStatus && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">{discoveryStatus}</p>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Device Count Summary */}
        <div className="mb-4 flex items-center space-x-4 text-sm text-gray-600">
          <span>Pool Devices: {poolDevices.length}</span>
          <span>Discovered: {discoveredDevices.length}</span>
          <span>Total Available: {uniqueDevices.length}</span>
        </div>

        {/* Devices Grid */}
        {uniqueDevices.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {uniqueDevices.map((device, index) => (
              <DraggableDevice
                key={`${device.address}-${index}`}
                device={device}
                onDragStart={onDragStart}
                onDragEnd={onDragEnd}
                isDragging={isDragging}
                isBeingDragged={draggedItem?.address === device.address}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <span className="text-4xl">📱</span>
            <p className="mt-2 text-lg font-medium">No devices available</p>
            <p className="text-sm">Click "Discover Devices" to find nearby sensors and timers</p>
          </div>
        )}
        
        {/* Discovery Progress */}
        {isDiscovering && (
          <div className="mt-4 text-center">
            <div className="inline-flex items-center space-x-2 text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span className="text-sm">Scanning for devices...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};