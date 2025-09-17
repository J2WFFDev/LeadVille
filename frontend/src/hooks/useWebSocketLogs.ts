/**
 * Custom hook for WebSocket log streaming using native WebSocket
 */

import { useState, useEffect, useRef } from 'react';

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  source: string;
  message: string;
  raw?: string;
}

interface UseWebSocketLogsReturn {
  logs: LogEntry[];
  isConnected: boolean;
  connectionStatus: string;
  clearLogs: () => void;
  pauseLogging: () => void;
  resumeLogging: () => void;
}

export const useWebSocketLogs = (maxLines: number = 1000): UseWebSocketLogsReturn => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [connectionStatus, setConnectionStatus] = useState<string>('Disconnected');
  const [isPaused, setIsPaused] = useState<boolean>(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  // Parse log entry from different formats
  const parseLogEntry = (data: any): LogEntry => {
    // If it's already a structured log entry
    if (data.timestamp && data.level && data.source && data.message) {
      return {
        timestamp: data.timestamp,
        level: data.level,
        source: data.source,
        message: data.message,
        raw: data.raw
      };
    }

    // If it's a raw log line, parse it
    if (typeof data === 'string') {
      const logLine = data;
      const timestamp = new Date().toISOString();
      
      // Try to extract log level from the line
      let level: LogEntry['level'] = 'INFO';
      if (logLine.toLowerCase().includes('error')) level = 'ERROR';
      else if (logLine.toLowerCase().includes('warning')) level = 'WARNING';
      else if (logLine.toLowerCase().includes('debug')) level = 'DEBUG';
      
      // Try to extract source from the line
      let source = 'system';
      const apiMatch = logLine.match(/device_api|api/i);
      const sensorMatch = logLine.match(/sensor|bt50/i);
      const timerMatch = logLine.match(/timer|amg/i);
      
      if (apiMatch) source = 'device_api';
      else if (sensorMatch) source = 'sensor';
      else if (timerMatch) source = 'timer';
      
      return {
        timestamp,
        level,
        source,
        message: logLine,
        raw: logLine
      };
    }

    // Fallback for unknown format
    return {
      timestamp: new Date().toISOString(),
      level: 'INFO',
      source: 'unknown',
      message: JSON.stringify(data),
      raw: JSON.stringify(data)
    };
  };

  // Add log entry
  const addLogEntry = (entry: LogEntry) => {
    if (isPaused) return;
    
    setLogs((prevLogs: LogEntry[]) => {
      const newLogs = [...prevLogs, entry];
      // Keep only the last maxLines entries
      return newLogs.slice(-maxLines);
    });
  };

  // Connect to native WebSocket server
  const connectWebSocket = () => {
    try {
      console.log('🔌 Attempting WebSocket connection to ws://192.168.1.124:8001/ws/logs');
      
      const ws = new WebSocket('ws://192.168.1.124:8001/ws/logs');
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected successfully!');
        setIsConnected(true);
        setConnectionStatus('Connected via WebSocket');
        
        // Clear any pending reconnection
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
        
        // Request initial log batch
        ws.send(JSON.stringify({ type: 'request_logs', limit: 50 }));
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📋 Received WebSocket message:', data);
          
          if (data.type === 'log_batch' && Array.isArray(data.logs)) {
            // Handle batch of logs
            data.logs.forEach((logData: any) => {
              const logEntry = parseLogEntry(logData);
              addLogEntry(logEntry);
            });
          } else if (data.type === 'log_entry') {
            // Handle single log entry
            const logEntry = parseLogEntry(data);
            addLogEntry(logEntry);
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error, event.data);
        }
      };
      
      ws.onclose = () => {
        console.log('❌ WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('Disconnected');
        
        // Attempt to reconnect
        console.log('🔄 Will attempt to reconnect in 5 seconds...');
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnectionStatus('Connection Error');
        setIsConnected(false);
      };

      // Store the WebSocket for cleanup
      wsRef.current = ws;
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('Failed to Connect');
      
      // Attempt to reconnect after 10 seconds
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 10000);
    }
  };

  // Poll logs from REST API as fallback
  const pollLogs = async () => {
    try {
      const response = await fetch('http://192.168.1.124:8001/api/logs?limit=50');
      if (response.ok) {
        const data = await response.json();
        
        // Clear existing logs and add fresh ones (to avoid duplicates)
        setLogs(data.map((logData: any) => parseLogEntry(logData)));
        
        // Update connection status to show we're getting data
        if (!isConnected) {
          setConnectionStatus(`Polling API (${data.length} entries) - WebSocket: Retrying...`);
        }
      }
    } catch (error) {
      console.error('Failed to poll logs:', error);
      if (!isConnected) {
        setConnectionStatus('API Connection Failed');
      }
    }
  };

  // Initialize connection
  useEffect(() => {
    // Start with immediate polling to show logs right away
    pollLogs();
    
    // Set up aggressive polling (every 2 seconds)
    const pollingInterval = setInterval(pollLogs, 2000);
    
    // Try WebSocket connection in background
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      clearInterval(pollingInterval);
    };
  }, []);

  // Clear logs
  const clearLogs = () => {
    setLogs([]);
  };

  // Pause logging
  const pauseLogging = () => {
    setIsPaused(true);
  };

  // Resume logging
  const resumeLogging = () => {
    setIsPaused(false);
  };

  return {
    logs,
    isConnected,
    connectionStatus,
    clearLogs,
    pauseLogging,
    resumeLogging
  };
};