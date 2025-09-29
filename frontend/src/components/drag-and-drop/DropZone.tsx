/**
 * Drop Zone Component
 * Represents target slots and timer slots where devices can be dropped
 */

import type { Assignment } from '../../hooks/useDragAndDrop.js';

interface DropZoneProps {
  id: string;
  type: 'target' | 'timer';
  targetNumber?: number;
  targetInfo?: {
    shape: string;
    type?: string;
    category?: string;
    distance_feet: number;
    height_feet?: number;
  };
  assignment?: Assignment;
  canAcceptDrop: boolean;
  isDragOver: boolean;
  onDragOver: (e: DragEvent) => void;
  onDragLeave: (e: DragEvent) => void;
  onDrop: (e: DragEvent) => void;
  onRemoveAssignment?: () => void;
}

export const DropZone = ({
  id,
  type,
  targetNumber,
  targetInfo,
  assignment,
  canAcceptDrop,
  isDragOver,
  onDragOver,
  onDragLeave,
  onDrop,
  onRemoveAssignment
}: DropZoneProps) => {

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    onDragOver(e);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    onDragLeave(e);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    onDrop(e);
  };

  // Get drop zone styling based on state
  const getDropZoneStyles = () => {
    let baseClasses = 'rounded-lg p-4 text-center transition-all duration-200 min-h-24 flex flex-col items-center justify-center';
    
    if (assignment) {
      // Has assignment - success state
      baseClasses += ' bg-green-50 border-2 border-green-300 text-green-800';
    } else if (isDragOver && canAcceptDrop) {
      // Valid drag over
      baseClasses += ' bg-blue-50 border-2 border-blue-400 border-dashed text-blue-700 scale-105';
    } else if (isDragOver) {
      // Invalid drag over
      baseClasses += ' bg-red-50 border-2 border-red-400 border-dashed text-red-700';
    } else {
      // Default state
      baseClasses += ' bg-gray-50 border-2 border-gray-300 border-dashed text-gray-600 hover:border-gray-400 hover:bg-gray-100';
    }

    return baseClasses;
  };

  // Get the appropriate icon for the drop zone type
  const getDropZoneIcon = () => {
    if (assignment) {
      return assignment.targetAssignment === 'timer' ? '✅ ⏱️' : '✅ 📡';
    }
    
    return type === 'timer' ? '⏱️' : '🎯';
  };

  // Get drop zone title text
  const getDropZoneTitle = () => {
    if (type === 'timer') {
      return 'Timer Device';
    }
    return `Target ${targetNumber}`;
  };

  // Get drop zone subtitle/info
  const getDropZoneSubtitle = () => {
    if (type === 'timer') {
      return 'Drop timer device here';
    }
    
    if (targetInfo) {
      const parts = [targetInfo.shape];
      if (targetInfo.type) parts.push(targetInfo.type);
      if (targetInfo.distance_feet) parts.push(`${targetInfo.distance_feet}ft`);
      return parts.join(' • ');
    }
    
    return 'Drop impact sensor here';
  };

  // Get assignment display info
  const getAssignmentInfo = () => {
    if (!assignment) return null;
    
    return {
      deviceType: assignment.targetAssignment === 'timer' ? 'Timer' : 'Impact Sensor',
      deviceAddress: assignment.deviceAddress,
      deviceName: assignment.deviceAddress // Could be enhanced with device names
    };
  };

  const assignmentInfo = getAssignmentInfo();

  return (
    <div
      className={getDropZoneStyles()}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="region"
      aria-label={`${getDropZoneTitle()} drop zone`}
      title={assignment ? `Assigned: ${assignmentInfo?.deviceAddress}` : getDropZoneSubtitle()}
    >
      {assignment ? (
        // Assigned state
        <div className="space-y-2 w-full">
          <div className="flex items-center justify-center space-x-2">
            <span className="text-2xl">{getDropZoneIcon()}</span>
            <div className="text-center">
              <h3 className="font-semibold text-green-900">{getDropZoneTitle()}</h3>
              <p className="text-sm text-green-700">{assignmentInfo?.deviceType} Assigned</p>
            </div>
          </div>
          
          <div className="text-xs text-green-600 bg-green-100 rounded px-2 py-1">
            <div className="font-mono truncate">
              {(assignmentInfo?.deviceAddress?.length || 0) > 15 
                ? `${assignmentInfo?.deviceAddress?.slice(0, 15)}...` 
                : assignmentInfo?.deviceAddress}
            </div>
          </div>
          
          {onRemoveAssignment && (
            <button
              onClick={onRemoveAssignment}
              className="text-xs text-red-600 hover:text-red-800 bg-red-50 hover:bg-red-100 rounded px-2 py-1 transition-colors"
              title="Remove assignment"
            >
              ✕ Remove
            </button>
          )}
        </div>
      ) : (
        // Empty state
        <div className="space-y-2">
          <span className="text-3xl opacity-60">{getDropZoneIcon()}</span>
          <div>
            <h3 className="font-semibold">{getDropZoneTitle()}</h3>
            <p className="text-sm opacity-75">{getDropZoneSubtitle()}</p>
          </div>
          
          {isDragOver && !canAcceptDrop && (
            <div className="text-xs text-red-600 bg-red-100 rounded px-2 py-1">
              ⚠️ Invalid device type
            </div>
          )}
          
          {isDragOver && canAcceptDrop && (
            <div className="text-xs text-blue-600 bg-blue-100 rounded px-2 py-1 animate-pulse">
              📥 Drop to assign
            </div>
          )}
        </div>
      )}
      
      {/* Target info display */}
      {type === 'target' && targetInfo && !assignment && (
        <div className="mt-2 text-xs text-gray-500 opacity-75">
          {targetInfo.height_feet && (
            <div>{targetInfo.height_feet}ft height</div>
          )}
        </div>
      )}
    </div>
  );
};