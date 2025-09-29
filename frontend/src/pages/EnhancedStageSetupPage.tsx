/**
 * Enhanced Stage Setup Page with Drag and Drop
 * Replaces dropdown-based assignment with intuitive drag and drop interface
 */

import { useState, useEffect } from 'react';
import { useDragAndDrop } from '../hooks/useDragAndDrop.js';
import { DevicePool } from '../components/drag-and-drop/DevicePool.js';
import { DropZone } from '../components/drag-and-drop/DropZone.js';

interface League {
  id: number;
  name: string;
  abbreviation: string;
  description: string;
}

interface Target {
  id: number;
  target_number: number;
  shape: string;
  type: string;
  category: string;
  distance_feet: number;
  offset_feet: number;
  height_feet: number;
  sensor?: {
    id: number;
    hw_addr: string;
    label: string;
    last_seen: string | null;
    battery: number | null;
    rssi: number | null;
  };
}

interface Stage {
  id: number;
  name: string;
  description: string;
  target_count: number;
  targets: Target[];
}

interface Bridge {
  id: number;
  name: string;
  hardware_id: string;
  stage_id?: number;
  stage_name?: string;
}

export const EnhancedStageSetupPage = () => {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [selectedStage, setSelectedStage] = useState<Stage | null>(null);
  const [stageDetails, setStageDetails] = useState<any>(null);
  const [bridge, setBridge] = useState<Bridge | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize drag and drop functionality
  const {
    draggedItem,
    isDragging,
    dragOverZone,
    assignments,
    initializeDropZones,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop,
    removeAssignment,
    getAssignment,
    canDropInZone,
    getAssignmentSummary
  } = useDragAndDrop();

  // Load initial data
  useEffect(() => {
    loadLeagues();
    loadBridgeConfig();
  }, []);

  // Initialize drop zones when stage is selected
  useEffect(() => {
    if (stageDetails && stageDetails.targets) {
      initializeDropZones(stageDetails.targets, true); // Include timer slot
    }
  }, [stageDetails, initializeDropZones]);

  const loadLeagues = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/leagues');
      if (response.ok) {
        const data = await response.json();
        setLeagues(data);
      } else {
        setError('Failed to load leagues');
      }
    } catch (error) {
      setError('Error loading leagues');
    } finally {
      setLoading(false);
    }
  };

  const loadBridgeConfig = async () => {
    try {
      const response = await fetch('/api/admin/bridge/config');
      if (response.ok) {
        const data = await response.json();
        setBridge(data);
      } else {
        console.error('Failed to load bridge config');
      }
    } catch (error) {
      console.error('Error loading bridge config:', error);
    }
  };

  const loadLeagueStages = async (leagueId: number) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/leagues/${leagueId}/stages`);
      if (response.ok) {
        const data = await response.json();
        setStages(data);
      } else {
        setError('Failed to load stages');
      }
    } catch (error) {
      setError('Error loading stages');
    } finally {
      setLoading(false);
    }
  };

  const loadStageDetails = async (stageId: number) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/admin/stages/${stageId}/details`);
      if (response.ok) {
        const data = await response.json();
        setStageDetails(data);
      } else {
        setError('Failed to load stage details');
      }
    } catch (error) {
      setError('Error loading stage details');
    } finally {
      setLoading(false);
    }
  };

  // Handle drag over events
  const handleZoneDragOver = (e: DragEvent, zoneId: string) => {
    e.preventDefault();
    if (draggedItem) {
      const canDrop = handleDragOver(zoneId, draggedItem.type);
      e.dataTransfer!.dropEffect = canDrop ? 'move' : 'none';
    }
  };

  const handleZoneDragLeave = (e: DragEvent) => {
    e.preventDefault();
    // Could add visual feedback here if needed
  };

  // Handle device assignment via API
  const assignDeviceToTarget = async (assignment: any) => {
    try {
      // Determine the correct API endpoint and payload based on assignment type
      if (assignment.targetAssignment === 'timer') {
        // Assign timer device - this would need the specific API endpoint
        console.log('Assigning timer device:', assignment);
        // TODO: Implement timer assignment API call
      } else {
        // Assign sensor to target
        const targetId = assignment.targetId;
        const sensorAddress = assignment.deviceAddress;
        
        const response = await fetch(`/api/admin/targets/${targetId}/assign-sensor`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sensor_address: sensorAddress,
            sensor_id: assignment.deviceId // If available
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          setError(`Failed to assign sensor: ${errorData.detail || 'Unknown error'}`);
          return false;
        }

        // Refresh stage details to show updated assignments
        if (selectedStage) {
          await loadStageDetails(selectedStage.id);
        }
      }

      return true;
    } catch (error) {
      console.error('Error assigning device:', error);
      setError('Error assigning device');
      return false;
    }
  };

  // Handle drop events
  const handleZoneDrop = async (e: DragEvent, zoneId: string) => {
    e.preventDefault();
    const success = await handleDrop(zoneId, assignDeviceToTarget);
    if (!success) {
      setError('Failed to assign device to target');
    }
  };

  // Handle assignment removal
  const handleRemoveAssignment = (zoneId: string) => {
    removeAssignment(zoneId);
    // TODO: Also call API to remove assignment from backend
  };

  // Render stage layout with drop zones
  const renderEnhancedStageLayout = () => {
    if (!stageDetails || !stageDetails.targets) {
      return null;
    }

    return (
      <div className="space-y-6">
        {/* Timer Drop Zone */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="text-lg font-semibold mb-4 text-yellow-800">⏱️ Timer Device</h4>
          <DropZone
            id="timer-slot"
            type="timer"
            assignment={getAssignment('timer-slot')}
            canAcceptDrop={canDropInZone('timer-slot')}
            isDragOver={dragOverZone === 'timer-slot'}
            onDragOver={(e) => handleZoneDragOver(e, 'timer-slot')}
            onDragLeave={handleZoneDragLeave}
            onDrop={(e) => handleZoneDrop(e, 'timer-slot')}
            onRemoveAssignment={() => handleRemoveAssignment('timer-slot')}
          />
        </div>

        {/* Targets Grid */}
        <div>
          <h4 className="text-lg font-semibold mb-4 text-gray-800">🎯 Stage Targets</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {stageDetails.targets.map((target: Target) => {
              const zoneId = `target-${target.id}`;
              return (
                <div key={target.id} className="space-y-2">
                  {/* Target Info Header */}
                  <div className="text-sm text-gray-600">
                    <div className="font-semibold">Target {target.target_number}</div>
                    <div>{target.shape} • {target.distance_feet}ft</div>
                    <div className="text-xs">
                      <span className={`px-2 py-1 rounded ${
                        target.category === 'Stop' ? 'bg-red-100 text-red-800' :
                        target.category === 'Penalty' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {target.category}
                      </span>
                    </div>
                  </div>
                  
                  {/* Drop Zone */}
                  <DropZone
                    id={zoneId}
                    type="target"
                    targetNumber={target.target_number}
                    targetInfo={{
                      shape: target.shape,
                      type: target.type,
                      category: target.category,
                      distance_feet: target.distance_feet,
                      height_feet: target.height_feet
                    }}
                    assignment={getAssignment(zoneId)}
                    canAcceptDrop={canDropInZone(zoneId)}
                    isDragOver={dragOverZone === zoneId}
                    onDragOver={(e) => handleZoneDragOver(e, zoneId)}
                    onDragLeave={handleZoneDragLeave}
                    onDrop={(e) => handleZoneDrop(e, zoneId)}
                    onRemoveAssignment={() => handleRemoveAssignment(zoneId)}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const summary = getAssignmentSummary();

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🎯 Enhanced Stage Setup
          </h1>
          <p className="text-gray-600">
            Configure stages and assign devices using drag and drop
          </p>
        </div>
        {bridge && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm font-semibold text-blue-900">
              🌉 {bridge.name}
            </div>
            {bridge.stage_name && (
              <div className="text-xs text-blue-700 mt-1">
                Assigned to: {bridge.stage_name}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
          <button 
            onClick={() => setError(null)}
            className="ml-4 text-red-600 hover:text-red-800"
          >
            ✕
          </button>
        </div>
      )}

      {/* Stage Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Stage Selection</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              League
            </label>
            <select
              value={selectedLeague?.id || ''}
              onChange={(e) => {
                const league = leagues.find(l => l.id === parseInt(e.target.value));
                setSelectedLeague(league || null);
                setSelectedStage(null);
                setStageDetails(null);
                if (league) {
                  loadLeagueStages(league.id);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select League...</option>
              {leagues.map(league => (
                <option key={league.id} value={league.id}>
                  {league.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Stage
            </label>
            <select
              value={selectedStage?.id || ''}
              onChange={(e) => {
                const stage = stages.find(s => s.id === parseInt(e.target.value));
                setSelectedStage(stage || null);
                if (stage) {
                  loadStageDetails(stage.id);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              disabled={!selectedLeague}
            >
              <option value="">Select Stage...</option>
              {stages.map(stage => (
                <option key={stage.id} value={stage.id}>
                  {stage.name} ({stage.target_count} targets)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Assignment Summary */}
        {stageDetails && (
          <div className="mt-4 flex items-center space-x-6 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${summary.timerAssigned ? 'bg-green-500' : 'bg-gray-300'}`}></span>
              <span>Timer: {summary.timerAssigned ? 'Assigned' : 'Not assigned'}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${summary.sensorCount > 0 ? 'bg-green-500' : 'bg-gray-300'}`}></span>
              <span>Sensors: {summary.sensorCount} assigned</span>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              summary.isComplete ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {summary.isComplete ? '✅ Setup Complete' : '⏳ Setup In Progress'}
            </div>
          </div>
        )}
      </div>

      {/* Device Pool */}
      <DevicePool
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        draggedItem={draggedItem}
        isDragging={isDragging}
      />

      {/* Stage Layout with Drop Zones */}
      {stageDetails && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">
              {stageDetails.league?.name} - {stageDetails.name}
            </h2>
            <div className="text-sm text-gray-600">
              {stageDetails.target_count} targets • {stageDetails.description}
            </div>
          </div>

          {renderEnhancedStageLayout()}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}
    </div>
  );
};