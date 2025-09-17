/**
 * Main layout component for LeadVille Bridge interface
 * Provides kiosk-friendly responsive design
 */

import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Navigation } from './Navigation';

interface LayoutProps {
  children?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <Header />
      
      {/* Navigation */}
      <Navigation />
      
      {/* Main Content */}
      <main className="flex-1 container mx-auto px-6 py-8">
        <div className="min-h-full">
          {children || <Outlet />}
        </div>
      </main>
      
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              LeadVille Impact Bridge © 2024
            </div>
            <div className="flex items-center space-x-4">
              <span>Version 2.0.0</span>
              <span>•</span>
              <span>Production Ready</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};