// Router configuration to add Timer Dashboard to existing app
// Add this to your existing router setup

import TimerDashboard from '../components/TimerDashboard';

// Add to your existing routes array:
const timerRoute = {
  path: '/timer-dashboard',
  element: <TimerDashboard />,
  meta: {
    title: 'Timer Dashboard',
    icon: 'Target',
    description: 'Live shooting timer data and statistics'
  }
};

// Or if using React Router v6:
import { Route } from 'react-router-dom';

// Add this Route component to your Routes:
<Route path="/timer-dashboard" element={<TimerDashboard />} />

// Navigation link to add to your existing navigation:
const timerNavLink = {
  href: '/timer-dashboard',
  label: 'Timer Dashboard',
  icon: 'Target',
  description: 'Real-time timer data'
};