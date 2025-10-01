/**
 * Live Log page component - Merged timer and impact sensor events
 * Based on ConsolePage with timer-sensor database integration
 * Shows merged timer and impact sensor events in real-time
 */

import { useState, useEffect } from 'react';
import { endpointConfig } from '../config/endpoints';

interface LogEntryProps {
  log: {
    timestamp: string;
    level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
    source: string;
    message: string;
    raw?: string;
  };
}

const LogEntry = ({ log }: LogEntryProps) => {
  const getRowStyle = () => {
    switch (log.level) {
      case 'ERROR':
        return {
          backgroundColor: '#fef2f2',
          borderLeft: '4px solid #ef4444'
        };
      case 'WARNING':
        return {
          backgroundColor: '#fefce8',
          borderLeft: '4px solid #eab308'
        };
      case 'DEBUG':
        return {
          backgroundColor: '#faf5ff',
          borderLeft: '4px solid #a855f7'
        };
      case 'INFO':
      default:
        return {
          backgroundColor: '#ffffff',
          borderLeft: '4px solid #3b82f6'
        };
    }
  };

  const getLevelBadgeStyle = () => {
    switch (log.level) {
      case 'ERROR':
        return {
          backgroundColor: '#fecaca',
          color: '#991b1b',
        };
      case 'WARNING':
        return {
          backgroundColor: '#fef3c7',
          color: '#92400e',
        };
      case 'DEBUG':
        return {
          backgroundColor: '#e9d5ff',
          color: '#6b21a8',
        };
      case 'INFO':
      default:
        return {
          backgroundColor: '#dbeafe',
          color: '#1e40af',
        };
    }
  };

  const getSourceTag = () => {
    let cleanSource = log.source;
    if (cleanSource.includes('AMG')) {
      cleanSource = 'AMG_TIMER';
    } else if (cleanSource.toLowerCase().includes('bridge')) {
      cleanSource = 'Bridge';
    } else if (cleanSource.toLowerCase().includes('impact')) {
      cleanSource = 'Impact';
    } else if (cleanSource.toLowerCase().includes('sensor')) {
      cleanSource = 'Sensor';
    }
    
    if (cleanSource.length > 12) {
      cleanSource = cleanSource.substring(0, 12) + '...';
    }
    
    return cleanSource;
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        fractionalSecondDigits: 3
      });
    } catch {
      return timestamp.slice(-12);
    }
  };

  return (
    <tr 
      style={{
        ...getRowStyle(),
        borderBottom: '1px solid #e5e7eb'
      }}
      className="hover:opacity-80 transition-all"
    >
      <td 
        style={{
          width: '130px',
          padding: '8px 12px',
          fontSize: '11px',
          fontFamily: 'monospace',
          color: '#4b5563',
          borderRight: '1px solid #d1d5db',
          backgroundColor: '#f9fafb'
        }}
      >
        {formatTimestamp(log.timestamp)}
      </td>
      <td 
        style={{
          width: '80px',
          padding: '8px 12px',
          borderRight: '1px solid #d1d5db',
          backgroundColor: '#f9fafb'
        }}
      >
        <span 
          style={{
            ...getLevelBadgeStyle(),
            padding: '4px 8px',
            fontSize: '10px',
            fontWeight: 'bold',
            borderRadius: '4px'
          }}
        >
          {log.level}
        </span>
      </td>
      <td 
        style={{
          padding: '8px 12px',
          fontSize: '12px',
          color: '#1f2937'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start' }}>
          <span 
            style={{
              backgroundColor: '#e5e7eb',
              color: '#374151',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: '500',
              marginRight: '8px',
              flexShrink: 0
            }}
          >
            {getSourceTag()}
          </span>
          <span style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
            {log.message}
          </span>
        </div>
      </td>
    </tr>
  );
};

export const LiveLogPage = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [searchFilter, setSearchFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [isRestarting, setIsRestarting] = useState(false);

  // Load merged timer and sensor data from shot_log database view
  const loadMergedData = async () => {
    try {
      // Get data from shot_log database view endpoint
      console.log('Attempting to fetch from shot-log API...');
      const shotLogUrl = `${endpointConfig.getApiUrl()}/shot-log?limit=100`;
      console.log('Using shot-log URL:', shotLogUrl);
      const response = await fetch(shotLogUrl);
      console.log('Shot-log API response status:', response.status, response.statusText);
      
      if (response.ok) {
        const data = await response.json();
        const logs = data.logs || [];
        
        console.log('Successfully fetched shot-log data:', data.count, 'records');
        // The backend already formats the data properly, so we can use it directly
        setLogs(logs);
        setIsConnected(true);
        setConnectionStatus(`Connected to shot_log view (${data.count} records)`);
      } else {
        console.error('Shot-log API failed with status:', response.status);
        // Fallback to regular logs but filter for timer/sensor context
        const fallbackUrl = `${endpointConfig.getApiUrl()}/logs?limit=100`;
        console.log('Trying fallback URL:', fallbackUrl);
        const fallbackResponse = await fetch(fallbackUrl);
        if (fallbackResponse.ok) {
          const logs = await fallbackResponse.json();
          const timerSensorLogs = logs.filter((log: any) => 
            log.message.toLowerCase().includes('shot') ||
            log.message.toLowerCase().includes('timer') ||
            log.message.toLowerCase().includes('impact') ||
            log.message.toLowerCase().includes('string') ||
            log.message.toLowerCase().includes('amg')
          ).map((log: any) => ({
            timestamp: log.timestamp,
            level: log.level || 'INFO',
            source: log.source || 'System',
            message: enhanceLogMessage(log.message),
            raw: log.raw || JSON.stringify(log)
          }));
          setLogs(timerSensorLogs);
          setIsConnected(true);
          setConnectionStatus('Connected - filtered for timer/sensor events');
        } else {
          setIsConnected(false);
          setConnectionStatus('Failed to connect to API');
        }
      }
    } catch (error) {
      console.error('Failed to load merged data:', error);
      setIsConnected(false);
      setConnectionStatus('Network error: ' + error);
    }
  };

  // Enhance log messages to highlight timer/sensor information
  const enhanceLogMessage = (message: string) => {
    // Add emojis and formatting for timer/sensor events
    if (message.toLowerCase().includes('shot') && message.includes('time')) {
      return `🎯 ${message}`;
    } else if (message.toLowerCase().includes('string') && message.includes('final')) {
      return `⏹️ ${message}`;
    } else if (message.toLowerCase().includes('timer') && message.includes('start')) {
      return `🔫 ${message}`;
    } else if (message.toLowerCase().includes('impact')) {
      return `💥 ${message}`;
    } else if (message.toLowerCase().includes('amg')) {
      return `⏱️ ${message}`;
    }
    return message;
  };



  // Load data on component mount and set up refresh interval
  useEffect(() => {
    loadMergedData();
    
    // Refresh data every 5 seconds
    const interval = setInterval(loadMergedData, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const filteredLogs = logs.filter(log => {
    const matchesSearch = searchFilter === '' || 
      log.message.toLowerCase().includes(searchFilter.toLowerCase()) ||
      log.source.toLowerCase().includes(searchFilter.toLowerCase());
    
    const matchesLevel = levelFilter === 'ALL' || log.level === levelFilter;
    
    return matchesSearch && matchesLevel;
  });

  // Get primary source for header display
  const getPrimarySource = () => {
    if (logs.length === 0) return 'Waiting for merged data...';
    
    const recentSources = logs.slice(-20).map(log => log.source);
    const uniqueSources = [...new Set(recentSources)];
    
    if (uniqueSources.length === 0) {
      return 'Timer & Impact System';
    } else if (uniqueSources.length === 1) {
      return uniqueSources[0];
    } else if (uniqueSources.length <= 3) {
      return uniqueSources.join(', ');
    } else {
      return `${uniqueSources.slice(0, 2).join(', ')} +${uniqueSources.length - 2} more`;
    }
  };

  const handleRestartService = async () => {
    setIsRestarting(true);
    try {
      // Attempt to refresh the data
      await loadMergedData();
      alert('Data refreshed successfully!');
      setTimeout(() => {
        setIsRestarting(false);
      }, 2000);
    } catch (error) {
      alert(`Failed to refresh data: ${error}`);
      setIsRestarting(false);
    }
  };

  return (
    <div 
      style={{ 
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#f3f4f6'
      }}
    >
      {/* Fixed Header */}
      <div 
        style={{
          backgroundColor: '#ffffff',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          borderBottom: '1px solid #e5e7eb',
          padding: '16px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#1f2937', margin: 0 }}>
              📊 Live System Log
            </h1>
            <p style={{ color: '#6b7280', fontSize: '14px', margin: '4px 0 0 0' }}>
              Merged timer and impact sensor events in real-time
            </p>
            <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: '#6b7280', marginRight: '8px' }}>
                Source:
              </span>
              <span 
                style={{
                  backgroundColor: '#dbeafe',
                  color: '#1e40af',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: '500'
                }}
              >
                {getPrimarySource()}
              </span>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div 
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                fontWeight: '600',
                fontSize: '14px',
                ...(isConnected 
                  ? { color: '#065f46', backgroundColor: '#d1fae5', border: '1px solid #10b981' }
                  : { color: '#991b1b', backgroundColor: '#fee2e2', border: '1px solid #ef4444' }
                )
              }}
            >
              {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginLeft: '12px' }}>
              {connectionStatus}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ flex: '1 1 256px', marginRight: '16px' }}>
            <input
              type="text"
              placeholder="Search logs..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>

          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
              marginRight: '8px'
            }}
          >
            <option value="ALL">All Levels</option>
            <option value="ERROR">Errors Only</option>
            <option value="WARNING">Warnings Only</option>
            <option value="INFO">Info Only</option>
            <option value="DEBUG">Debug Only</option>
          </select>

          {/* Refresh Data Button */}
          <button
            onClick={handleRestartService}
            disabled={isRestarting}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              fontWeight: '600',
              fontSize: '14px',
              border: 'none',
              cursor: isRestarting ? 'not-allowed' : 'pointer',
              backgroundColor: isRestarting ? '#d1d5db' : '#10b981',
              color: isRestarting ? '#6b7280' : '#ffffff',
              marginLeft: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            {isRestarting ? (
              <>
                <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⟳</span>
                Refreshing...
              </>
            ) : (
              <>🔄 Refresh Data</>
            )}
          </button>
        </div>

        <div style={{ display: 'flex', fontSize: '14px', color: '#6b7280' }}>
          <span style={{ marginRight: '24px' }}>Total: <strong>{logs.length}</strong></span>
          <span style={{ marginRight: '24px' }}>Filtered: <strong>{filteredLogs.length}</strong></span>
          <span style={{ marginRight: '24px' }}>Errors: <strong>{logs.filter(l => l.level === 'ERROR').length}</strong></span>
          <span style={{ marginRight: '24px' }}>Warnings: <strong>{logs.filter(l => l.level === 'WARNING').length}</strong></span>
          <span>Since startup</span>
        </div>
      </div>

      {/* Logs Container - SCROLLABLE (No Auto-scroll) */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <div 
          style={{ 
            height: '100%', 
            overflow: 'auto', 
            backgroundColor: '#ffffff' 
          }}
        >
          {filteredLogs.length === 0 ? (
            <div 
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                height: '100%', 
                color: '#6b7280' 
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
                <p style={{ fontSize: '18px', margin: '0 0 8px 0' }}>No merged events to display</p>
                <p style={{ fontSize: '14px', margin: 0 }}>
                  {logs.length === 0 
                    ? 'Loading timer and impact sensor data...' 
                    : 'Try adjusting your filters'
                  }
                </p>
              </div>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead 
                style={{ 
                  position: 'sticky', 
                  top: 0, 
                  backgroundColor: '#d1d5db', 
                  borderBottom: '2px solid #9ca3af',
                  zIndex: 10
                }}
              >
                <tr>
                  <th 
                    style={{
                      width: '130px',
                      padding: '12px',
                      textAlign: 'left',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      textTransform: 'uppercase',
                      borderRight: '1px solid #9ca3af'
                    }}
                  >
                    Timestamp
                  </th>
                  <th 
                    style={{
                      width: '80px',
                      padding: '12px',
                      textAlign: 'left',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      textTransform: 'uppercase',
                      borderRight: '1px solid #9ca3af'
                    }}
                  >
                    Level
                  </th>
                  <th 
                    style={{
                      padding: '12px',
                      textAlign: 'left',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      textTransform: 'uppercase'
                    }}
                  >
                    Message
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log, index) => (
                  <LogEntry 
                    key={`${log.timestamp}-${index}`} 
                    log={log} 
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Fixed Footer */}
      <div 
        style={{
          backgroundColor: '#e5e7eb',
          borderTop: '1px solid #d1d5db',
          padding: '8px 16px',
          fontSize: '12px',
          color: '#6b7280'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>API: {endpointConfig.getApiUrl()}/shot-log</span>
          <span>Live streaming • Manual scroll</span>
        </div>
      </div>
    </div>
  );
};