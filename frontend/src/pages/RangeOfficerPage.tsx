/**
 * Range Officer (RO) View Page
 * Live stage monitoring with hit markers, impact visualization, and run history
 */

import React, { useState, useEffect } from 'react';
import { StageLayout } from '../components/match-setup/StageLayout';
import { useStageConfig } from '../hooks/useStageConfig';
import { useWebSocketConnection } from '../hooks/useWebSocket';

interface HitEvent {
  id: string;
  targetId: string;
  timestamp: string;
  magnitude: number;
  runId?: string;
  sensorId?: string;
}

interface RunSummary {
  id: string;
  shooterId: string;
  shooterName: string;
  stageId: string;
  startTime: string;
  endTime?: string;
  status: 'active' | 'completed' | 'paused';
  hits: HitEvent[];
  totalHits: number;
  timeElapsed: number;
}

interface TimerEvent {
  id: string;
  type: 'START' | 'SHOT' | 'STOP';
  timestamp: string;
  runId?: string;
}

export const RangeOfficerPage: React.FC = () => {
  const { currentStageConfig, loadStageConfig, isLoading: stageLoading } = useStageConfig();
  const { isConnected } = useWebSocketConnection();
  
  // RO-specific state
  const [currentRun, setCurrentRun] = useState<RunSummary | null>(null);
  const [recentHits, setRecentHits] = useState<HitEvent[]>([]);
  const [runHistory, setRunHistory] = useState<RunSummary[]>([]);
  const [liveHitMarkers, setLiveHitMarkers] = useState<Record<string, HitEvent>>({});
  const [timerEvents, setTimerEvents] = useState<TimerEvent[]>([]);
  const [autoHideDuration, setAutoHideDuration] = useState(5000); // 5 seconds

  // Mock connected devices and sensor assignments for demo
  const [connectedDevices] = useState([
    {
      address: 'BT50:01:A1:B2:C3',
      name: 'BT50-P1',
      batteryLevel: 85,
      signalStrength: -45,
      lastHit: new Date(Date.now() - 120000), // 2 minutes ago
      status: 'connected' as const
    },
    {
      address: 'BT50:02:D4:E5:F6',
      name: 'BT50-P2',
      batteryLevel: 72,
      signalStrength: -52,
      lastHit: new Date(Date.now() - 300000), // 5 minutes ago
      status: 'connected' as const
    },
    {
      address: 'BT50:03:G7:H8:I9',
      name: 'BT50-P3',
      batteryLevel: 15,
      signalStrength: -38,
      status: 'low-battery' as const
    }
  ]);

  const [sensorAssignments] = useState({
    'P1': { targetId: 'P1', sensorAddress: 'BT50:01:A1:B2:C3' },
    'P2': { targetId: 'P2', sensorAddress: 'BT50:02:D4:E5:F6' },
    'P3': { targetId: 'P3', sensorAddress: 'BT50:03:G7:H8:I9' }
  });

  // Load default stage on mount
  useEffect(() => {
    loadStageConfig('USPSA', 'Steel_Challenge_5to_Go');
  }, [loadStageConfig]);

  // Auto-hide hit markers after duration
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setLiveHitMarkers(prev => {
        const updated = { ...prev };
        Object.keys(updated).forEach(targetId => {
          const hitTime = new Date(updated[targetId].timestamp).getTime();
          if (now - hitTime > autoHideDuration) {
            delete updated[targetId];
          }
        });
        return updated;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [autoHideDuration]);

  // Format time duration
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return mins > 0 ? `${mins}:${secs.padStart(5, '0')}` : `${secs}s`;
  };

  // Format timestamp for display
  const formatTime = (timestamp: string): string => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  };

  // Get system status color
  const getSystemStatusColor = () => {
    if (!isConnected) return 'bg-red-500';
    if (connectedDevices.filter(d => d.status === 'connected').length === 0) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // Demo function to simulate hit events
  const simulateHit = (targetId: string) => {
    const hitEvent: HitEvent = {
      id: `hit_${Date.now()}_${targetId}`,
      targetId,
      timestamp: new Date().toISOString(),
      magnitude: Math.random() * 1000 + 200, // Random magnitude
      sensorId: sensorAssignments[targetId]?.sensorAddress
    };

    // Add to live markers (will auto-hide after duration)
    setLiveHitMarkers(prev => ({
      ...prev,
      [targetId]: hitEvent
    }));

    // Add to recent hits
    setRecentHits(prev => [hitEvent, ...prev.slice(0, 9)]); // Keep last 10

    // Add to current run if active
    if (currentRun) {
      setCurrentRun(prev => prev ? {
        ...prev,
        hits: [...prev.hits, hitEvent],
        totalHits: prev.totalHits + 1
      } : null);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              🎯 Range Officer View
            </h1>
            <p className="text-gray-600 text-sm">
              Live stage monitoring and run management
            </p>
          </div>

          {/* System Status */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${getSystemStatusColor()}`}></div>
              <span className="text-sm font-medium">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            
            <div className="text-sm text-gray-600">
              Sensors: {connectedDevices.filter(d => d.status === 'connected').length}/{connectedDevices.length}
            </div>

            <div className="text-sm text-gray-600">
              {currentStageConfig ? `${currentStageConfig.league} - ${currentStageConfig.stage_name}` : 'No Stage Loaded'}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex min-h-0">
        {/* Stage Layout - Main Area */}
        <div className="flex-1 p-4">
          <div className="bg-white rounded-lg shadow-md h-full flex flex-col">
            <div className="p-4 border-b">
              <h2 className="text-xl font-semibold flex items-center">
                📍 Stage Layout
                {currentRun && (
                  <span className="ml-4 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                    ⏱️ Run Active: {formatDuration(currentRun.timeElapsed)}
                  </span>
                )}
              </h2>
            </div>
            
            <div className="flex-1 p-4">
              {currentStageConfig ? (
                <StageLayout
                  stageConfig={currentStageConfig}
                  sensorAssignments={sensorAssignments}
                  connectedDevices={connectedDevices}
                  liveHitMarkers={liveHitMarkers}
                />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  {stageLoading ? (
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                      <span>Loading stage...</span>
                    </div>
                  ) : (
                    <span>No stage configuration loaded</span>
                  )}
                </div>
              )}
            </div>

            {/* Demo Controls */}
            <div className="p-4 border-t bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-gray-700">Demo Controls:</span>
                  <div className="flex space-x-2 mt-2">
                    {currentStageConfig?.targets.map(target => (
                      <button
                        key={target.target_number}
                        onClick={() => simulateHit(`P${target.target_number}`)}
                        className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                      >
                        Hit P{target.target_number}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div className="text-sm text-gray-500">
                  Hit markers auto-hide after {autoHideDuration / 1000}s
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-80 p-4 space-y-4">
          {/* Current Run Summary */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              ⏱️ Current String
            </h3>
            
            {currentRun ? (
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600">Shooter</div>
                  <div className="font-medium">{currentRun.shooterName}</div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">Start Time</div>
                    <div className="font-medium text-sm">{formatTime(currentRun.startTime)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Elapsed</div>
                    <div className="font-medium text-sm">{formatDuration(currentRun.timeElapsed)}</div>
                  </div>
                </div>
                
                <div>
                  <div className="text-sm text-gray-600">Hits</div>
                  <div className="font-medium">{currentRun.totalHits}</div>
                </div>

                <div className="space-y-1">
                  <div className="text-sm text-gray-600">Hit Sequence</div>
                  <div className="text-xs space-y-1 max-h-20 overflow-y-auto">
                    {currentRun.hits.map((hit, idx) => (
                      <div key={hit.id} className="flex justify-between">
                        <span>{idx + 1}. {hit.targetId}</span>
                        <span>{formatTime(hit.timestamp)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                No active string
                <div className="mt-2">
                  <button 
                    onClick={() => setCurrentRun({
                      id: `run_${Date.now()}`,
                      shooterId: 'demo_shooter',
                      shooterName: 'Demo Shooter',
                      stageId: 'current_stage',
                      startTime: new Date().toISOString(),
                      status: 'active',
                      hits: [],
                      totalHits: 0,
                      timeElapsed: 0
                    })}
                    className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                  >
                    Start Demo Run
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Recent Hits */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              🎯 Recent Hits
            </h3>
            
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {recentHits.length > 0 ? (
                recentHits.map((hit, idx) => (
                  <div key={hit.id} className="flex items-center justify-between text-sm">
                    <span className="font-medium">{hit.targetId}</span>
                    <span className="text-gray-600">{formatTime(hit.timestamp)}</span>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-4">
                  No recent hits
                </div>
              )}
            </div>
          </div>

          {/* Run History */}
          <div className="bg-white rounded-lg shadow-md p-4 flex-1">
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              📋 Run History
            </h3>
            
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {runHistory.length > 0 ? (
                runHistory.map((run) => (
                  <div key={run.id} className="p-2 border border-gray-200 rounded text-sm">
                    <div className="flex justify-between items-start">
                      <span className="font-medium">{run.shooterName}</span>
                      <span className="text-xs text-gray-500">{formatTime(run.startTime)}</span>
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      Hits: {run.totalHits} • Time: {run.endTime ? formatDuration((new Date(run.endTime).getTime() - new Date(run.startTime).getTime()) / 1000) : 'Active'}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-4">
                  No completed runs
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};