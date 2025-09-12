# LeadVille

## MVP-1: Sensor & Timer Interface

LeadVille MVP-1 provides a web-based interface for monitoring sensor data and managing timer functionality. This implementation focuses on building the next layer of interface with minimal, clean components.

### Features

#### 1 Sensor Component
- **Temperature Monitoring**: Simulated temperature sensor with realistic readings (18-25°C range)
- **Real-time Updates**: Sensor readings update every 2 seconds when active
- **Status Indicators**: Clear visual feedback for online/offline status
- **Control Interface**: Start/Stop monitoring functionality

#### 1 Timer Component  
- **Countdown Timer**: Configurable timer with minutes input (0-59 minutes)
- **Timer Controls**: Start, Pause, and Reset functionality
- **Visual Display**: Large, easy-to-read timer display in HH:MM:SS format
- **Completion Alert**: Notification when timer reaches zero

#### Interface Layer
- **System Status Dashboard**: Real-time status monitoring for all components
- **Responsive Design**: Clean, professional interface that works on desktop and mobile
- **Status Indicators**: Color-coded status indicators for quick system overview
- **User-Friendly Controls**: Intuitive button layout with proper state management

### Usage

1. **Open the Interface**: Open `index.html` in a web browser or serve via HTTP server
2. **Start Sensor Monitoring**: Click "Start Monitoring" to begin receiving temperature data
3. **Set Timer**: Adjust minutes (default 5) and click "Start" to begin countdown
4. **Monitor System**: View real-time status in the System Status panel

### Technical Implementation

- **Pure Web Technologies**: HTML5, CSS3, and vanilla JavaScript
- **Modular Architecture**: Separate classes for SensorManager, TimerManager, and InterfaceManager
- **Event-Driven Design**: Clean event handling with proper state management
- **Responsive Layout**: CSS Grid and Flexbox for modern, responsive design

### Files

- `index.html` - Main application interface
- `styles.css` - Complete styling and responsive design
- `app.js` - Application logic with modular JavaScript classes
- `README.md` - This documentation

### Development

To run locally:
```bash
# Serve via Python HTTP server
python3 -m http.server 8000

# Or use any other HTTP server
# Then open http://localhost:8000
```

This MVP demonstrates the foundational interface layer for LeadVille, providing a solid base for future enhancements and additional sensor/timer integrations.