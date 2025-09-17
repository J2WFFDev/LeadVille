/**
 * Timer control page
 */

import { TimerPanel } from '../components/dashboard/TimerPanel';

export const TimerPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
          Timer Control
        </h1>
        <p className="text-gray-600">
          AMG Labs Commander timer management and shot tracking
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="lg:col-span-2">
          <TimerPanel />
        </div>
      </div>
    </div>
  );
};