/**
 * Timer Dashboard Page - Real-time shot display and analysis
 * Provides live shooting timer data visualization with WebSocket updates
 */

import React, { useState, useEffect, useRef } from 'react';

interface TimerEvent {
  log_id: number;
  event_time: string;
  event_type: string;
  shot_number?: number;
  total_shots?: number;
  shot_time?: number;
  string_total_time?: number;
  timer_device?: string;
  shot_rating?: string;
}

interface TimerStatus {
  timer_device: string;
  total_events: number;
  shot_events: number;
  max_string_time?: number;
  avg_split_time?: number;
  status: 'active' | 'recent' | 'idle';
}

interface LeaderboardEntry {
  timer_device: string;
  best_time: number;
  strings_completed: number;
  last_string: string;
}

interface WebSocketMessage {
  type: string;
  data: any;
}

export const TimerDashboardPage: React.FC = () => {
  // State management
  const [wsStatus, setWsStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');
  const [currentString, setCurrentString] = useState<TimerEvent[]>([]);
  const [timerStatus, setTimerStatus] = useState<TimerStatus[]>([]);
  const [latestEvents, setLatestEvents] = useState<TimerEvent[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [lastEventId, setLastEventId] = useState<number>(0);
  
  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket connection management
  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://${window.location.hostname}:8002/ws`;
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('📡 Timer WebSocket connected');
        setWsStatus('connected');
        
        // Send ping to keep alive
        const pingInterval = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
        
        (wsRef.current as any).pingInterval = pingInterval;
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('📡 Timer WebSocket disconnected');
        setWsStatus('disconnected');
        
        if ((wsRef.current as any)?.pingInterval) {
          clearInterval((wsRef.current as any).pingInterval);
        }
        
        // Attempt reconnection
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
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

  // Handle WebSocket messages
  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'initial_data':
        setCurrentString(message.data.current_string || []);
        setTimerStatus(message.data.timer_status || []);
        break;
        
      case 'timer_event':
        const event: TimerEvent = message.data;
        setLastEventId(Math.max(lastEventId, event.log_id));
        
        // Add to latest events
        setLatestEvents(prev => [event, ...prev.slice(0, 19)]);
        
        // Update current string if it's a shot
        if (event.event_type === 'SHOT') {
          setCurrentString(prev => [...prev, event].sort((a, b) => (a.shot_number || 0) - (b.shot_number || 0)));
        } else if (event.event_type === 'START') {
          setCurrentString([]);
        }
        break;
        
      case 'pong':
        // Keep-alive response
        break;
        
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  // Fetch initial data and leaderboard
  const fetchData = async () => {
    try {
      const [eventsRes, stringRes, statusRes, leaderRes] = await Promise.all([
        fetch(`http://${window.location.hostname}:8001/api/events/latest?limit=10`),
        fetch(`http://${window.location.hostname}:8001/api/string/current`),
        fetch(`http://${window.location.hostname}:8001/api/timer/status`),
        fetch(`http://${window.location.hostname}:8001/api/leaderboard`)
      ]);
      
      if (eventsRes.ok) setLatestEvents(await eventsRes.json());
      if (stringRes.ok) {
        const stringData = await stringRes.json();
        setCurrentString(stringData.shots || []);
      }
      if (statusRes.ok) setTimerStatus(await statusRes.json());
      if (leaderRes.ok) {
        const leaderData = await leaderRes.json();
        setLeaderboard(leaderData.leaderboard || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  // Component lifecycle
  useEffect(() => {
    fetchData();
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

  // Helper functions
  const formatTime = (seconds?: number): string => {
    if (!seconds) return 'N/A';
    return `${seconds.toFixed(2)}s`;
  };

  const getShotRatingColor = (rating?: string): string => {
    switch (rating) {
      case 'excellent': return 'text-green-500 bg-green-50';
      case 'good': return 'text-blue-500 bg-blue-50';
      case 'fair': return 'text-yellow-500 bg-yellow-50';
      case 'slow': return 'text-red-500 bg-red-50';
      default: return 'text-gray-500 bg-gray-50';
    }
  };

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
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🎯</span>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Timer Dashboard</h1>
              <p className="text-sm text-gray-500">Real-time shooting timer data and statistics</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {getStatusIcon()}
              <span className="text-sm text-gray-600 capitalize">{wsStatus}</span>
            </div>
            <div className="text-sm text-gray-500">
              Live streaming • Real-time updates
            </div>
          </div>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {timerStatus.length > 0 ? timerStatus.map((timer, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Timer Device</p>
                <p className="text-lg font-semibold text-gray-900">{timer.timer_device}</p>
              </div>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                timer.status === 'active' ? 'bg-green-100 text-green-800' :
                timer.status === 'recent' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {timer.status}
              </div>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Total Events</p>
                <p className="font-semibold">{timer.total_events}</p>
              </div>
              <div>
                <p className="text-gray-500">Avg Split</p>
                <p className="font-semibold">{formatTime(timer.avg_split_time)}</p>
              </div>
            </div>
          </div>
        )) : (
          <div className="col-span-3 bg-white rounded-lg shadow p-6 text-center text-gray-500">
            No timer devices found
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current String */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <span className="text-lg">📊</span>
              <h2 className="text-lg font-semibold text-gray-900">Current String</h2>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                {currentString.length} shots
              </span>
            </div>
          </div>
          
          <div className="p-6">
            {currentString.length > 0 ? (
              <div className="space-y-3">
                {currentString.map((shot, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-leadville-primary text-white rounded-full flex items-center justify-center text-sm font-semibold">
                          {shot.shot_number}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          Split: {formatTime(shot.shot_time)}
                        </p>
                        <p className="text-xs text-gray-500">
                          Total: {formatTime(shot.string_total_time)}
                        </p>
                      </div>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${getShotRatingColor(shot.shot_rating)}`}>
                      {shot.shot_rating}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <span className="text-4xl text-gray-400 block mb-3">⏰</span>
                <p className="text-gray-500">No active string</p>
                <p className="text-sm text-gray-400">Waiting for timer start...</p>
              </div>
            )}
          </div>
        </div>

        {/* Today's Leaderboard */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <span className="text-lg">🏆</span>
              <h2 className="text-lg font-semibold text-gray-900">Today's Best Times</h2>
            </div>
          </div>
          
          <div className="p-6">
            {leaderboard.length > 0 ? (
              <div className="space-y-3">
                {leaderboard.map((entry, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                          index === 0 ? 'bg-yellow-500 text-white' :
                          index === 1 ? 'bg-gray-400 text-white' :
                          index === 2 ? 'bg-amber-600 text-white' :
                          'bg-gray-200 text-gray-600'
                        }`}>
                          {index + 1}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{entry.timer_device}</p>
                        <p className="text-xs text-gray-500">{entry.strings_completed} strings</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900">{formatTime(entry.best_time)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <span className="text-4xl text-gray-400 block mb-3">🏆</span>
                <p className="text-gray-500">No times recorded today</p>
                <p className="text-sm text-gray-400">Start shooting to see leaderboard</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Events */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <span className="text-lg text-purple-600">⚡</span>
            <h2 className="text-lg font-semibold text-gray-900">Recent Events</h2>
            <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded-full">
              Live
            </span>
          </div>
        </div>
        
        <div className="p-6">
          {latestEvents.length > 0 ? (
            <div className="space-y-2">
              {latestEvents.slice(0, 10).map((event, index) => (
                <div key={event.log_id || index} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      event.event_type === 'START' ? 'bg-green-500' :
                      event.event_type === 'SHOT' ? 'bg-blue-500' :
                      event.event_type === 'STOP' ? 'bg-red-500' :
                      'bg-gray-500'
                    }`} />
                    <span className="text-sm font-medium text-gray-800">{event.event_type}</span>
                    {event.shot_number && (
                      <span className="text-sm text-gray-600">Shot #{event.shot_number}</span>
                    )}
                    {event.shot_time && (
                      <span className="text-sm text-gray-600">{formatTime(event.shot_time)}</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(event.event_time).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <span className="text-4xl text-gray-400 block mb-3">⚡</span>
              <p className="text-gray-500">No recent events</p>
              <p className="text-sm text-gray-400">Events will appear here in real-time</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};