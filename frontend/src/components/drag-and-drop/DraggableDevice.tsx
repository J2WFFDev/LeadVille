/**
 * Draggable Device Component
 * Represents sensors and timers that can be dragged to targets
 */

import type { DeviceItem } from '../../hooks/useDragAndDrop.js';

interface DraggableDeviceProps {
  device: DeviceItem;
  onDragStart: (device: DeviceItem) => void;
  onDragEnd: () => void;
  isDragging?: boolean;
  isBeingDragged?: boolean;
}

export const DraggableDevice = ({
  device,
  onDragStart,
  onDragEnd,
  isDragging = false,
  isBeingDragged = false
}: DraggableDeviceProps) => {
  const deviceType = device.type === 'timer' ? 'Timer' : 'Impact Sensor';
  const icon = device.type === 'timer' ? '⏱️' : '📡';
  const displayAddress = device.address || device.hw_addr || 'Unknown';
  const displayName = device.name || device.label || 'Unnamed Device';

  const handleDragStart = (e: DragEvent) => {
    if (e.dataTransfer) {
      e.dataTransfer.setData('application/json', JSON.stringify(device));
      e.dataTransfer.effectAllowed = 'move';
    }
    onDragStart(device);
  };

  const handleDragEnd = () => {
    onDragEnd();
  };

  // Determine styling based on state
  const getDeviceStyles = () => {
    let baseClasses = 'bg-white border border-gray-300 rounded-lg p-3 cursor-move transition-all duration-200 select-none';
    
    if (isBeingDragged) {
      baseClasses += ' opacity-50 scale-95 rotate-2';
    } else if (isDragging) {
      baseClasses += ' opacity-75';
    } else {
      baseClasses += ' hover:border-blue-400 hover:shadow-md hover:scale-102';
    }

    return baseClasses;
  };

  // Get device status color and text
  const getDeviceStatus = () => {
    if (device.isPoolDevice) {
      return {
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-800',
        text: 'Pool Device'
      };
    }
    return {
      bgColor: 'bg-green-100',
      textColor: 'text-green-800',
      text: 'Discovered'
    };
  };

  // Get signal strength indicator
  const getSignalStrength = () => {
    if (!device.rssi) return null;
    
    let strengthClass = 'bg-gray-400';
    let strengthText = 'Unknown';
    
    if (device.rssi >= -50) {
      strengthClass = 'bg-green-500';
      strengthText = 'Excellent';
    } else if (device.rssi >= -60) {
      strengthClass = 'bg-green-400';
      strengthText = 'Good';
    } else if (device.rssi >= -70) {
      strengthClass = 'bg-yellow-500';
      strengthText = 'Fair';
    } else {
      strengthClass = 'bg-red-500';
      strengthText = 'Poor';
    }

    return {
      className: strengthClass,
      text: strengthText,
      value: device.rssi
    };
  };

  // Get battery level indicator
  const getBatteryLevel = () => {
    if (!device.battery) return null;
    
    let batteryClass = 'bg-gray-400';
    let batteryIcon = '🔋';
    
    if (device.battery >= 80) {
      batteryClass = 'bg-green-500';
      batteryIcon = '🔋';
    } else if (device.battery >= 60) {
      batteryClass = 'bg-green-400';
      batteryIcon = '🔋';
    } else if (device.battery >= 40) {
      batteryClass = 'bg-yellow-500';
      batteryIcon = '🔋';
    } else if (device.battery >= 20) {
      batteryClass = 'bg-orange-500';
      batteryIcon = '🪫';
    } else {
      batteryClass = 'bg-red-500';
      batteryIcon = '🪫';
    }

    return {
      className: batteryClass,
      icon: batteryIcon,
      value: device.battery
    };
  };

  const status = getDeviceStatus();
  const signal = getSignalStrength();
  const battery = getBatteryLevel();

  return (
    <div
      className={getDeviceStyles()}
      draggable={true}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      role="button"
      tabIndex={0}
      aria-label={`Draggable ${deviceType}: ${displayName}`}
      title={`Drag to assign ${deviceType} to a target`}
    >
      {/* Device Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <span className="text-2xl" role="img" aria-label={deviceType}>
            {icon}
          </span>
          <div>
            <h3 className="font-semibold text-gray-900">{deviceType}</h3>
            <div className="flex items-center space-x-2">
              <span className={`text-xs px-2 py-1 rounded ${status.bgColor} ${status.textColor}`}>
                {status.text}
              </span>
              {isBeingDragged && (
                <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded animate-pulse">
                  Dragging...
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Quick Status Indicators */}
        <div className="flex items-center space-x-2">
          {signal && (
            <div 
              className={`w-3 h-3 rounded-full ${signal.className}`}
              title={`Signal: ${signal.text} (${signal.value} dBm)`}
            />
          )}
          {battery && (
            <div className="flex items-center space-x-1">
              <span 
                className="text-sm"
                title={`Battery: ${battery.value}%`}
              >
                {battery.icon}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Device Details */}
      <div className="text-sm text-gray-600 space-y-1">
        <div className="flex justify-between">
          <span className="font-medium">MAC:</span>
          <span className="font-mono text-xs">
            {displayAddress.length > 12 ? `${displayAddress.slice(0, 12)}...` : displayAddress}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="font-medium">Name:</span>
          <span className="truncate max-w-24" title={displayName}>
            {displayName}
          </span>
        </div>

        {signal && (
          <div className="flex justify-between">
            <span className="font-medium">Signal:</span>
            <span className={`font-medium ${
              signal.value >= -60 ? 'text-green-600' : 
              signal.value >= -70 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {signal.value} dBm
            </span>
          </div>
        )}

        {battery && (
          <div className="flex justify-between">
            <span className="font-medium">Battery:</span>
            <span className={`font-medium ${
              battery.value >= 60 ? 'text-green-600' : 
              battery.value >= 30 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {battery.value}%
            </span>
          </div>
        )}
      </div>

      {/* Drag Handle Indicator */}
      {!isBeingDragged && (
        <div className="mt-3 flex items-center justify-center space-x-1 text-gray-400">
          <div className="w-1 h-1 bg-current rounded-full"></div>
          <div className="w-1 h-1 bg-current rounded-full"></div>
          <div className="w-1 h-1 bg-current rounded-full"></div>
          <div className="w-1 h-1 bg-current rounded-full"></div>
        </div>
      )}
    </div>
  );
};