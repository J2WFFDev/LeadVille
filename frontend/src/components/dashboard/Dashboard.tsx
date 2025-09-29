/**
 * Main dashboard component combining all panels
 * Responsive layout optimized for kiosk displays
 */

import { StatusPanel } from './StatusPanel';
import { TimerPanel } from './TimerPanel';
import { SensorPanel } from './SensorPanel';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
          LeadVille Bridge Dashboard
        </h1>
        <p className="text-gray-600">
          Real-time monitoring of timer events and impact sensor data
        </p>
      </div>

      {/* Dashboard Grid - Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Timer Panel - Takes priority on smaller screens */}
        <div className="lg:col-span-1">
          <TimerPanel />
        </div>

        {/* Sensor Panel */}
        <div className="lg:col-span-1">
          <SensorPanel />
        </div>

        {/* Status Panel */}
        <div className="lg:col-span-2 xl:col-span-1">
          <StatusPanel />
        </div>
      </div>

      {/* Quick Actions - Kiosk Friendly */}
      <div className="panel">
        <div className="panel-header">
          Quick Actions
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="btn-primary">
            🎯 Start Session
          </button>
          <Link to="/device-assignment" className="btn-secondary">
            🔧 Device Assignment
          </Link>
          <button className="btn-secondary">
            🔄 Reconnect
          </button>
          <button className="btn-danger">
            ⏹️ Emergency Stop
          </button>
        </div>
      </div>
    </div>
  );
};