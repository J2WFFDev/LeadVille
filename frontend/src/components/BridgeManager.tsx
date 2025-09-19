/**
 * Bridge configuration and management component
 */

import React, { useState, useEffect } from 'react';

interface Bridge {
  id: number;
  name: string;
  bridge_id: string;
  current_stage_id?: number;
  current_stage_name?: string;
}

interface Stage {
  id: number;
  name: string;
  stage_number: number;
}

export const BridgeManager: React.FC = () => {
  const [bridge, setBridge] = useState<Bridge | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editName, setEditName] = useState('');
  const [editBridgeId, setEditBridgeId] = useState('');
  const [selectedStageId, setSelectedStageId] = useState<number | ''>('');

  // Load Bridge configuration
  useEffect(() => {
    loadBridgeConfig();
    loadStages();
  }, []);

  const loadBridgeConfig = async () => {
    try {
      const response = await fetch('/api/admin/bridge');
      if (response.ok) {
        const data = await response.json();
        const bridgeData = data.bridge || data; // Handle both formats
        setBridge(bridgeData);
        setEditName(bridgeData.name || '');
        setEditBridgeId(bridgeData.bridge_id || '');
        setSelectedStageId(bridgeData.current_stage_id || '');
      } else {
        console.error('Failed to load Bridge configuration');
      }
    } catch (error) {
      console.error('Error loading Bridge configuration:', error);
    }
  };

  const loadStages = async () => {
    try {
      const response = await fetch('/api/admin/leagues/1/stages'); // SASP league
      if (response.ok) {
        const data = await response.json();
        setStages(data.stages || data);
      }
    } catch (error) {
      console.error('Error loading stages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveBridge = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/admin/bridge', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: editName,
          bridge_id: editBridgeId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const updatedBridge = data.bridge || data; // Handle both formats
        setBridge(updatedBridge);
        alert('Bridge configuration saved successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to save Bridge configuration: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Network error: ${error}`);
    } finally {
      setSaving(false);
    }
  };

  const handleAssignStage = async () => {
    if (!selectedStageId) {
      alert('Please select a stage to assign');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch('/api/admin/bridge/assign_stage', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          stage_id: selectedStageId,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        loadBridgeConfig(); // Reload to get updated stage assignment
      } else {
        const error = await response.json();
        alert(`Failed to assign stage: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Network error: ${error}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">Loading Bridge configuration...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-4">🌉 Bridge Configuration</h2>
        <p className="text-gray-600 mb-6">
          Configure this Bridge's identity and stage assignment for multi-Bridge deployments.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bridge Identity */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="font-medium text-lg mb-4">🏷️ Bridge Identity</h3>
          
          {bridge && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bridge Name
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter Bridge name (e.g., 'Match Director', 'Stage 1 Bridge')"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Friendly name to identify this Bridge in multi-Bridge setups
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bridge ID
                </label>
                <input
                  type="text"
                  value={editBridgeId}
                  onChange={(e) => setEditBridgeId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                  placeholder="Enter unique bridge identifier"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Unique identifier for this Bridge (MAC address, serial number, etc.)
                </p>
              </div>

              <div className="pt-2">
                <button
                  onClick={handleSaveBridge}
                  disabled={saving || !editName.trim() || !editBridgeId.trim()}
                  className={`px-4 py-2 rounded-lg font-medium ${
                    saving || !editName.trim() || !editBridgeId.trim()
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-500 text-white hover:bg-blue-600'
                  }`}
                >
                  {saving ? 'Saving...' : 'Save Identity'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Stage Assignment */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="font-medium text-lg mb-4">🏟️ Stage Assignment</h3>
          
          <div className="space-y-4">
            {bridge?.current_stage_name && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <span className="text-green-600 text-xl mr-3">✅</span>
                  <div>
                    <div className="font-medium text-green-800">Currently Assigned:</div>
                    <div className="text-green-700">{bridge.current_stage_name}</div>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assign to Stage
              </label>
              <select
                value={selectedStageId}
                onChange={(e) => setSelectedStageId(e.target.value ? parseInt(e.target.value) : '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select a stage...</option>
                {stages.map((stage) => (
                  <option key={stage.id} value={stage.id}>
                    Stage {stage.stage_number}: {stage.name}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                This Bridge will only manage sensors assigned to the selected stage
              </p>
            </div>

            <div className="pt-2">
              <button
                onClick={handleAssignStage}
                disabled={saving || !selectedStageId}
                className={`px-4 py-2 rounded-lg font-medium ${
                  saving || !selectedStageId
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-500 text-white hover:bg-green-600'
                }`}
              >
                {saving ? 'Assigning...' : 'Assign Stage'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Current Configuration Summary */}
      {bridge && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-medium text-lg mb-4">📋 Current Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm font-medium text-gray-700">Bridge Name</div>
              <div className="text-lg text-gray-900">{bridge.name || 'Not set'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700">Bridge ID</div>
              <div className="text-lg font-mono text-gray-900">{bridge.bridge_id || 'Not set'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700">Assigned Stage</div>
              <div className="text-lg text-gray-900">{bridge.current_stage_name || 'Not assigned'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <span className="text-yellow-600 text-xl mr-3">💡</span>
          <div className="text-sm text-yellow-800">
            <div className="font-medium mb-2">Bridge-Centric Architecture</div>
            <ul className="space-y-1 list-disc list-inside">
              <li>Each Bridge manages sensors exclusively assigned to its stage</li>
              <li>BLE sensors only connect to their assigned Bridge, preventing conflicts</li>
              <li>Stage assignment determines which sensors this Bridge will discover and connect to</li>
              <li>Multiple Bridges can operate independently on different stages</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};