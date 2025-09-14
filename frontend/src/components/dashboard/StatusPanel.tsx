/**
 * Status panel component showing system health and connection status
 */

import { useHealthStatus, useWebSocketConnection } from '../../hooks/useWebSocket';

interface StatusItemProps {
  label: string;
  value: string;
  status: 'connected' | 'disconnected' | 'ready' | 'active' | 'unknown';
}

const StatusItem: React.FC<StatusItemProps> = ({ label, value, status }) => {
  const getStatusClass = () => {
    switch (status) {
      case 'connected':
        return 'status-connected';
      case 'disconnected':
        return 'status-disconnected';
      case 'ready':
        return 'status-ready';
      case 'active':
        return 'status-active';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  return (
    <div className="flex items-center justify-between p-4 rounded-lg border">
      <div className="font-medium text-gray-700">{label}:</div>
      <div className={`px-3 py-2 rounded-lg border text-sm font-semibold ${getStatusClass()}`}>
        {value}
      </div>
    </div>
  );
};

export const StatusPanel: React.FC = () => {
  const { isConnected, connectionState } = useWebSocketConnection();
  const { connectionStatus, rssi, uptime } = useHealthStatus();

  const formatUptime = (seconds: number | null): string => {
    if (!seconds) return '--';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const getWebSocketStatus = (): 'connected' | 'disconnected' | 'ready' => {
    if (isConnected) return 'connected';
    if (connectionState === 'connecting') return 'ready';
    return 'disconnected';
  };

  const getDeviceStatus = (): 'connected' | 'disconnected' | 'unknown' => {
    if (!connectionStatus) return 'unknown';
    return connectionStatus.toLowerCase() === 'connected' ? 'connected' : 'disconnected';
  };

  return (
    <div className="panel">
      <div className="panel-header">
        System Status
      </div>
      
      <div className="space-y-4">
        <StatusItem
          label="WebSocket"
          value={isConnected ? 'Connected' : connectionState.charAt(0).toUpperCase() + connectionState.slice(1)}
          status={getWebSocketStatus()}
        />
        
        <StatusItem
          label="Device Connection"
          value={connectionStatus || 'Unknown'}
          status={getDeviceStatus()}
        />
        
        <StatusItem
          label="Signal Strength"
          value={rssi ? `${rssi} dBm` : '--'}
          status={rssi && rssi > -70 ? 'connected' : rssi ? 'ready' : 'unknown'}
        />
        
        <StatusItem
          label="System Uptime"
          value={formatUptime(uptime)}
          status={uptime ? 'active' : 'unknown'}
        />
      </div>
    </div>
  );
};