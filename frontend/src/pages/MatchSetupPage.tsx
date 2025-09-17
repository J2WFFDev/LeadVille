/**
 * Match Setup Page - React implementation
 * Replaces vanilla JS DeviceAdmin Match Setup functionality
 */

import React, { useState } from 'react';
import { StageSelector } from '../components/match-setup/StageSelector';
import { StageLayout } from '../components/match-setup/StageLayout';
import { SensorAssignment } from '../components/match-setup/SensorAssignment';
import { useStageConfig } from '../hooks/useStageConfig';
import { useSensorData } from '../hooks/useSensorData';



export const MatchSetupPage: React.FC = () => {
  const [selectedStage, setSelectedStage] = useState<string>('');
  const [selectedLeague, setSelectedLeague] = useState<string>('');
  
  // Custom hooks for data management
  const { 
    stageConfigurations, 
    currentStageConfig, 
    isLoading: stageLoading,
    loadStageConfig
  } = useStageConfig();
  
  const { 
    connectedDevices, 
    sensorAssignments,
    updateSensorAssignment,
    isLoading: sensorLoading
  } = useSensorData();

  // Handle stage selection
  const handleStageChange = async (league: string, stage: string) => {
    setSelectedLeague(league);
    setSelectedStage(stage);
    await loadStageConfig(league, stage);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 p-4">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Match Setup
        </h1>
        <p className="text-gray-600">
          Configure stages, assign sensors to targets, and manage match parameters
        </p>
      </div>

      {/* Stage Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Stage Selection</h2>
        <StageSelector
          stageConfigurations={stageConfigurations}
          selectedLeague={selectedLeague}
          selectedStage={selectedStage}
          onStageChange={handleStageChange}
          isLoading={stageLoading}
        />
      </div>

      {/* Main Content Area */}
      {currentStageConfig && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          
          {/* Stage Layout - Takes up 2 columns on XL screens */}
          <div className="xl:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">
                Stage Layout - {currentStageConfig.league} {currentStageConfig.stage_name}
              </h2>
              <StageLayout
                stageConfig={currentStageConfig}
                sensorAssignments={sensorAssignments}
                connectedDevices={connectedDevices}
              />
            </div>
          </div>

          {/* Sensor Assignment Panel */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Sensor Assignment</h2>
              <SensorAssignment
                stageConfig={currentStageConfig}
                connectedDevices={connectedDevices}
                sensorAssignments={sensorAssignments}
                onAssignmentChange={updateSensorAssignment}
                isLoading={sensorLoading}
              />
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                  Start Match
                </button>
                <button className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
                  Test All Sensors
                </button>
                <button className="w-full px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors">
                  Calibrate Targets
                </button>
                <button className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors">
                  Reset Stage
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {(stageLoading || sensorLoading) && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}
    </div>
  );
};