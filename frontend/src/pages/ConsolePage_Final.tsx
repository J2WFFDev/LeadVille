/**
 * Console logs page component - Updated per user feedback
 * 1. Fixed source name display in header 
 * 2. Removed Pause button (not needed)
 * 3. Increased log limit to show more history since startup
 */

import { useState } from 'react';
import { useWebSocketLogs } from '../hooks/useWebSocketLogs';

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
    if (cleanSource.includes('bridge_console_')) {
      cleanSource = 'Bridge';
    } else if (cleanSource.toLowerCase().includes('bt50')) {
      cleanSource = 'BT50';
    } else if (cleanSource.toLowerCase().includes('amg')) {
      cleanSource = 'AMG';
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

export const ConsolePage = () => {
  // Increased log limit to show more history since startup
  const { logs, isConnected, connectionStatus } = useWebSocketLogs(2000);
  const [searchFilter, setSearchFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');

  const filteredLogs = logs.filter(log => {
    const matchesSearch = searchFilter === '' || 
      log.message.toLowerCase().includes(searchFilter.toLowerCase()) ||
      log.source.toLowerCase().includes(searchFilter.toLowerCase());
    
    const matchesLevel = levelFilter === 'ALL' || log.level === levelFilter;
    
    return matchesSearch && matchesLevel;
  });

  // Get primary source for header display - improved logic
  const getPrimarySource = () => {
    if (logs.length === 0) return 'Waiting for logs...';
    
    // Get all unique sources from recent logs
    const recentSources = logs.slice(-20).map(log => {
      if (log.source.includes('bridge_console_')) return 'Bridge';
      if (log.source.toLowerCase().includes('bt50')) return 'BT50';
      if (log.source.toLowerCase().includes('amg')) return 'AMG';
      if (log.source.toLowerCase().includes('fastapi')) return 'FastAPI';
      if (log.source.toLowerCase().includes('websocket')) return 'WebSocket';
      return log.source.length > 15 ? log.source.substring(0, 15) + '...' : log.source;
    });
    
    const uniqueSources = [...new Set(recentSources)];
    
    if (uniqueSources.length === 0) {
      return 'System';
    } else if (uniqueSources.length === 1) {
      return uniqueSources[0];
    } else if (uniqueSources.length <= 3) {
      return uniqueSources.join(', ');
    } else {
      return `${uniqueSources.slice(0, 2).join(', ')} +${uniqueSources.length - 2} more`;
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
              🖥️ System Console
            </h1>
            <p style={{ color: '#6b7280', fontSize: '14px', margin: '4px 0 0 0' }}>
              Real-time log streaming from LeadVille Bridge
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

          {/* Removed Pause button - not needed for log viewing */}
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
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
                <p style={{ fontSize: '18px', margin: '0 0 8px 0' }}>No logs to display</p>
                <p style={{ fontSize: '14px', margin: 0 }}>
                  {logs.length === 0 
                    ? 'Waiting for log entries...' 
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
          <span>WebSocket: ws://192.168.1.124:8001/ws/logs</span>
          <span>Live streaming • Manual scroll</span>
        </div>
      </div>
    </div>
  );
};