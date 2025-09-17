/**
 * Console logs page component with real-time WebSocket streaming
 * Redesigned with proper nested scrolling and source integration
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
        return 'bg-red-50 hover:bg-red-100 border-l-4 border-l-red-500';
      case 'WARNING':
        return 'bg-yellow-50 hover:bg-yellow-100 border-l-4 border-l-yellow-500';
      case 'DEBUG':
        return 'bg-purple-50 hover:bg-purple-100 border l-4 border-l-purple-500';
      case 'INFO':
      default:
        return 'bg-white hover:bg-gray-50 border-l-4 border-l-blue-500';
    }
  };

  const getLevelBadgeClass = () => {
    switch (log.level) {
      case 'ERROR':
        return 'bg-red-100 text-red-700 px-2 py-1 text-xs font-bold rounded';
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-700 px-2 py-1 text-xs font-bold rounded';
      case 'DEBUG':
        return 'bg-purple-100 text-purple-700 px-2 py-1 text-xs font-bold rounded';
      case 'INFO':
      default:
        return 'bg-blue-100 text-blue-700 px-2 py-1 text-xs font-bold rounded';
    }
  };

  const getSourceTag = () => {
    // Clean up source names for display
    let cleanSource = log.source;
    if (cleanSource.includes('bridge_console_')) {
      cleanSource = 'Bridge';
    } else if (cleanSource.toLowerCase().includes('bt50')) {
      cleanSource = 'BT50Sensor';
    } else if (cleanSource.toLowerCase().includes('amg')) {
      cleanSource = 'AMGTimer';
    }
    
    // Truncate if still too long
    if (cleanSource.length > 12) {
      cleanSource = cleanSource.substring(0, 12) + '…';
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
    <tr className={`${getRowClass()} transition-colors duration-150 border-b border-gray-100`}>
      <td className="w-32 px-3 py-2 text-xs font-mono text-gray-600 border-r border-gray-200 bg-gray-50">
        {formatTimestamp(log.timestamp)}
      </td>
      <td className="w-20 px-3 py-2 border-r border-gray-200 bg-gray-50">
        <span className={getLevelBadgeClass()}>
          {log.level}
        </span>
      </td>
      <td className="px-3 py-2 text-xs text-gray-800">
        <div className="flex items-start gap-2">
          <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs font-medium shrink-0">
            {getSourceTag()}
          </span>
          <span className="font-mono leading-relaxed break-words">
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

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Filter logs based on search and level
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
    if (isConnected) return 'text-green-600 bg-green-100 border border-green-300';
    return 'text-red-600 bg-red-100 border border-red-300';
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Fixed Header - Controls */}
      <div className="flex-shrink-0 bg-white shadow-sm border-b p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              🖥️ System Console
            </h1>
            <p className="text-gray-600 text-sm">
              Real-time log streaming from LeadVille Bridge
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className={`px-3 py-2 rounded-lg font-semibold text-sm ${getConnectionStatusClass()}`}>
              {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </div>
            <div className="text-xs text-gray-500">
              {connectionStatus}
            </div>
          </div>
        </div>

        {/* Controls Row */}
        <div className="flex flex-wrap items-center gap-4 mb-3">
          {/* Search */}
          <div className="flex-1 min-w-64">
            <input
              type="text"
              placeholder="Search logs..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          {/* Level Filter */}
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          >
            <option value="ALL">All Levels</option>
            <option value="ERROR">Errors Only</option>
            <option value="WARNING">Warnings Only</option>
            <option value="INFO">Info Only</option>
            <option value="DEBUG">Debug Only</option>
          </select>

          {/* Control Buttons */}
          <button
            onClick={handlePauseToggle}
            className={`px-4 py-2 rounded-lg font-semibold text-sm ${
              isPaused 
                ? 'bg-green-500 text-white hover:bg-green-600' 
                : 'bg-yellow-500 text-white hover:bg-yellow-600'
            }`}
          >
            {isPaused ? '▶️ Resume' : '⏸️ Pause'}
          </button>

          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-4 py-2 rounded-lg font-semibold text-sm ${
              autoScroll 
                ? 'bg-blue-500 text-white hover:bg-blue-600' 
                : 'bg-gray-500 text-white hover:bg-gray-600'
            }`}
          >
            {autoScroll ? '📌 Auto-scroll: ON' : '📌 Auto-scroll: OFF'}
          </button>

          <button
            onClick={clearLogs}
            className="px-4 py-2 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 text-sm"
          >
            🗑️ Clear
          </button>
        </div>

        {/* Stats */}
        <div className="flex gap-6 text-sm text-gray-600">
          <span>Total: <strong>{logs.length}</strong></span>
          <span>Filtered: <strong>{filteredLogs.length}</strong></span>
          <span>Errors: <strong>{logs.filter(l => l.level === 'ERROR').length}</strong></span>
          <span>Warnings: <strong>{logs.filter(l => l.level === 'WARNING').length}</strong></span>
        </div>
      </div>

      {/* Logs Container - This is the key fix! */}
      <div className="flex-1 min-h-0 bg-white border-t">
        <div className="h-full overflow-auto">
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
            <table className="w-full table-fixed">
              <thead className="sticky top-0 bg-gray-200 border-b-2 border-gray-300 shadow-sm">
                <tr>
                  <th className="w-32 px-3 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wide border-r border-gray-300">
                    Timestamp
                  </th>
                  <th className="w-20 px-3 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wide border-r border-gray-300">
                    Level
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wide">
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
      <div className="flex-shrink-0 bg-gray-100 border-t px-4 py-2 text-xs text-gray-600">
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