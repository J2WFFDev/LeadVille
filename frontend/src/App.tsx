/**
 * Main LeadVille Bridge React Application
 * Provides routing and layout for kiosk-friendly interface
 */

import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { TimerPage } from './pages/TimerPage';
import { SensorPage } from './pages/SensorPage';
import { MatchSetupPage } from './pages/MatchSetupPage';
import { SettingsPage } from './pages/SettingsPage';
import { ConsolePage } from './pages/ConsolePage';
import { RangeOfficerPage } from './pages/RangeOfficerPage';
import { StageSetupPage } from './pages/StageSetupPage';
import { EnhancedStageSetupPage } from './pages/EnhancedStageSetupPage';
import { TimerDashboardPage } from './pages/TimerDashboardPage';
import { LiveLogPage } from './pages/LiveLogPage';
import { DeviceAssignmentPage } from './pages/DeviceAssignmentPage';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/timer" element={<TimerPage />} />
          <Route path="/timer-dashboard" element={<TimerDashboardPage />} />
          <Route path="/live-log" element={<LiveLogPage />} />
          <Route path="/sensor" element={<SensorPage />} />
          <Route path="/match-setup" element={<MatchSetupPage />} />
          <Route path="/stage-setup" element={<StageSetupPage />} />
          <Route path="/stage-setup-enhanced" element={<EnhancedStageSetupPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/console" element={<ConsolePage />} />
          <Route path="/ro" element={<RangeOfficerPage />} />
          <Route path="/device-assignment" element={<DeviceAssignmentPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
