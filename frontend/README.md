# LeadVille Bridge - Frontend

Modern React-based frontend for the LeadVille Impact Bridge system. Built with Vite, TypeScript, and Tailwind CSS for kiosk-friendly responsive interfaces.

## Features

- 🚀 **Modern Tech Stack**: React 18 + Vite + TypeScript + Tailwind CSS
- 📱 **Responsive Design**: Optimized for kiosk displays and mobile devices
- 🔄 **Real-time Updates**: WebSocket integration with backend Python services
- 🎯 **Kiosk-Friendly**: Large buttons, clear status indicators, touch-optimized
- 🧭 **Routing**: React Router for navigation between dashboard views
- 📊 **Dashboard Components**: Timer control, sensor monitoring, system status

## Architecture

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── dashboard/       # Dashboard panels and widgets
│   │   ├── layout/          # Layout components (Header, Nav, etc.)
│   │   └── ui/              # Reusable UI components
│   ├── hooks/               # Custom React hooks
│   │   └── useWebSocket.ts  # WebSocket integration hooks
│   ├── pages/               # Page-level components
│   ├── utils/               # Utility functions
│   │   └── websocket.ts     # WebSocket client
│   └── index.css           # Tailwind CSS configuration
├── tailwind.config.js       # Tailwind configuration
└── vite.config.ts          # Vite configuration
```

## Quick Start

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Development Server**:
   ```bash
   npm run dev
   ```
   Opens at `http://localhost:5173`

3. **Build for Production**:
   ```bash
   npm run build
   ```

4. **Preview Production Build**:
   ```bash
   npm run preview
   ```

## WebSocket Integration

The frontend connects to the LeadVille Bridge WebSocket server at `ws://localhost:8765` for real-time updates:

- **Timer Events**: Shot detection, timing data, AMG timer status
- **Health Status**: Device connection status, signal strength, uptime
- **Session Updates**: Session state, shot counts, duration tracking

### Example Usage

```typescript
import { useDashboardData } from './hooks/useWebSocket';

function Dashboard() {
  const { connection, timer, health, session } = useDashboardData();
  
  return (
    <div>
      Status: {connection.isConnected ? 'Connected' : 'Disconnected'}
      Current Shot: {timer.currentShot}
      Timer: {timer.currentTime}s
    </div>
  );
}
```

## Kiosk Design Guidelines

- **Large Touch Targets**: Minimum 44px for buttons and interactive elements
- **High Contrast**: Clear color differentiation for status indicators
- **Readable Typography**: Large font sizes for distance viewing
- **Responsive Layout**: Adapts to different screen sizes and orientations
- **Visual Feedback**: Clear state changes and loading indicators

## Component Library

### Layout Components
- `Header`: Main navigation and connection status
- `Navigation`: Tab-style navigation between sections
- `Layout`: Main layout wrapper with responsive grid

### Dashboard Components
- `Dashboard`: Main dashboard with all panels
- `TimerPanel`: Timer controls and shot tracking
- `SensorPanel`: Impact sensor monitoring
- `StatusPanel`: System health and connection status

### Custom Hooks
- `useWebSocketConnection()`: WebSocket connection management
- `useTimerEvents()`: Timer-specific event handling
- `useHealthStatus()`: Device health monitoring
- `useDashboardData()`: Combined dashboard data

## Configuration

### Tailwind CSS
Custom theme configuration in `tailwind.config.js`:
- LeadVille brand colors (`leadville-primary`, `leadville-secondary`)
- Kiosk-specific spacing and typography scales
- Responsive breakpoints optimized for kiosk displays

### WebSocket Client
Configuration in `src/utils/websocket.ts`:
- Auto-reconnection with exponential backoff
- Message type handling and validation
- Connection state management

## Development

### Code Style
- TypeScript strict mode enabled
- ESLint + Prettier for code formatting
- Component-based architecture with clear separation of concerns

### Testing
- Unit tests with Vitest (planned)
- Component tests with React Testing Library (planned)
- E2E tests with Playwright (planned)

## Integration with Backend

The frontend connects to the existing LeadVille Bridge Python backend:

1. **WebSocket Server**: `src/impact_bridge/websocket_integration.py`
2. **Configuration**: Uses settings from `config/dev_config.json`
3. **Protocol**: JSON message format for timer events and health status
4. **Auto-Discovery**: Connects to configured WebSocket port (default: 8765)

## Deployment

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run preview
```

### Docker (Future)
Integration with existing Docker deployment planned for Raspberry Pi targets.

---

**Note**: This frontend complements the existing MVP HTML/CSS/JS interface at the repository root. Both interfaces can coexist during the transition period.
