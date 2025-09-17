/**
 * Custom hook for WebSocket log streaming using Socket.IO
 */

import { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

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
  
  const socketRef = useRef<Socket | null>(null);
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

  // Connect to Socket.IO server
  const connectWebSocket = () => {
    try {
      console.log('🔌 Attempting Socket.IO connection to http://192.168.1.124:8001/ws/logs');
      
      // Connect to the logs namespace directly
      const logsSocket = io('http://192.168.1.124:8001/ws/logs', {
        transports: ['polling', 'websocket'], // Try polling first, then websocket
        timeout: 10000,
        forceNew: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 2000
      });
      
      console.log('📡 Socket.IO client created, waiting for connection...');
      
      logsSocket.on('connect', () => {
        console.log('✅ Socket.IO connected successfully!');
        setIsConnected(true);
        setConnectionStatus('Connected via Socket.IO');
        
        // Clear any pending reconnection
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      });
      
      logsSocket.on('log_entry', (data: any) => {
        console.log('📋 Received log entry:', data);
        try {
          const logEntry = parseLogEntry(data);
          addLogEntry(logEntry);
        } catch (error) {
          console.error('❌ Error parsing log entry:', error, data);
        }
      });
      
      logsSocket.on('disconnect', (reason: string) => {
        console.log('❌ Socket.IO disconnected:', reason);
        setIsConnected(false);
        setConnectionStatus('Disconnected');
        
        // Don't auto-reconnect if we're disconnecting on purpose
        if (reason !== 'io client disconnect') {
          console.log('🔄 Will attempt to reconnect in 5 seconds...');
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
        }
      });
      
      logsSocket.on('connect_error', (error: any) => {
        console.error('❌ Socket.IO connection error:', error);
        setConnectionStatus('Connection Error: ' + error.message);
        setIsConnected(false);
      });
      
      logsSocket.on('error', (error: any) => {
        console.error('❌ Socket.IO error:', error);
      });

      // Store the logs socket for cleanup
      socketRef.current = logsSocket;
      
    } catch (error) {
      console.error('Failed to create Socket.IO connection:', error);
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
      if (socketRef.current) {
        socketRef.current.disconnect();
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