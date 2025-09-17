/**
 * Stage Layout Component
 * Dynamic SVG rendering with enhanced callouts and real-time sensor status
 */

import React, { useRef, useEffect, useState } from 'react';

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

interface SensorAssignment {
  targetId: string;
  sensorAddress: string;
}

interface ConnectedDevice {
  address: string;
  name: string;
  batteryLevel?: number;
  signalStrength?: number;
  lastHit?: Date;
  status: 'connected' | 'disconnected' | 'low-battery' | 'error';
}

interface HitEvent {
  id: string;
  targetId: string;
  timestamp: string;
  magnitude: number;
}

interface StageLayoutProps {
  stageConfig: StageConfiguration;
  sensorAssignments: Record<string, SensorAssignment>;
  connectedDevices: ConnectedDevice[];
  liveHitMarkers?: Record<string, HitEvent>; // Optional for RO view
}

interface SVGCoordinate {
  x: number;
  y: number;
  size: number;
}

export const StageLayout: React.FC<StageLayoutProps> = ({
  stageConfig,
  sensorAssignments,
  connectedDevices,
  liveHitMarkers = {}
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });

  // Convert real-world coordinates to SVG coordinates using holistic perspective geometry
  const convertToSVGCoordinates = (target: Target): SVGCoordinate => {
    const { distance, offset, height } = target;
    
    // Constants for perspective geometry (matching vanilla JS implementation)
    const eyeLevel = 56; // inches
    const pixelsPerFoot = 15; // Unified scaling factor
    const svgWidth = dimensions.width;
    const svgHeight = dimensions.height;
    
    // Convert to pixels
    const distancePixels = distance * 12 * pixelsPerFoot; // feet to inches to pixels
    const offsetPixels = offset * 12 * pixelsPerFoot;
    const heightPixels = height * 12 * pixelsPerFoot;
    
    // Apply perspective transformation
    const perspectiveFactor = 1 / (1 + distancePixels / 10000);
    const apparentSize = 20 * perspectiveFactor; // Base size with perspective
    
    // Calculate SVG coordinates
    const x = svgWidth / 2 + offsetPixels * perspectiveFactor;
    const y = svgHeight - 100 - (heightPixels - eyeLevel) * perspectiveFactor;
    
    return { x, y, size: Math.max(apparentSize, 8) };
  };

  // Get target color based on type
  const getTargetColor = (target: Target): string => {
    if (target.type === 'Stop Plate') return '#ff4444';
    if (target.category === 'Popper') return '#44ff44';
    if (target.shape === 'circle') return '#4444ff';
    return '#888888';
  };

  // Get sensor info for a target
  const getSensorInfo = (targetId: string) => {
    const assignment = sensorAssignments[targetId];
    if (!assignment) return null;
    
    const device = connectedDevices.find(d => d.address === assignment.sensorAddress);
    return device;
  };

  // Get sensor status color
  const getSensorStatusColor = (device: ConnectedDevice | null): string => {
    if (!device) return '#gray-400';
    switch (device.status) {
      case 'connected': return '#green-500';
      case 'low-battery': return '#yellow-500';
      case 'error': return '#red-500';
      case 'disconnected': return '#gray-400';
      default: return '#gray-400';
    }
  };

  // Hit detection will be implemented with WebSocket integration

  // Format time ago
  const getTimeAgo = (date: Date | undefined): string => {
    if (!date) return 'Never';
    const diffMs = Date.now() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour}h ago`;
    return `${Math.floor(diffHour / 24)}d ago`;
  };

  // Update dimensions when container resizes
  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current?.parentElement) {
        const container = svgRef.current.parentElement;
        setDimensions({
          width: container.clientWidth,
          height: Math.max(400, container.clientWidth * 0.5)
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Sort targets by distance (farthest first for proper layering)
  const sortedTargets = [...stageConfig.targets].sort((a, b) => b.distance - a.distance);

  return (
    <div className="w-full">
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="border border-gray-300 rounded-lg bg-gray-100"
        viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
      >
        {/* Background elements */}
        <defs>
          <pattern id="groundPattern" patternUnits="userSpaceOnUse" width="50" height="50">
            <rect width="50" height="50" fill="#e5e7eb" />
            <circle cx="25" cy="25" r="1" fill="#d1d5db" />
          </pattern>
        </defs>
        
        <rect width="100%" height="100%" fill="url(#groundPattern)" />
        
        {/* Ground line */}
        <line
          x1="0"
          y1={dimensions.height - 50}
          x2={dimensions.width}
          y2={dimensions.height - 50}
          stroke="#374151"
          strokeWidth="2"
        />

        {/* Render targets */}
        {sortedTargets.map((target) => {
          const coords = convertToSVGCoordinates(target);
          const targetId = `P${target.target_number}`;
          const sensorInfo = getSensorInfo(targetId);
          const hitEvent = liveHitMarkers[targetId];
          const isHit = !!hitEvent; // Check if target has active hit marker
          
          return (
            <g key={target.target_number}>
              {/* Target shape */}
              {target.shape === 'circle' ? (
                <circle
                  cx={coords.x}
                  cy={coords.y}
                  r={coords.size}
                  fill={isHit ? '#ff4444' : getTargetColor(target)}
                  stroke={isHit ? '#ff0000' : '#333333'}
                  strokeWidth={isHit ? 3 : 1}
                  className={isHit ? 'animate-pulse' : ''}
                />
              ) : (
                <rect
                  x={coords.x - coords.size}
                  y={coords.y - coords.size}
                  width={coords.size * 2}
                  height={coords.size * 2}
                  fill={isHit ? '#ff4444' : getTargetColor(target)}
                  stroke={isHit ? '#ff0000' : '#333333'}
                  strokeWidth={isHit ? 3 : 1}
                  className={isHit ? 'animate-pulse' : ''}
                />
              )}

              {/* Enhanced Callout */}
              <g transform={`translate(${coords.x + coords.size + 10}, ${coords.y - 25})`}>
                {/* Callout background */}
                <rect
                  width="140"
                  height="60"
                  fill="white"
                  stroke="#d1d5db"
                  strokeWidth="1"
                  rx="4"
                  className="drop-shadow-md"
                />
                
                {/* Target ID */}
                <text
                  x="8"
                  y="15"
                  fontSize="12"
                  fontWeight="bold"
                  fill="#374151"
                >
                  {targetId}
                </text>
                
                {/* Sensor info */}
                {sensorInfo ? (
                  <>
                    <text x="8" y="28" fontSize="10" fill="#6b7280">
                      {sensorInfo.name}
                    </text>
                    
                    {/* Status indicator */}
                    <circle
                      cx="125"
                      cy="12"
                      r="4"
                      fill={getSensorStatusColor(sensorInfo)}
                    />
                    
                    {/* Battery level */}
                    {sensorInfo.batteryLevel && (
                      <text x="8" y="40" fontSize="9" fill="#6b7280">
                        Battery: {sensorInfo.batteryLevel}%
                      </text>
                    )}
                    
                    {/* Last hit - show live hit or historical */}
                    <text x="8" y="52" fontSize="9" fill={isHit ? "#ef4444" : "#6b7280"}>
                      {isHit ? `HIT! ${new Date(hitEvent.timestamp).toLocaleTimeString()}` : `Last: ${getTimeAgo(sensorInfo.lastHit)}`}
                    </text>
                  </>
                ) : (
                  <text x="8" y="35" fontSize="10" fill="#ef4444">
                    No sensor assigned
                  </text>
                )}
              </g>

              {/* Connection line to callout */}
              <line
                x1={coords.x + coords.size}
                y1={coords.y}
                x2={coords.x + coords.size + 10}
                y2={coords.y}
                stroke="#d1d5db"
                strokeWidth="1"
                strokeDasharray="2,2"
              />
            </g>
          );
        })}

        {/* Stage label */}
        <text
          x={dimensions.width / 2}
          y={dimensions.height - 20}
          textAnchor="middle"
          fontSize="16"
          fontWeight="bold"
          fill="#374151"
        >
          {stageConfig.league} - {stageConfig.stage_name}
        </text>
      </svg>
    </div>
  );
};