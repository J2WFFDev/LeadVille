/**
 * Validation utilities for drag and drop device assignment
 */

import type { DeviceItem, DropZone, Assignment } from '../hooks/useDragAndDrop.js';

export interface ValidationResult {
  isValid: boolean;
  errorMessage?: string;
  warningMessage?: string;
}

export interface ValidationRules {
  requireTimerForStage: boolean;
  maxSensorsPerTarget: number;
  minBatteryLevel: number;
  maxDistanceFromBridge: number; // in meters, based on RSSI
  allowDuplicateAssignments: boolean;
}

const defaultRules: ValidationRules = {
  requireTimerForStage: true,
  maxSensorsPerTarget: 1,
  minBatteryLevel: 15, // 15% minimum battery
  maxDistanceFromBridge: 50, // Maximum distance in meters
  allowDuplicateAssignments: false
};

/**
 * Validate if a device can be assigned to a drop zone
 */
export const validateDeviceAssignment = (
  device: DeviceItem,
  dropZone: DropZone,
  existingAssignments: Record<string, Assignment>,
  rules: Partial<ValidationRules> = {}
): ValidationResult => {
  const validationRules = { ...defaultRules, ...rules };

  // Check device type compatibility
  if (!dropZone.acceptedTypes.includes(device.type)) {
    return {
      isValid: false,
      errorMessage: `${device.type === 'timer' ? 'Timer' : 'Sensor'} devices cannot be assigned to ${dropZone.type} slots`
    };
  }

  // Check if device is already assigned (if duplicates not allowed)
  if (!validationRules.allowDuplicateAssignments) {
    const existingAssignment = Object.values(existingAssignments).find(
      assignment => assignment.deviceAddress === device.address
    );
    if (existingAssignment) {
      return {
        isValid: false,
        errorMessage: 'Device is already assigned to another target'
      };
    }
  }

  // Check if target already has maximum sensors assigned
  if (dropZone.type === 'target') {
    const targetAssignments = Object.values(existingAssignments).filter(
      assignment => assignment.targetId === dropZone.targetId
    );
    if (targetAssignments.length >= validationRules.maxSensorsPerTarget) {
      return {
        isValid: false,
        errorMessage: `Target already has maximum number of sensors assigned (${validationRules.maxSensorsPerTarget})`
      };
    }
  }

  // Battery level validation
  if (device.battery !== undefined && device.battery !== null) {
    if (device.battery < validationRules.minBatteryLevel) {
      return {
        isValid: false,
        errorMessage: `Device battery level (${device.battery}%) is below minimum required (${validationRules.minBatteryLevel}%)`
      };
    }
    if (device.battery < validationRules.minBatteryLevel + 10) {
      return {
        isValid: true,
        warningMessage: `Device battery level (${device.battery}%) is low. Consider replacing batteries soon.`
      };
    }
  }

  // Signal strength validation (RSSI-based distance estimation)
  if (device.rssi !== undefined && device.rssi !== null) {
    const estimatedDistance = estimateDistanceFromRSSI(device.rssi);
    if (estimatedDistance > validationRules.maxDistanceFromBridge) {
      return {
        isValid: false,
        errorMessage: `Device is too far from bridge (estimated ${estimatedDistance.toFixed(1)}m). Signal: ${device.rssi} dBm`
      };
    }
    if (device.rssi < -70) {
      return {
        isValid: true,
        warningMessage: `Weak signal strength (${device.rssi} dBm). Consider moving device closer to bridge.`
      };
    }
  }

  return { isValid: true };
};

/**
 * Validate complete stage setup
 */
export const validateStageSetup = (
  assignments: Record<string, Assignment>,
  dropZones: DropZone[],
  rules: Partial<ValidationRules> = {}
): ValidationResult => {
  const validationRules = { ...defaultRules, ...rules };
  const warnings: string[] = [];

  // Check if timer is required and assigned
  if (validationRules.requireTimerForStage) {
    const timerAssigned = Object.values(assignments).some(
      assignment => assignment.targetAssignment === 'timer'
    );
    if (!timerAssigned) {
      return {
        isValid: false,
        errorMessage: 'Timer device must be assigned for stage operation'
      };
    }
  }

  // Check for unassigned targets
  const targetZones = dropZones.filter(zone => zone.type === 'target');
  const assignedTargets = Object.values(assignments).filter(
    assignment => assignment.targetAssignment.startsWith('target-')
  );
  
  const unassignedTargets = targetZones.length - assignedTargets.length;
  if (unassignedTargets > 0) {
    warnings.push(`${unassignedTargets} target(s) do not have sensors assigned`);
  }

  // Check for duplicate assignments (should not happen with proper validation)
  const deviceAddresses = Object.values(assignments).map(a => a.deviceAddress);
  const duplicates = deviceAddresses.filter((address, index) => 
    deviceAddresses.indexOf(address) !== index
  );
  if (duplicates.length > 0) {
    return {
      isValid: false,
      errorMessage: 'Duplicate device assignments detected'
    };
  }

  return {
    isValid: true,
    warningMessage: warnings.length > 0 ? warnings.join('. ') : undefined
  };
};

/**
 * Estimate distance from RSSI (simplified formula)
 * Note: This is a rough estimation and can vary significantly based on environment
 */
export const estimateDistanceFromRSSI = (rssi: number, txPower: number = -59): number => {
  if (rssi >= txPower) {
    return 0.5; // Very close
  }
  
  // Simplified path loss formula: distance = 10^((txPower - rssi) / (10 * n))
  // where n is path loss exponent (2 for free space, 3-4 for indoor)
  const pathLossExponent = 3; // Indoor environment
  const distance = Math.pow(10, (txPower - rssi) / (10 * pathLossExponent));
  
  return Math.max(0.5, Math.min(distance, 100)); // Clamp between 0.5m and 100m
};

/**
 * Get signal strength category
 */
export const getSignalStrengthCategory = (rssi: number): {
  category: 'excellent' | 'good' | 'fair' | 'poor';
  description: string;
  color: string;
} => {
  if (rssi >= -50) {
    return { category: 'excellent', description: 'Excellent', color: 'green' };
  } else if (rssi >= -60) {
    return { category: 'good', description: 'Good', color: 'green' };
  } else if (rssi >= -70) {
    return { category: 'fair', description: 'Fair', color: 'yellow' };
  } else {
    return { category: 'poor', description: 'Poor', color: 'red' };
  }
};

/**
 * Get battery level category
 */
export const getBatteryLevelCategory = (battery: number): {
  category: 'excellent' | 'good' | 'fair' | 'poor';
  description: string;
  color: string;
} => {
  if (battery >= 80) {
    return { category: 'excellent', description: 'Excellent', color: 'green' };
  } else if (battery >= 60) {
    return { category: 'good', description: 'Good', color: 'green' };
  } else if (battery >= 40) {
    return { category: 'fair', description: 'Fair', color: 'yellow' };
  } else {
    return { category: 'poor', description: 'Poor', color: 'red' };
  }
};

/**
 * Generate user-friendly error messages
 */
export const getValidationErrorMessage = (
  device: DeviceItem,
  dropZone: DropZone,
  result: ValidationResult
): string => {
  if (result.isValid) return '';

  const deviceName = device.name || device.label || `Device ${device.address}`;
  const targetName = dropZone.type === 'timer' ? 'Timer Slot' : `Target ${dropZone.targetNumber}`;

  return `Cannot assign ${deviceName} to ${targetName}: ${result.errorMessage}`;
};

/**
 * Generate suggestions for improving setup
 */
export const getSetupSuggestions = (
  assignments: Record<string, Assignment>,
  dropZones: DropZone[],
  availableDevices: DeviceItem[]
): string[] => {
  const suggestions: string[] = [];

  // Check for devices with low battery
  const lowBatteryDevices = availableDevices.filter(
    device => device.battery && device.battery < 30
  );
  if (lowBatteryDevices.length > 0) {
    suggestions.push(`${lowBatteryDevices.length} device(s) have low battery levels and should be recharged`);
  }

  // Check for devices with poor signal
  const poorSignalDevices = availableDevices.filter(
    device => device.rssi && device.rssi < -70
  );
  if (poorSignalDevices.length > 0) {
    suggestions.push(`${poorSignalDevices.length} device(s) have poor signal strength - consider relocating bridge or devices`);
  }

  // Check for unassigned targets
  const targetZones = dropZones.filter(zone => zone.type === 'target');
  const assignedTargets = Object.values(assignments).filter(
    assignment => assignment.targetAssignment.startsWith('target-')
  );
  
  if (assignedTargets.length === 0) {
    suggestions.push('Assign sensors to targets to enable impact detection');
  } else if (assignedTargets.length < targetZones.length) {
    suggestions.push(`${targetZones.length - assignedTargets.length} target(s) still need sensor assignment`);
  }

  // Check for timer assignment
  const timerAssigned = Object.values(assignments).some(
    assignment => assignment.targetAssignment === 'timer'
  );
  if (!timerAssigned) {
    suggestions.push('Assign a timer device to enable match timing');
  }

  return suggestions;
};