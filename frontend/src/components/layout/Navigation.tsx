/**
 * Navigation component for LeadVille Bridge interface
 */

import { NavLink } from 'react-router-dom';

interface NavigationItem {
  path: string;
  label: string;
  icon?: string;
}

const navigationItems: NavigationItem[] = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/timer', label: 'Timer Control', icon: '⏱️' },
  { path: '/sensor', label: 'Sensor Monitor', icon: '📡' },
  { path: '/stage-setup', label: 'Stage Setup', icon: '🏟️' },
  { path: '/ro', label: 'Range Officer', icon: '🎯' },
  { path: '/console', label: 'Console Logs', icon: '🖥️' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

export const Navigation: React.FC = () => {
  return (
    <nav className="bg-white shadow-md border-b border-gray-200">
      <div className="container mx-auto px-6">
        <div className="flex space-x-1">
          {navigationItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center space-x-2 px-4 py-4 text-sm font-medium transition-colors duration-200 border-b-2 ${
                  isActive
                    ? 'text-leadville-primary border-leadville-primary bg-blue-50'
                    : 'text-gray-600 border-transparent hover:text-leadville-primary hover:border-gray-300'
                }`
              }
            >
              {item.icon && (
                <span className="text-lg" role="img" aria-label={item.label}>
                  {item.icon}
                </span>
              )}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
};