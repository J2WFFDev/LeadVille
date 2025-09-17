/**
 * Sensor Assignment Component
 * Manages assignment of sensors to targets
 */

import React from 'react';

interface Target {
  target_number: number;
  shape: string;
  type: string;
  category: string;
  distance: number;
  offset: number;
  height: number;
}

interface StageConfiguration {
  league: string;
  stage_name: string;
  targets: Target[];
}

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

interface SensorAssignmentProps {
  stageConfig: StageConfiguration;
  connectedDevices: ConnectedDevice[];
  sensorAssignments: Record<string, SensorAssignment>;
  onAssignmentChange: (targetId: string, sensorAddress: string) => void;
  isLoading: boolean;
}

export const SensorAssignment: React.FC<SensorAssignmentProps> = ({
  stageConfig,
  connectedDevices,
  sensorAssignments,
  onAssignmentChange,
  isLoading
}) => {
  // Get assignment for a target
  const getAssignmentForTarget = (targetId: string): string => {
    return sensorAssignments[targetId]?.sensorAddress || '';
  };

  // Check if sensor is already assigned
  const isSensorAssigned = (sensorAddress: string): boolean => {
    return Object.values(sensorAssignments).some(
      (assignment) => assignment.sensorAddress === sensorAddress
    );
  };

  // Get sensor status icon
  const getSensorStatusIcon = (device: ConnectedDevice): string => {
    switch (device.status) {
      case 'connected': return '🟢';
      case 'low-battery': return '🟡';
      case 'error': return '🔴';
      case 'disconnected': return '⚫';
      default: return '❓';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Connected Devices Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">
          Connected Sensors ({connectedDevices.length})
        </h3>
        <div className="grid grid-cols-1 gap-2">
          {connectedDevices.map((device) => (
            <div
              key={device.address}
              className={`flex items-center justify-between p-2 rounded ${
                isSensorAssigned(device.address) 
                  ? 'bg-blue-100 border border-blue-200' 
                  : 'bg-white border border-gray-200'
              }`}
            >
              <div className="flex items-center space-x-2">
                <span>{getSensorStatusIcon(device)}</span>
                <span className="text-sm font-medium">{device.name}</span>
              </div>
              <div className="text-xs text-gray-500">
                {device.batteryLevel && `${device.batteryLevel}%`}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Target Assignments */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-700">
          Target Assignments
        </h3>
        
        {stageConfig.targets
          .sort((a, b) => a.target_number - b.target_number)
          .map((target) => {
            const targetId = `P${target.target_number}`;
            const currentAssignment = getAssignmentForTarget(targetId);
            
            return (
              <div
                key={target.target_number}
                className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">
                      {targetId}
                    </span>
                    <span className="text-xs text-gray-500">
                      {target.type} - {target.distance}ft
                    </span>
                  </div>
                </div>
                
                <div className="flex-1 max-w-xs">
                  <select
                    value={currentAssignment}
                    onChange={(e) => onAssignmentChange(targetId, e.target.value)}
                    className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select sensor...</option>
                    {connectedDevices.map((device) => (
                      <option
                        key={device.address}
                        value={device.address}
                        disabled={isSensorAssigned(device.address) && currentAssignment !== device.address}
                      >
                        {getSensorStatusIcon(device)} {device.name}
                        {device.batteryLevel && ` (${device.batteryLevel}%)`}
                      </option>
                    ))}
                  </select>
                </div>
                
                {currentAssignment && (
                  <button
                    onClick={() => onAssignmentChange(targetId, '')}
                    className="ml-2 p-1 text-red-600 hover:text-red-800"
                    title="Remove assignment"
                  >
                    ✕
                  </button>
                )}
              </div>
            );
          })}
      </div>

      {/* Auto-assign button */}
      <div className="pt-4 border-t border-gray-200">
        <button
          onClick={() => {
            // Auto-assign sensors to targets
            let availableSensors = connectedDevices
              .filter(device => device.status === 'connected')
              .map(device => device.address);
            
            stageConfig.targets.forEach((target, index) => {
              const targetId = `P${target.target_number}`;
              if (availableSensors[index] && !getAssignmentForTarget(targetId)) {
                onAssignmentChange(targetId, availableSensors[index]);
              }
            });
          }}
          disabled={connectedDevices.filter(d => d.status === 'connected').length === 0}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          Auto-Assign Available Sensors
        </button>
      </div>
    </div>
  );
};