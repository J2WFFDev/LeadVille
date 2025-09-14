/**
 * Timer panel component for shot timing and control
 */

import { useTimerEvents } from '../../hooks/useWebSocket';

export const TimerPanel: React.FC = () => {
  const { 
    currentShot, 
    currentTime, 
    timerState, 
    timerEvents 
  } = useTimerEvents();

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return `${minutes.toString().padStart(2, '0')}:${secs.padStart(5, '0')}`;
  };

  const getTimerStateClass = () => {
    switch (timerState) {
      case 'active':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'ready':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'stopped':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getTimerStateIcon = () => {
    switch (timerState) {
      case 'active':
        return '▶️';
      case 'ready':
        return '⏸️';
      case 'stopped':
        return '⏹️';
      default:
        return '⏱️';
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        Timer Control
      </div>
      
      <div className="space-y-6">
        {/* Current Timer Display */}
        <div className="text-center">
          <div className="text-6xl md:text-7xl font-mono font-bold text-gray-800 mb-2">
            {formatTime(currentTime)}
          </div>
          <div className={`inline-flex items-center px-4 py-2 rounded-lg border text-lg font-semibold ${getTimerStateClass()}`}>
            <span className="mr-2">{getTimerStateIcon()}</span>
            {timerState.charAt(0).toUpperCase() + timerState.slice(1)}
          </div>
        </div>

        {/* Shot Counter */}
        <div className="bg-gray-50 rounded-lg p-6 text-center">
          <div className="text-sm font-medium text-gray-600 mb-2">Current Shot</div>
          <div className="text-4xl font-bold text-leadville-primary">
            {currentShot || '--'}
          </div>
        </div>

        {/* Recent Events */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Recent Events</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {timerEvents.slice(-5).reverse().map((event, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm">
                <div className="font-medium text-gray-700">
                  {event.event_type.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-gray-500">
                  {event.data.event_detail || 
                   (event.data.current_shot ? `Shot ${event.data.current_shot}` : 'Event')}
                </div>
              </div>
            ))}
            {timerEvents.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                No timer events yet
              </div>
            )}
          </div>
        </div>

        {/* Control Buttons - Kiosk Friendly */}
        <div className="grid grid-cols-2 gap-4">
          <button className="btn-primary">
            Start Timer
          </button>
          <button className="btn-secondary">
            Reset Timer
          </button>
        </div>
      </div>
    </div>
  );
};