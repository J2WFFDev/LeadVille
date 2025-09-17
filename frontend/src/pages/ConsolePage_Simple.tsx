/**
 * Console logs page component with real-time WebSocket streaming
 * Simplified version with basic Tailwind classes
 */

import { useState, useEffect, useRef } from 'react';
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
  const getRowClass = () => {
    switch (log.level) {
      case 'ERROR':
        return 'bg-red-100 hover:bg-red-200 border-l-4 border-red-500';
      case 'WARNING':
        return 'bg-yellow-100 hover:bg-yellow-200 border-l-4 border-yellow-500';
      case 'DEBUG':
        return 'bg-purple-100 hover:bg-purple-200 border-l-4 border-purple-500';
      case 'INFO':
      default:
        return 'bg-white hover:bg-gray-100 border-l-4 border-blue-500';
    }
  };

  const getLevelBadgeClass = () => {
    switch (log.level) {
      case 'ERROR':
        return 'bg-red-200 text-red-800 px-2 py-1 text-xs font-bold rounded';
      case 'WARNING':
        return 'bg-yellow-200 text-yellow-800 px-2 py-1 text-xs font-bold rounded';
      case 'DEBUG':
        return 'bg-purple-200 text-purple-800 px-2 py-1 text-xs font-bold rounded';
      case 'INFO':
      default:
        return 'bg-blue-200 text-blue-800 px-2 py-1 text-xs font-bold rounded';
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
    <tr className={`${getRowClass()} transition-colors border-b border-gray-200`}>
      <td className="w-32 px-3 py-2 text-xs font-mono text-gray-600 border-r border-gray-300 bg-gray-100">
        {formatTimestamp(log.timestamp)}
      </td>
      <td className="w-20 px-3 py-2 border-r border-gray-300 bg-gray-100">
        <span className={getLevelBadgeClass()}>
          {log.level}
        </span>
      </td>
      <td className="px-3 py-2 text-xs text-gray-800">
        <div className="flex items-start">
          <span className="bg-gray-200 text-gray-700 px-2 py-1 rounded text-xs font-medium mr-2">
            {getSourceTag()}
          </span>
          <span className="font-mono">
            {log.message}
          </span>
        </div>
      </td>
    </tr>
  );
};

export const ConsolePage = () => {
  const { logs, isConnected, connectionStatus, clearLogs, pauseLogging, resumeLogging } = useWebSocketLogs(500);
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter(log => {
    const matchesSearch = searchFilter === '' || 
      log.message.toLowerCase().includes(searchFilter.toLowerCase()) ||
      log.source.toLowerCase().includes(searchFilter.toLowerCase());
    
    const matchesLevel = levelFilter === 'ALL' || log.level === levelFilter;
    
    return matchesSearch && matchesLevel;
  });

  const handlePauseToggle = () => {
    if (isPaused) {
      resumeLogging();
      setIsPaused(false);
    } else {
      pauseLogging();
      setIsPaused(true);
    }
  };

  const getConnectionStatusClass = () => {
    if (isConnected) return 'text-green-700 bg-green-200 border border-green-400';
    return 'text-red-700 bg-red-200 border border-red-400';
  };

  return (
    <div style={{ height: '100vh' }} className="flex flex-col bg-gray-100">
      {/* Fixed Header */}
      <div className="bg-white shadow border-b p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              🖥️ System Console
            </h1>
            <p className="text-gray-600 text-sm">
              Real-time log streaming from LeadVille Bridge
            </p>
          </div>
          
          <div className="flex items-center">
            <div className={`px-3 py-2 rounded font-semibold text-sm ${getConnectionStatusClass()}`}>
              {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </div>
            <div className="text-xs text-gray-500 ml-3">
              {connectionStatus}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center mb-3">
          <div className="flex-1 min-w-64 mr-4">
            <input
              type="text"
              placeholder="Search logs..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
            />
          </div>

          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded text-sm mr-2"
          >
            <option value="ALL">All Levels</option>
            <option value="ERROR">Errors Only</option>
            <option value="WARNING">Warnings Only</option>
            <option value="INFO">Info Only</option>
            <option value="DEBUG">Debug Only</option>
          </select>

          <button
            onClick={handlePauseToggle}
            className={`px-4 py-2 rounded font-semibold text-sm mr-2 ${
              isPaused 
                ? 'bg-green-500 text-white hover:bg-green-600' 
                : 'bg-yellow-500 text-white hover:bg-yellow-600'
            }`}
          >
            {isPaused ? '▶️ Resume' : '⏸️ Pause'}
          </button>

          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-4 py-2 rounded font-semibold text-sm mr-2 ${
              autoScroll 
                ? 'bg-blue-500 text-white hover:bg-blue-600' 
                : 'bg-gray-500 text-white hover:bg-gray-600'
            }`}
          >
            {autoScroll ? '📌 Auto-scroll: ON' : '📌 Auto-scroll: OFF'}
          </button>

          <button
            onClick={clearLogs}
            className="px-4 py-2 bg-red-500 text-white rounded font-semibold hover:bg-red-600 text-sm"
          >
            🗑️ Clear
          </button>
        </div>

        <div className="flex text-sm text-gray-600">
          <span className="mr-6">Total: <strong>{logs.length}</strong></span>
          <span className="mr-6">Filtered: <strong>{filteredLogs.length}</strong></span>
          <span className="mr-6">Errors: <strong>{logs.filter(l => l.level === 'ERROR').length}</strong></span>
          <span>Warnings: <strong>{logs.filter(l => l.level === 'WARNING').length}</strong></span>
        </div>
      </div>

      {/* Logs Container - FIXED HEIGHT */}
      <div className="flex-1" style={{ minHeight: 0 }}>
        <div className="h-full overflow-auto bg-white">
          {filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <div className="text-4xl mb-4">📋</div>
                <p className="text-lg">No logs to display</p>
                <p className="text-sm">
                  {logs.length === 0 
                    ? 'Waiting for log entries...' 
                    : 'Try adjusting your filters'
                  }
                </p>
              </div>
            </div>
          ) : (
            <table className="w-full">
              <thead className="sticky top-0 bg-gray-300 border-b-2 border-gray-400">
                <tr>
                  <th className="w-32 px-3 py-3 text-left text-xs font-bold text-gray-800 uppercase border-r border-gray-400">
                    Timestamp
                  </th>
                  <th className="w-20 px-3 py-3 text-left text-xs font-bold text-gray-800 uppercase border-r border-gray-400">
                    Level
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-bold text-gray-800 uppercase">
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
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Fixed Footer */}
      <div className="bg-gray-200 border-t px-4 py-2 text-xs text-gray-600">
        <div className="flex justify-between items-center">
          <span>WebSocket: ws://192.168.1.124:8001/ws/logs</span>
          <span>
            {isPaused ? 'Logging paused' : 'Live streaming'} • 
            Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
          </span>
        </div>
      </div>
    </div>
  );
};