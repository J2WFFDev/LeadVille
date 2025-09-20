/**
 * Sensor panel component for BT50 impact sensor monitoring
 */

import { useWebSocketMessages } from '../../hooks/useWebSocket';

interface SensorData {
  acceleration?: number;
  impact_detected?: boolean;
  threshold?: number;
  calibration_status?: string;
}

export const SensorPanel: React.FC = () => {
  const { messages } = useWebSocketMessages();

  // Mock sensor data - in real implementation this would come from sensor-specific messages
  const sensorData: SensorData = {
    acceleration: 2.4,
    impact_detected: false,
    threshold: 10.0,
    calibration_status: 'calibrated'
  };

  const getCalibrationStatusClass = () => {
    switch (sensorData.calibration_status) {
      case 'calibrated':
        return 'status-connected';
      case 'calibrating':
        return 'status-ready';
      case 'not_calibrated':
        return 'status-disconnected';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  const getImpactStatusClass = () => {
    return sensorData.impact_detected ? 'status-disconnected' : 'status-connected';
  };

  return (
    <div className="panel">
      <div className="panel-header">
        Impact Sensor Monitor
      </div>
      
      <div className="space-y-6">
        {/* Current Acceleration Reading */}
        <div className="text-center">
          <div className="text-5xl md:text-6xl font-mono font-bold text-gray-800 mb-2">
            {sensorData.acceleration?.toFixed(1) || '--'} <span className="text-3xl text-gray-500">g</span>
          </div>
          <div className="text-sm text-gray-600">Current Acceleration</div>
        </div>

        {/* Status Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-sm font-medium text-gray-600 mb-2">Calibration Status</div>
            <div className={`px-4 py-3 rounded-lg border text-sm font-semibold ${getCalibrationStatusClass()}`}>
              {(sensorData.calibration_status?.charAt(0).toUpperCase() || '') + 
               (sensorData.calibration_status?.slice(1).replace('_', ' ') || 'Unknown')}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-sm font-medium text-gray-600 mb-2">Impact Detection</div>
            <div className={`px-4 py-3 rounded-lg border text-sm font-semibold ${getImpactStatusClass()}`}>
              {sensorData.impact_detected ? '🔴 Impact!' : '🟢 Normal'}
            </div>
          </div>
        </div>

        {/* Threshold Settings */}
        <div className="bg-gray-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-700">Detection Threshold</span>
            <span className="text-lg font-mono font-bold text-leadville-primary">
              {sensorData.threshold?.toFixed(1) || '--'} g
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-leadville-primary h-2 rounded-full transition-all duration-300"
              style={{ 
                width: `${Math.min(100, ((sensorData.acceleration || 0) / (sensorData.threshold || 10)) * 100)}%` 
              }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0g</span>
            <span>{sensorData.threshold}g</span>
          </div>
        </div>

        {/* Recent Messages */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">WebSocket Activity</h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {messages.slice(-3).reverse().map((message, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-100 rounded-lg text-sm">
                <div className="font-medium text-gray-700">
                  {message.type.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
            {messages.length === 0 && (
              <div className="text-center text-gray-500 py-4">
                No messages received
              </div>
            )}
          </div>
        </div>

        {/* Control Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <button className="btn-primary">
            Calibrate Sensor
          </button>
          <button className="btn-secondary">
            Reset Baseline
          </button>
        </div>
      </div>
    </div>
  );
};