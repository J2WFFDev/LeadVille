/**
 * Network Management Component
 * Handles WiFi/AP mode switching with real-time status updates
 */

import React, { useState, useEffect } from 'react';

interface NetworkStatus {
  mode: 'online' | 'offline' | 'unknown';
  ssid: string | null;
  ip_addresses: string[];
  connected_clients: number;
  interfaces: Record<string, any>;
}

interface NetworkManagerProps {
  onStatusChange?: (status: NetworkStatus) => void;
}

export const NetworkManager: React.FC<NetworkManagerProps> = ({ onStatusChange }) => {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [switchingMode, setSwitchingMode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // WiFi connection form state
  const [showWiFiForm, setShowWiFiForm] = useState(false);
  const [wifiSSID, setWifiSSID] = useState('');
  const [wifiPassword, setWifiPassword] = useState('');
  
  // Fetch network status
  const fetchNetworkStatus = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://192.168.1.124:8001/api/admin/network');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const status = await response.json();
      setNetworkStatus(status);
      onStatusChange?.(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch network status');
      console.error('Network status fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Switch to offline mode (AP mode)
  const switchToOfflineMode = async () => {
    setSwitchingMode(true);
    setError(null);
    
    try {
      const response = await fetch('http://192.168.1.124:8001/api/admin/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mode: 'offline'
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Wait a moment for the switch to complete
      setTimeout(() => {
        fetchNetworkStatus();
        setSwitchingMode(false);
      }, 3000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch to offline mode');
      setSwitchingMode(false);
    }
  };

  // Switch to online mode (join WiFi)
  const switchToOnlineMode = async () => {
    if (!wifiSSID || !wifiPassword) {
      setError('Please enter both SSID and password');
      return;
    }
    
    setSwitchingMode(true);
    setError(null);
    
    try {
      const response = await fetch('http://192.168.1.124:8001/api/admin/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },  
        body: JSON.stringify({
          mode: 'online',
          ssid: wifiSSID,
          password: wifiPassword
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Wait for connection to establish
      setTimeout(() => {
        fetchNetworkStatus();
        setSwitchingMode(false);
        setShowWiFiForm(false);
        setWifiSSID('');
        setWifiPassword('');
      }, 5000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch to online mode');
      setSwitchingMode(false);
    }
  };

  // Get status indicator color
  const getStatusColor = () => {
    if (!networkStatus) return 'bg-gray-400';
    switch (networkStatus.mode) {
      case 'online': return 'bg-green-500';
      case 'offline': return 'bg-blue-500';
      default: return 'bg-yellow-500';
    }
  };

  // Get mode description
  const getModeDescription = () => {
    if (!networkStatus) return 'Unknown';
    switch (networkStatus.mode) {
      case 'online':
        return `Connected to ${networkStatus.ssid || 'WiFi'}`;
      case 'offline':
        return 'Access Point Mode (LeadVille-Bridge)';
      default:
        return 'Network status unknown';
    }
  };

  // Auto-refresh status every 10 seconds
  useEffect(() => {
    fetchNetworkStatus();
    
    const interval = setInterval(fetchNetworkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (  
    <div className="space-y-6">
      {/* Current Status */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Network Status</h3>
          <button
            onClick={fetchNetworkStatus}
            disabled={isLoading}
            className={`px-3 py-1 rounded text-sm ${
              isLoading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {isLoading ? '⟳ Refreshing...' : '🔄 Refresh'}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded-md">
            <p className="text-red-700 text-sm">⚠️ {error}</p>
          </div>
        )}

        {networkStatus ? (
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
              <span className="font-medium">{getModeDescription()}</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Mode:</span>
                <span className="ml-2 font-medium capitalize">{networkStatus.mode}</span>
              </div>
              
              {networkStatus.ip_addresses.length > 0 && (
                <div>
                  <span className="text-gray-600">IP Address:</span>
                  <span className="ml-2 font-mono">{networkStatus.ip_addresses[0]}</span>
                </div>
              )}
              
              {networkStatus.mode === 'offline' && (
                <div>
                  <span className="text-gray-600">Connected Clients:</span>
                  <span className="ml-2 font-medium">{networkStatus.connected_clients}</span>
                </div>
              )}
              
              {networkStatus.ssid && (
                <div>
                  <span className="text-gray-600">SSID:</span>
                  <span className="ml-2 font-medium">{networkStatus.ssid}</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            {isLoading ? '⟳ Loading network status...' : 'No network status available'}
          </div>
        )}
      </div>

      {/* Mode Switching */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Network Mode</h3>
        
        {switchingMode && (
          <div className="mb-4 p-3 bg-blue-100 border border-blue-300 rounded-md">
            <p className="text-blue-700 text-sm">🔄 Switching network mode... Please wait</p>
          </div>
        )}

        <div className="space-y-4">
          {/* Offline Mode Button */}
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h4 className="font-medium">🏗️ Offline Mode (Access Point)</h4>
              <p className="text-sm text-gray-600">
                Creates "LeadVille-Bridge" WiFi network for field use
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Network: LeadVille-Bridge • Password: leadville2024 • IP: 192.168.4.1
              </p>
            </div>
            <button
              onClick={switchToOfflineMode}
              disabled={switchingMode || networkStatus?.mode === 'offline'}
              className={`px-4 py-2 rounded font-medium ${
                networkStatus?.mode === 'offline'
                  ? 'bg-blue-100 text-blue-700 cursor-not-allowed'
                  : switchingMode
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {networkStatus?.mode === 'offline' ? '✓ Active' : 'Activate'}
            </button>
          </div>

          {/* Online Mode Section */}
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-medium">🌐 Online Mode (Join WiFi)</h4>
                <p className="text-sm text-gray-600">
                  Connect to existing WiFi network
                </p>
              </div>
              <button
                onClick={() => setShowWiFiForm(!showWiFiForm)}
                disabled={switchingMode}
                className={`px-4 py-2 rounded font-medium ${
                  networkStatus?.mode === 'online'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-green-500 text-white hover:bg-green-600'
                }`}
              >
                {networkStatus?.mode === 'online' ? '✓ Connected' : 'Connect'}
              </button>
            </div>

            {/* WiFi Connection Form */}
            {showWiFiForm && (
              <div className="mt-4 space-y-3 p-3 bg-gray-50 rounded">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    WiFi Network (SSID)
                  </label>
                  <input
                    type="text"
                    value={wifiSSID}
                    onChange={(e) => setWifiSSID(e.target.value)}
                    placeholder="Enter WiFi name"
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    value={wifiPassword}
                    onChange={(e) => setWifiPassword(e.target.value)}
                    placeholder="Enter WiFi password"
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={switchToOnlineMode}
                    disabled={switchingMode || !wifiSSID || !wifiPassword}
                    className={`px-4 py-2 rounded font-medium ${
                      switchingMode || !wifiSSID || !wifiPassword
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-green-500 text-white hover:bg-green-600'
                    }`}
                  >
                    {switchingMode ? '⟳ Connecting...' : '🔗 Connect'}
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowWiFiForm(false);
                      setWifiSSID('');
                      setWifiPassword('');
                      setError(null);
                    }}
                    className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Network Information */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">Connection Information</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium mb-2">🏗️ Offline Mode Details</h4>
            <div className="text-sm space-y-1">
              <div><span className="text-gray-600">SSID:</span> <code>LeadVille-Bridge</code></div>
              <div><span className="text-gray-600">Password:</span> <code>leadville2024</code></div>
              <div><span className="text-gray-600">IP Range:</span> <code>192.168.4.1/24</code></div>
              <div><span className="text-gray-600">Portal:</span> <code>http://bridge.local</code></div>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium mb-2">🌐 Access URLs</h4>
            <div className="text-sm space-y-1">
              <div><span className="text-gray-600">Frontend:</span> <code>http://192.168.1.124:5175</code></div>
              <div><span className="text-gray-600">API:</span> <code>http://192.168.1.124:8001/api</code></div>
              <div><span className="text-gray-600">WebSocket:</span> <code>ws://192.168.1.124:8001/ws</code></div>
              <div><span className="text-gray-600">Console:</span> <code>http://192.168.1.124:5175/console</code></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};