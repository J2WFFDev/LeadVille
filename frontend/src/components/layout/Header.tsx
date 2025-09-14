/**
 * Header component for LeadVille Bridge interface
 */

import { useWebSocketConnection } from '../../hooks/useWebSocket';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ 
  title = "LeadVille Bridge",
  subtitle = "Impact Sensor & Timer System"
}) => {
  const { isConnected, connectionState } = useWebSocketConnection();

  const getConnectionStatusClass = () => {
    switch (connectionState) {
      case 'connected':
        return 'status-connected';
      case 'connecting':
        return 'status-ready';
      case 'disconnected':
      case 'closed':
        return 'status-disconnected';
      default:
        return 'status-ready';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionState) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'disconnected':
      case 'closed':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  return (
    <header className="bg-gradient-to-r from-leadville-primary to-leadville-secondary text-white shadow-lg">
      <div className="container mx-auto px-6 py-6">
        <div className="flex items-center justify-between">
          {/* Title Section */}
          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-bold mb-2">{title}</h1>
            <p className="text-lg md:text-xl opacity-90">{subtitle}</p>
          </div>

          {/* Connection Status */}
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm font-medium opacity-80">WebSocket Status</div>
              <div className={`inline-flex items-center px-3 py-2 rounded-lg border text-sm font-semibold ${getConnectionStatusClass()}`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                }`}></div>
                {getConnectionStatusText()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};