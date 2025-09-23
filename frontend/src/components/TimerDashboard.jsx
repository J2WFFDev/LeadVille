import React, { useState, useEffect, useRef } from 'react';
import { Activity, Clock, Target, Zap, Trophy, AlertCircle, Wifi, WifiOff } from 'lucide-react';

const TimerDashboard = () => {
  // State management
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [currentString, setCurrentString] = useState([]);
  const [timerStatus, setTimerStatus] = useState([]);
  const [latestEvents, setLatestEvents] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [lastEventId, setLastEventId] = useState(0);
  
  // WebSocket ref
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection management
  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://${window.location.hostname}:8001/ws`;
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
        
        wsRef.current.pingInterval = pingInterval;
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
        console.log('📡 Timer WebSocket disconnected');
        setWsStatus('disconnected');
        
        if (wsRef.current?.pingInterval) {
          clearInterval(wsRef.current.pingInterval);
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
  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'initial_data':
        setCurrentString(message.data.current_string || []);
        setTimerStatus(message.data.timer_status || []);
        break;
        
      case 'timer_event':
        const event = message.data;
        setLastEventId(Math.max(lastEventId, event.log_id));
        
        // Add to latest events
        setLatestEvents(prev => [event, ...prev.slice(0, 19)]);
        
        // Update current string if it's a shot
        if (event.event_type === 'SHOT') {
          setCurrentString(prev => [...prev, event].sort((a, b) => a.shot_number - b.shot_number));
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
  const formatTime = (seconds) => {
    if (!seconds) return 'N/A';
    return `${seconds.toFixed(2)}s`;
  };

  const getShotRatingColor = (rating) => {
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
      case 'connected': return <Wifi className="h-4 w-4 text-green-500" />;
      case 'disconnected': return <WifiOff className="h-4 w-4 text-red-500" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <WifiOff className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Target className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">LeadVille Timer Dashboard</h1>
                <p className="text-sm text-gray-500">Real-time shooting timer data</p>
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
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {timerStatus.map((timer, index) => (
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
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Current String */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-blue-600" />
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
                          <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-semibold">
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
                  <Clock className="h-12 w-12 text-gray-400 mx-auto mb-3" />
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
                <Trophy className="h-5 w-5 text-yellow-600" />
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
                  <Trophy className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">No times recorded today</p>
                  <p className="text-sm text-gray-400">Start shooting to see leaderboard</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recent Events */}
        <div className="mt-6 bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <Zap className="h-5 w-5 text-purple-600" />
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
                <Zap className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No recent events</p>
                <p className="text-sm text-gray-400">Events will appear here in real-time</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-white border-t mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <div>
              LeadVille Impact Bridge © 2024 • Timer Dashboard • Real-time Updates
            </div>
            <div className="flex items-center space-x-4">
              <span>WebSocket: ws://{window.location.hostname}:8001/ws</span>
              <span className={`capitalize ${wsStatus === 'connected' ? 'text-green-600' : 'text-red-600'}`}>
                {wsStatus}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimerDashboard;