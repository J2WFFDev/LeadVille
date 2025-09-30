/**
 * Settings and configuration page
 */

import React, { useState } from 'react';
import { NetworkManager } from '../components/NetworkManager';
import { DeviceManager } from '../components/DeviceManager';
import { BridgeManager } from '../components/BridgeManager';
import { DeviceAssignment } from '../components/DeviceAssignment';

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'network' | 'system' | 'devices' | 'bridge' | 'assignment'>('network');
  const [isRestarting, setIsRestarting] = useState(false);

  const handleRestartService = async () => {
    setIsRestarting(true);
    try {
      const response = await fetch('/api/admin/services/restart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        try {
          await response.json();
          console.log('Bridge service restart initiated successfully');
        } catch (jsonError) {
          // JSON parsing failed, but response was OK - restart probably succeeded
          console.log('Bridge service restart initiated (response parsing issue, but restart likely succeeded)');
        }
        
        // Reset the button state after a delay
        setTimeout(() => {
          setIsRestarting(false);
        }, 5000);
      } else {
        try {
          const error = await response.json();
          console.error(`Failed to restart service: ${error.error || 'Unknown error'}`);
        } catch (jsonError) {
          console.error(`Failed to restart service: HTTP ${response.status}`);
        }
        setIsRestarting(false);
      }
    } catch (error) {
      console.error(`Network error: ${error}`);
      setIsRestarting(false);
    }
  };
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
          ⚙️ System Settings
        </h1>
        <p className="text-gray-600">
          Network, device, and system configuration
        </p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {[
              { id: 'network', label: '🌐 Network', icon: '🌐' },
              { id: 'devices', label: '📡 Devices', icon: '📡' },
              { id: 'bridge', label: '🌉 Bridge', icon: '🌉' },
              { id: 'assignment', label: '🎯 Device Assignment', icon: '🎯' },
              { id: 'system', label: '⚙️ System', icon: '⚙️' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'network' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Network Configuration</h2>
              <NetworkManager />
            </div>
          )}

          {activeTab === 'devices' && (
            <DeviceManager />
          )}

          {activeTab === 'bridge' && (
            <BridgeManager />
          )}

          {activeTab === 'assignment' && (
            <DeviceAssignment />
          )}

          {activeTab === 'system' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">System Information</h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* System Information */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium mb-3">📋 System Information</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Version:</span>
                      <span className="font-mono">2.0.0</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Build:</span>
                      <span className="font-mono">Production</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Platform:</span>
                      <span className="font-mono">React + Vite + TypeScript</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Backend:</span>
                      <span className="font-mono">FastAPI + WebSocket</span>
                    </div>
                  </div>
                </div>

                {/* WebSocket Configuration */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium mb-3">🔌 WebSocket Configuration</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        WebSocket URL
                      </label>
                      <input
                        type="text"
                        defaultValue="ws://pitts:8001"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                        readOnly
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Reconnect Interval (ms)
                      </label>
                      <input
                        type="number"
                        defaultValue="3000"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        readOnly
                      />
                    </div>
                  </div>
                </div>

                {/* System Actions */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium mb-3">🔧 System Actions</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Bridge Service Control
                      </label>
                      <p className="text-sm text-gray-600 mb-3">
                        Restart the core BLE bridge service that handles sensor communication. 
                        This will reset all device connections and timing calibrations.
                      </p>
                      <button
                        onClick={handleRestartService}
                        disabled={isRestarting}
                        style={{
                          backgroundColor: isRestarting ? '#d1d5db' : '#f97316',
                          color: 'white',
                          padding: '8px 16px',
                          borderRadius: '6px',
                          border: 'none',
                          fontWeight: '600',
                          fontSize: '14px',
                          cursor: isRestarting ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}
                      >
                        {isRestarting ? (
                          <>⏳ Restarting...</>
                        ) : (
                          <>🔄 Restart Bridge Service</>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium">
          Save Settings
        </button>
        <button className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 font-medium">
          Reset to Defaults
        </button>
      </div>
    </div>
  );
};