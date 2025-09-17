/**
 * React hooks for WebSocket integration with LeadVille Bridge
 */

import { useEffect, useState, useCallback } from 'react';
import { wsClient } from '../utils/websocket';
import type { WebSocketMessage, TimerEvent, HealthStatus, SessionUpdate } from '../utils/websocket';

// Hook for WebSocket connection status
export const useWebSocketConnection = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<string>('disconnected');

  useEffect(() => {
    const unsubscribeConnection = wsClient.onConnection((connected) => {
      setIsConnected(connected);
      setConnectionState(wsClient.connectionState);
    });

    // Initial state
    setIsConnected(wsClient.connected);
    setConnectionState(wsClient.connectionState);

    // Connect on mount
    wsClient.connect();

    return () => {
      unsubscribeConnection();
    };
  }, []);

  const connect = useCallback(() => {
    wsClient.connect();
  }, []);

  const disconnect = useCallback(() => {
    wsClient.disconnect();
  }, []);

  return {
    isConnected,
    connectionState,
    connect,
    disconnect
  };
};

// Hook for listening to WebSocket messages
export const useWebSocketMessages = () => {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    const unsubscribe = wsClient.onMessage((message) => {
      setLastMessage(message);
      setMessages(prev => [...prev.slice(-99), message]); // Keep last 100 messages
    });

    return unsubscribe;
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastMessage(null);
  }, []);

  return {
    messages,
    lastMessage,
    clearMessages
  };
};

// Hook for timer events specifically
export const useTimerEvents = () => {
  const [timerEvents, setTimerEvents] = useState<TimerEvent[]>([]);
  const [lastTimerEvent, setLastTimerEvent] = useState<TimerEvent | null>(null);
  const [currentShot, setCurrentShot] = useState<number>(0);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [timerState, setTimerState] = useState<string>('idle');

  useEffect(() => {
    const unsubscribe = wsClient.onMessage((message) => {
      if (message.type === 'timer_event') {
        const timerEvent = message as TimerEvent;
        setLastTimerEvent(timerEvent);
        setTimerEvents(prev => [...prev.slice(-49), timerEvent]); // Keep last 50 events
        
        // Update current state
        if (timerEvent.data.current_shot !== undefined) {
          setCurrentShot(timerEvent.data.current_shot);
        }
        if (timerEvent.data.current_time !== undefined) {
          setCurrentTime(timerEvent.data.current_time);
        }
        if (timerEvent.data.shot_state !== undefined) {
          setTimerState(timerEvent.data.shot_state.toLowerCase());
        }
      }
    });

    return unsubscribe;
  }, []);

  const clearTimerEvents = useCallback(() => {
    setTimerEvents([]);
    setLastTimerEvent(null);
  }, []);

  return {
    timerEvents,
    lastTimerEvent,
    currentShot,
    currentTime,
    timerState,
    clearTimerEvents
  };
};

// Hook for health status updates
export const useHealthStatus = () => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('unknown');
  const [rssi, setRssi] = useState<number | null>(null);
  const [uptime, setUptime] = useState<number | null>(null);

  useEffect(() => {
    const unsubscribe = wsClient.onMessage((message) => {
      if (message.type === 'health_status') {
        const healthEvent = message as HealthStatus;
        setHealthStatus(healthEvent);
        
        // Update individual status fields
        setConnectionStatus(healthEvent.data.connection_status);
        setRssi(healthEvent.data.rssi_dbm || null);
        setUptime(healthEvent.data.uptime_seconds || null);
      }
    });

    return unsubscribe;
  }, []);

  return {
    healthStatus,
    connectionStatus,
    rssi,
    uptime
  };
};

// Hook for session updates
export const useSessionStatus = () => {
  const [sessionData, setSessionData] = useState<SessionUpdate | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<string>('idle');
  const [shotCount, setShotCount] = useState<number>(0);
  const [sessionDuration, setSessionDuration] = useState<number>(0);

  useEffect(() => {
    const unsubscribe = wsClient.onMessage((message) => {
      if (message.type === 'session_update') {
        const sessionEvent = message as SessionUpdate;
        setSessionData(sessionEvent);
        
        // Update individual session fields
        if (sessionEvent.data.session_id !== undefined) {
          setSessionId(sessionEvent.data.session_id);
        }
        if (sessionEvent.data.state !== undefined) {
          setSessionState(sessionEvent.data.state);
        }
        if (sessionEvent.data.shots !== undefined) {
          setShotCount(sessionEvent.data.shots);
        }
        if (sessionEvent.data.duration !== undefined) {
          setSessionDuration(sessionEvent.data.duration);
        }
      }
    });

    return unsubscribe;
  }, []);

  return {
    sessionData,
    sessionId,
    sessionState,
    shotCount,
    sessionDuration
  };
};

// Combined hook for dashboard data
export const useDashboardData = () => {
  const connection = useWebSocketConnection();
  const timerData = useTimerEvents();
  const healthData = useHealthStatus();
  const sessionData = useSessionStatus();

  return {
    connection,
    timer: timerData,
    health: healthData,
    session: sessionData
  };
};