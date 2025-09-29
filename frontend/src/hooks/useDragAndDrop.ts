/**
 * Custom React hook for drag and drop functionality
 * Handles device assignment to targets and timers
 */

import { useState, useCallback } from 'react';

export interface DeviceItem {
  id?: number;
  address: string;
  name: string;
  type: 'timer' | 'accelerometer';
  device_type?: string;
  hw_addr?: string;
  label?: string;
  rssi?: number;
  battery?: number;
  isPoolDevice?: boolean;
}

export interface DropZone {
  id: string;
  type: 'target' | 'timer';
  targetId?: number;
  targetNumber?: number;
  acceptedTypes: string[];
}

export interface Assignment {
  deviceAddress: string;
  deviceId?: number;
  targetId?: number;
  targetAssignment: string; // 'timer' or 'target-{id}'
}

interface DragAndDropState {
  draggedItem: DeviceItem | null;
  dropZones: DropZone[];
  assignments: Record<string, Assignment>;
  isDragging: boolean;
  dragOverZone: string | null;
}

export const useDragAndDrop = () => {
  const [state, setState] = useState<DragAndDropState>({
    draggedItem: null,
    dropZones: [],
    assignments: {},
    isDragging: false,
    dragOverZone: null,
  });

  // Initialize drop zones based on stage configuration
  const initializeDropZones = useCallback((targets: any[], hasTimer = true) => {
    const zones: DropZone[] = [];
    
    // Add timer drop zone
    if (hasTimer) {
      zones.push({
        id: 'timer-slot',
        type: 'timer',
        acceptedTypes: ['timer']
      });
    }
    
    // Add target drop zones
    targets.forEach(target => {
      zones.push({
        id: `target-${target.id}`,
        type: 'target',
        targetId: target.id,
        targetNumber: target.target_number,
        acceptedTypes: ['accelerometer']
      });
    });

    setState((prev: DragAndDropState) => ({ ...prev, dropZones: zones }));
  }, []);

  // Start dragging a device
  const handleDragStart = useCallback((device: DeviceItem) => {
    setState((prev: DragAndDropState) => ({
      ...prev,
      draggedItem: device,
      isDragging: true
    }));
  }, []);

  // Handle drag end
  const handleDragEnd = useCallback(() => {
    setState((prev: DragAndDropState) => ({
      ...prev,
      draggedItem: null,
      isDragging: false,
      dragOverZone: null
    }));
  }, []);

  // Handle drag over drop zone
  const handleDragOver = useCallback((zoneId: string, deviceType: string) => {
    const zone = state.dropZones.find((z: DropZone) => z.id === zoneId);
    const canDrop = zone?.acceptedTypes.includes(deviceType) || false;
    
    setState((prev: DragAndDropState) => ({
      ...prev,
      dragOverZone: canDrop ? zoneId : null
    }));
    
    return canDrop;
  }, [state.dropZones]);

  // Validate device assignment before dropping
  const validateAssignment = useCallback((zoneId: string, device: DeviceItem) => {
    const zone = state.dropZones.find((z: DropZone) => z.id === zoneId);
    if (!zone) return false;

    // Basic type checking
    if (!zone.acceptedTypes.includes(device.type)) {
      return false;
    }

    // Check for existing assignment to prevent duplicates
    const assignmentValues = Object.values(state.assignments) as Assignment[];
    const existingAssignment = assignmentValues.find(
      (assignment: Assignment) => assignment.deviceAddress === device.address
    );
    if (existingAssignment) {
      return false;
    }

    // Check if zone already has an assignment
    if (state.assignments[zoneId]) {
      return false;
    }

    return true;
  }, [state]);

  // Handle dropping a device
  const handleDrop = useCallback(async (
    zoneId: string,
    onAssign?: (assignment: Assignment) => Promise<boolean>
  ) => {
    const { draggedItem } = state;
    if (!draggedItem) return false;

    const zone = state.dropZones.find((z: DropZone) => z.id === zoneId);
    if (!zone || !zone.acceptedTypes.includes(draggedItem.type)) {
      return false;
    }

    const assignment: Assignment = {
      deviceAddress: draggedItem.address || draggedItem.hw_addr || '',
      deviceId: draggedItem.id,
      targetId: zone.targetId,
      targetAssignment: zone.type === 'timer' ? 'timer' : `target-${zone.targetId}`
    };

    // Call the assignment handler if provided
    if (onAssign) {
      const success = await onAssign(assignment);
      if (!success) {
        return false;
      }
    }

    // Update local state
    setState((prev: DragAndDropState) => ({
      ...prev,
      assignments: {
        ...prev.assignments,
        [zoneId]: assignment
      },
      draggedItem: null,
      isDragging: false,
      dragOverZone: null
    }));

    return true;
  }, [state]);

  // Remove an assignment
  const removeAssignment = useCallback((zoneId: string) => {
    setState((prev: DragAndDropState) => {
      const newAssignments = { ...prev.assignments };
      delete newAssignments[zoneId];
      return {
        ...prev,
        assignments: newAssignments
      };
    });
  }, []);

  // Get assignment for a specific zone
  const getAssignment = useCallback((zoneId: string) => {
    return state.assignments[zoneId];
  }, [state.assignments]);

  // Check if a zone can accept the current dragged item
  const canDropInZone = useCallback((zoneId: string) => {
    const { draggedItem } = state;
    if (!draggedItem) return false;

    const zone = state.dropZones.find((z: DropZone) => z.id === zoneId);
    return zone?.acceptedTypes.includes(draggedItem.type) || false;
  }, [state]);

  // Get summary of assignments
  const getAssignmentSummary = useCallback(() => {
    const assignmentValues = Object.values(state.assignments) as Assignment[];
    const timerAssigned = assignmentValues.some(
      (a: Assignment) => a.targetAssignment === 'timer'
    );
    const sensorCount = assignmentValues.filter(
      (a: Assignment) => a.targetAssignment.startsWith('target-')
    ).length;

    return {
      timerAssigned,
      sensorCount,
      totalAssignments: Object.keys(state.assignments).length,
      isComplete: timerAssigned && sensorCount > 0
    };
  }, [state.assignments]);

  // Clear all assignments
  const clearAllAssignments = useCallback(() => {
    setState((prev: DragAndDropState) => ({
      ...prev,
      assignments: {}
    }));
  }, []);

  return {
    // State
    draggedItem: state.draggedItem,
    isDragging: state.isDragging,
    dragOverZone: state.dragOverZone,
    assignments: state.assignments,
    dropZones: state.dropZones,
    
    // Actions
    initializeDropZones,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop,
    removeAssignment,
    getAssignment,
    canDropInZone,
    getAssignmentSummary,
    clearAllAssignments,
    validateAssignment
  };
};