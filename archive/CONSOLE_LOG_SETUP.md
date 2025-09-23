# Console Log Viewer Setup Summary

## Working Configuration (September 17, 2024)

### Services
- **API Server**: Port 8001 - Flask-SocketIO server serving console logs
- **Frontend**: Port 3003 - React app with console log viewer  
- **Main Application**: LeadVille bridge running on Pi

### Key Files Added
- scripts/device_api.py - Flask-SocketIO API server for console logs
- rontend/ - Complete React + TypeScript + Tailwind frontend
- rontend/src/hooks/useWebSocketLogs.ts - WebSocket + REST polling for logs
- rontend/src/pages/ConsoleLogPage.tsx - Main console viewer page

### URLs That Work
- API Health: http://192.168.1.124:8001/api/health
- Console Logs API: http://192.168.1.124:8001/api/logs?limit=20
- React Frontend: http://192.168.1.124:3003
- Console Page: http://192.168.1.124:3003/#/console

### Issues Resolved
1. **URL Configuration**: Updated React build to use 192.168.1.124:8001 instead of localhost:8001
2. **CORS**: API server configured to allow requests from frontend port
3. **WebSocket Fallback**: REST API polling works when WebSocket fails
4. **Log Parsing**: API server reads from original LeadVille log directories

### Known Issues
- WebSocket connection shows  Disconnected but REST polling works
- Multiple conflicting services running on different ports
- Need to consolidate to single clean environment

### Dependencies Installed
- python3-flask
- python3-flask-cors  
- python3-flask-socketio

### Next Steps
1. Clean Pi environment
2. Start with single working version
3. Fix WebSocket connection properly
4. Document proper startup procedure
