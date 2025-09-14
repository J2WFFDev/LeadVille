/**
 * Main LeadVille Bridge React Application
 * Provides routing and layout for kiosk-friendly interface
 */

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { TimerPage } from './pages/TimerPage';
import { SensorPage } from './pages/SensorPage';
import { SettingsPage } from './pages/SettingsPage';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/timer" element={<TimerPage />} />
          <Route path="/sensor" element={<SensorPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
