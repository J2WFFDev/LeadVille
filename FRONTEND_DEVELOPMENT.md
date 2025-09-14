# LeadVille Bridge - Frontend Development Guide

This guide covers the modern React frontend implementation for the LeadVille Impact Bridge system.

## Overview

The frontend foundation provides a modern, kiosk-friendly interface built with:

- **React 18** + **TypeScript** for type-safe component development
- **Vite** for fast development and optimized builds
- **Tailwind CSS** for responsive, kiosk-optimized styling
- **React Router** for navigation between dashboard sections
- **WebSocket client** for real-time backend integration

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development

```bash
# Terminal 1: Start WebSocket server simulation
python frontend_demo.py

# Terminal 2: Start React development server
cd frontend
npm run dev
```

Open http://localhost:5173 to see the interface.

### 3. Production Build

```bash
cd frontend
npm run build
npm run preview  # Test production build
```

## Architecture

### Directory Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── dashboard/      # Dashboard-specific components
│   │   │   ├── Dashboard.tsx       # Main dashboard layout
│   │   │   ├── TimerPanel.tsx      # Timer controls & display
│   │   │   ├── SensorPanel.tsx     # Sensor monitoring
│   │   │   └── StatusPanel.tsx     # System status
│   │   ├── layout/         # Layout components
│   │   │   ├── Header.tsx          # Main header with status
│   │   │   ├── Navigation.tsx      # Tab navigation
│   │   │   └── Layout.tsx          # Main layout wrapper
│   │   └── ui/             # Reusable UI components (future)
│   ├── hooks/              # Custom React hooks
│   │   └── useWebSocket.ts         # WebSocket integration
│   ├── pages/              # Page-level components
│   │   ├── DashboardPage.tsx       # Main dashboard page
│   │   ├── TimerPage.tsx           # Timer control page
│   │   ├── SensorPage.tsx          # Sensor monitoring page
│   │   └── SettingsPage.tsx        # System settings
│   ├── utils/              # Utility functions
│   │   └── websocket.ts            # WebSocket client
│   └── index.css           # Tailwind CSS + custom styles
├── tailwind.config.js      # Tailwind configuration
├── vite.config.ts          # Vite configuration
└── package.json            # Dependencies and scripts
```

### Key Components

#### WebSocket Integration (`src/utils/websocket.ts`)

Provides a robust WebSocket client with:
- Auto-reconnection with exponential backoff
- Type-safe message handling
- Event subscription management
- Connection state tracking

```typescript
// Example usage
import { wsClient } from './utils/websocket';

wsClient.connect();
wsClient.onMessage((message) => {
  console.log('Received:', message);
});
```

#### Custom Hooks (`src/hooks/useWebSocket.ts`)

React hooks for WebSocket integration:

- `useWebSocketConnection()` - Connection status
- `useTimerEvents()` - Timer-specific events
- `useHealthStatus()` - Device health monitoring
- `useDashboardData()` - Combined dashboard data

```typescript
// Example usage in component
import { useDashboardData } from '../hooks/useWebSocket';

function Dashboard() {
  const { connection, timer, health } = useDashboardData();
  
  return (
    <div>
      Status: {connection.isConnected ? 'Connected' : 'Disconnected'}
      Shot: {timer.currentShot}
      Time: {timer.currentTime}s
    </div>
  );
}
```

#### Layout System (`src/components/layout/`)

Responsive layout optimized for kiosk displays:

- **Header**: Shows connection status and branding
- **Navigation**: Tab-based navigation between sections
- **Layout**: Main wrapper with responsive grid

#### Dashboard Components (`src/components/dashboard/`)

Specialized components for monitoring:

- **TimerPanel**: Shot timing and timer controls
- **SensorPanel**: Impact sensor data and calibration
- **StatusPanel**: System health and connectivity
- **Dashboard**: Combined dashboard view

## Styling & Design

### Tailwind CSS Configuration

Custom configuration in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      'leadville': {
        primary: '#667eea',    // Brand primary
        secondary: '#764ba2',  // Brand secondary
        accent: '#4f46e5',     // Accent color
      }
    },
    spacing: {
      'kiosk': '12rem',       // Large spacing for kiosk
    },
    fontSize: {
      'kiosk-xl': ['2rem', '2.5rem'],   // Large kiosk text
      'kiosk-2xl': ['3rem', '3.5rem'],
      'kiosk-3xl': ['4rem', '4.5rem'],
    }
  }
}
```

### Component Classes

Pre-defined component classes in `src/index.css`:

```css
/* Kiosk-friendly buttons */
.btn-primary { /* Large primary button */ }
.btn-secondary { /* Secondary button */ }
.btn-danger { /* Danger/stop button */ }

/* Status indicators */
.status-connected { /* Green connected state */ }
.status-disconnected { /* Red disconnected state */ }
.status-ready { /* Yellow ready state */ }
.status-active { /* Blue active state */ }

/* Panels */
.panel { /* White panel with shadow */ }
.panel-header { /* Panel header styling */ }
```

### Responsive Design

The interface adapts to different screen sizes:

- **Mobile**: Single column layout, large touch targets
- **Tablet**: Two-column grid, optimized for touch
- **Desktop**: Three-column grid, full dashboard view
- **Kiosk**: Large elements, high contrast, distance viewing

## Integration with Backend

### WebSocket Protocol

Connects to the LeadVille Bridge WebSocket server at `ws://localhost:8765`.

**Message Types:**

1. **Timer Events**:
   ```json
   {
     "type": "timer_event",
     "event_type": "shot_detected",
     "timestamp": "2023-09-13T18:30:45.123Z",
     "device_id": "60:09:C3:1F:DC:1A",
     "data": {
       "shot_state": "ACTIVE",
       "current_shot": 3,
       "current_time": 15.67
     }
   }
   ```

2. **Health Status**:
   ```json
   {
     "type": "health_status",
     "timestamp": "2023-09-13T18:30:45.123Z",
     "data": {
       "connection_status": "connected",
       "rssi_dbm": -65,
       "uptime_seconds": 1234.5
     }
   }
   ```

3. **Session Updates**:
   ```json
   {
     "type": "session_update",
     "data": {
       "session_id": "session_001",
       "state": "active",
       "shots": 5,
       "duration": 125.4
     }
   }
   ```

### Backend Configuration

Uses existing configuration from `config/dev_config.json`:

```json
{
  "websocket": {
    "enabled": true,
    "host": "localhost", 
    "port": 8765
  }
}
```

## Development Workflow

### 1. Component Development

1. Create component in appropriate directory
2. Use TypeScript for type safety
3. Apply Tailwind classes for styling
4. Use custom hooks for WebSocket data
5. Test responsiveness across screen sizes

### 2. Adding New Features

1. **New Dashboard Panel**:
   - Create component in `src/components/dashboard/`
   - Add to main `Dashboard.tsx`
   - Create corresponding page if needed

2. **New WebSocket Message Type**:
   - Update types in `src/utils/websocket.ts`
   - Add handler in `src/hooks/useWebSocket.ts`
   - Use in components

3. **New Page**:
   - Create component in `src/pages/`
   - Add route in `src/App.tsx`
   - Update navigation in `src/components/layout/Navigation.tsx`

### 3. Testing

```bash
# Type checking
npm run build

# Linting
npm run lint

# Development server
npm run dev

# Production preview
npm run preview
```

## Deployment

### Development Environment

```bash
# Start both servers for full demo
python frontend_demo.py     # Terminal 1: WebSocket server
cd frontend && npm run dev  # Terminal 2: React dev server
```

### Production Build

```bash
cd frontend
npm run build               # Creates dist/ directory
npm run preview            # Test production build locally
```

### Integration with Existing System

The frontend is designed to complement the existing LeadVille system:

1. **Coexists** with current MVP HTML/CSS interface
2. **Uses** existing WebSocket server from `src/impact_bridge/websocket_integration.py`
3. **Reads** configuration from `config/dev_config.json`
4. **Compatible** with existing Raspberry Pi deployment

## Future Enhancements

Planned improvements for the frontend foundation:

- [ ] **Testing**: Unit tests with Vitest, E2E with Playwright
- [ ] **PWA**: Progressive Web App features for kiosk deployment
- [ ] **Dark Mode**: Theme switching for different environments
- [ ] **Offline Mode**: Local state management for network interruptions
- [ ] **Performance**: Chart components for data visualization
- [ ] **Accessibility**: ARIA labels and keyboard navigation
- [ ] **Docker**: Containerized deployment for Raspberry Pi

## Troubleshooting

### WebSocket Connection Issues

1. **Check server**: Ensure WebSocket server is running on port 8765
2. **Check firewall**: Verify port 8765 is accessible
3. **Check logs**: Look at browser developer console for errors
4. **Test connection**: Use `python test_websocket_server.py` to verify server

### Build Issues

1. **TypeScript errors**: Run `npm run build` to see type errors
2. **Missing dependencies**: Run `npm install` to ensure all packages installed
3. **Tailwind not working**: Check `postcss.config.js` configuration
4. **Port conflicts**: Change Vite port in `vite.config.ts` if needed

---

For questions or issues, refer to the main project documentation or create an issue in the repository.