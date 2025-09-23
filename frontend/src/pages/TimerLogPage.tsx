/**
 * Live Timer Log Page - Real-time timer events in console log format
 * Shows timer events (START, SHOT, STOP) with same layout as console page
 */

import React, { useState, useEffect, useRef } from 'react';

interface TimerLogEntry {
  id: number;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  source: string;
  message: string;
  event_type?: string;
  shot_number?: number;
  shot_time?: number;
  string_total_time?: number;
  timer_device?: string;
}

interface TimerLogEntryProps {
  log: TimerLogEntry;
}

const TimerLogEntry = ({ log }: TimerLogEntryProps) => {
  const getLevelBadgeClass = () => {
    switch (log.level) {
      case 'ERROR':
        return 'bg-red-500 text-white px-2 py-1 rounded text-xs font-bold';
      case 'WARNING':
        return 'bg-yellow-500 text-white px-2 py-1 rounded text-xs font-bold';
      case 'DEBUG':
        return 'bg-purple-500 text-white px-2 py-1 rounded text-xs font-bold';
      case 'INFO':
      default:
        return 'bg-blue-500 text-white px-2 py-1 rounded text-xs font-bold';
    }
  };

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="px-4 py-2 text-sm font-mono text-gray-600 w-1/6 align-top">
        {log.timestamp}
      </td>
      <td className="px-4 py-2 w-1/12 align-top">
        <span className={getLevelBadgeClass()}>
          {log.level}
        </span>
      </td>
      <td className="px-4 py-2 text-sm align-top">
        <div className="flex items-center space-x-2 mb-1">
          <span className="text-blue-600 font-medium">{log.source}</span>
          {log.event_type && (
            <span className="px-1 py-0.5 bg-green-100 text-green-800 text-xs rounded">
              {log.event_type}
            </span>
          )}
          {log.shot_number && (
            <span className="px-1 py-0.5 bg-purple-100 text-purple-800 text-xs rounded">
              #{log.shot_number}
            </span>
          )}
        </div>
        <div className="text-gray-900 font-mono text-sm leading-relaxed">
          {log.message}
        </div>
        {(log.shot_time || log.string_total_time) && (
          <div className="mt-1 text-xs text-gray-500 space-x-3">
            {log.shot_time && (
              <span>Time: <strong>{log.shot_time.toFixed(2)}s</strong></span>
            )}
            {log.string_total_time && (
              <span>Total: <strong>{log.string_total_time.toFixed(2)}s</strong></span>
            )}
          </div>
        )}
      </td>
    </tr>
  );
};

const TimerLogPage = () => {
  const [logs, setLogs] = useState<TimerLogEntry[]>([]);
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connected' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket connection management
  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://${window.location.hostname}:8002/ws`;
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('📡 Timer Log WebSocket connected');
        setWsStatus('connected');
        
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('📡 Timer Log WebSocket disconnected');
        setWsStatus('disconnected');
        
        // Auto-reconnect after 3 seconds
        if (!reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsStatus('error');
      };
      
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setWsStatus('error');
    }
  };

  // Load merged data from backend API
  const loadMergedData = async () => {
    try {
      // Get recent events from the shot_log_simple view (merged timer + impact data)
      const response = await fetch(`http://${window.location.hostname}:8002/api/events/latest?limit=50`);
      if (response.ok) {
        const events = await response.json();
        const mergedLogs: TimerLogEntry[] = events.map((event: any) => ({
          id: event.log_id,
          timestamp: new Date(event.event_time).toLocaleString(),
          level: 'INFO',
          source: event.timer_device || 'Bridge',
          message: formatMergedEventMessage(event),
          event_type: event.event_type,
          shot_number: event.shot_number,
          shot_time: event.shot_time,
          string_total_time: event.string_total_time,
          timer_device: event.timer_device
        }));
        setLogs(mergedLogs);
      }
    } catch (error) {
      console.error('Failed to load merged data:', error);
    }
  };

  // Handle WebSocket messages for real-time updates
  const handleWebSocketMessage = (message: any) => {
    if (message.type === 'initial_data') {
      // Load merged data from API instead of just current string
      loadMergedData();
    } else if (message.type === 'timer_event' || message.type === 'impact_event') {
      // Add new merged event as log entry
      const newLog: TimerLogEntry = {
        id: message.data.log_id || Date.now(),
        timestamp: new Date().toLocaleString(),
        level: getEventLevel(message.data),
        source: message.data.timer_device || message.data.source || 'Bridge',
        message: formatMergedEventMessage(message.data),
        event_type: message.data.event_type,
        shot_number: message.data.shot_number,
        shot_time: message.data.shot_time,
        string_total_time: message.data.string_total_time,
        timer_device: message.data.timer_device
      };
      
      setLogs(prev => [newLog, ...prev].slice(0, 100)); // Keep last 100 entries
    }
  };

  // Format merged event into readable message (combines timer + impact data)
  const formatMergedEventMessage = (data: any) => {
    switch (data.event_type) {
      case 'START':
        return `🔫 Timer started - String of ${data.total_shots || 'unknown'} shots`;
      case 'SHOT':
        const rating = getRating(data.shot_time);
        return `🎯 Shot ${data.shot_number}: ${data.shot_time?.toFixed(2)}s (${rating}) | Target ${data.target || 'unknown'} | Sensor ${data.sensor || 'unknown'}`;
      case 'STOP':
        return `⏹️ String completed - Total time: ${data.string_total_time?.toFixed(2)}s | ${data.total_shots} shots`;
      case 'IMPACT':
        return `💥 Impact #${data.shot_number || 'unknown'} | Target ${data.target || 'unknown'} | Sensor ${data.sensor || 'unknown'} - String ${data.string || 'unknown'}, Time ${data.shot_time || 'unknown'}s`;
      default:
        // Handle bridge status and other events
        if (data.message) {
          return data.message;
        }
        return `${data.event_type || 'Event'}: ${data.description || JSON.stringify(data)}`;
    }
  };

  // Get appropriate log level based on event data
  const getEventLevel = (data: any) => {
    switch (data.event_type) {
      case 'ERROR':
        return 'ERROR';
      case 'WARNING':
        return 'WARNING';
      case 'DEBUG':
        return 'DEBUG';
      case 'IMPACT':
        return 'INFO';
      case 'START':
      case 'SHOT':
      case 'STOP':
        return 'INFO';
      default:
        return 'INFO';
    }
  };

  // Get performance rating for shot time
  const getRating = (shotTime: number | undefined): string => {
    if (!shotTime) return 'unknown';
    if (shotTime <= 0.30) return 'excellent';
    if (shotTime <= 0.50) return 'good';
    if (shotTime <= 0.70) return 'fair';
    return 'slow';
  };

  // Connect on component mount and load initial data
  useEffect(() => {
    // Load initial merged data
    loadMergedData();
    
    // Connect WebSocket for real-time updates
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const getStatusIcon = () => {
    switch (wsStatus) {
      case 'connected': return <span className="text-green-500">📶</span>;
      case 'disconnected': return <span className="text-red-500">📵</span>;
      case 'error': return <span className="text-red-500">⚠️</span>;
      default: return <span className="text-gray-500">📵</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">⏱️</span>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Live System Log</h1>
              <p className="text-sm text-gray-500">Merged timer and impact sensor events in real-time</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {getStatusIcon()}
              <span className="text-sm text-gray-600 capitalize">{wsStatus}</span>
            </div>
            <div className="text-sm text-gray-500">
              {logs.length} events
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setLogs([])}
              className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
            >
              Clear Logs
            </button>
          </div>
          <div className="text-sm text-gray-500">
            Live • Real-time updates
          </div>
        </div>
      </div>

      {/* Logs Table - Nested Window Style */}
      <div className="bg-white rounded-lg shadow">
        {/* Table Header - Fixed outside scroll area */}
        <div className="border-b border-gray-200">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/6">
                  TIMESTAMP
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/12">
                  LEVEL
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MESSAGE
                </th>
              </tr>
            </thead>
          </table>
        </div>
        
        {/* Scrollable Content Area - Nested Window */}
        <div className="h-96 overflow-y-scroll bg-white border border-gray-300" style={{scrollbarWidth: 'auto'}}>
          {logs.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center py-8">
                <span className="text-4xl text-gray-400 block mb-3">⏱️</span>
                <p className="text-gray-500">No system events yet</p>
                <p className="text-sm text-gray-400">Start shooting to see merged timer and impact data</p>
              </div>
            </div>
          ) : (
            <table className="w-full">
              <tbody className="bg-white divide-y divide-gray-100">
                {logs.map((log) => (
                  <TimerLogEntry key={`${log.id}-${log.timestamp}`} log={log} />
                ))}
              </tbody>
            </table>
          )}
        </div>
        
        {/* Footer with stats */}
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
          Total: {logs.length} • Filtered: {logs.length} • Errors: 0 • Warnings: 0 • Since startup
        </div>
      </div>
    </div>
  );
};

export default TimerLogPage;