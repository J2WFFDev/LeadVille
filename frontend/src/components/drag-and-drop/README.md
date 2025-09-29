# Drag and Drop Device Assignment

This implementation provides an intuitive drag and drop interface for assigning sensors and timers to targets in the LeadVille Bridge system.

## 🎯 Features

### Core Functionality
- **Drag and Drop Interface**: Intuitive device assignment using native browser drag and drop
- **Device Pool Management**: Real-time device discovery and pool management
- **Visual Feedback**: Clear visual indicators for drag states, drop zones, and assignments
- **Validation System**: Comprehensive validation to prevent invalid assignments
- **Real-time Updates**: Live status updates for device battery, signal strength, and connectivity

### Device Types Supported
- **Impact Sensors (BT50)**: Accelerometer-based devices for target hit detection
- **Timer Devices**: AMG Labs Commander and compatible timing devices

### Assignment Types
- **Timer Assignment**: Single timer device for match timing
- **Sensor-to-Target Assignment**: One sensor per target for impact detection
- **Pool Device Integration**: Seamless integration with existing device pool system

## 📁 File Structure

```
frontend/src/
├── hooks/
│   └── useDragAndDrop.ts          # Core drag and drop state management
├── components/drag-and-drop/
│   ├── DraggableDevice.tsx        # Draggable device cards with status info
│   ├── DropZone.tsx              # Target and timer drop zones
│   └── DevicePool.tsx            # Device discovery and pool management
├── pages/
│   └── EnhancedStageSetupPage.tsx # Main drag and drop interface
└── utils/
    └── dragDropValidation.ts      # Validation utilities and rules
```

## 🔧 Implementation Details

### useDragAndDrop Hook

The core hook manages all drag and drop state:

```typescript
const {
  draggedItem,
  isDragging,
  assignments,
  initializeDropZones,
  handleDragStart,
  handleDragEnd,
  handleDrop,
  getAssignmentSummary
} = useDragAndDrop();
```

**Key Features:**
- Type-safe state management
- Automatic drop zone validation
- Assignment tracking and persistence
- Real-time summary calculations

### DraggableDevice Component

Displays devices with full status information:

- **Device Information**: MAC address, name, type
- **Battery Status**: Visual indicators and percentage
- **Signal Strength**: RSSI-based signal quality
- **Pool vs Discovered**: Clear distinction between device sources
- **Drag Visual Feedback**: Opacity and transform effects during drag

### DropZone Component

Intelligent drop zones with visual feedback:

- **Target Drop Zones**: Accept impact sensors only
- **Timer Drop Zone**: Accepts timer devices only
- **Visual States**: Default, drag over, invalid drop, assigned
- **Assignment Display**: Shows assigned device information
- **Remove Functionality**: Easy assignment removal

### DevicePool Component

Comprehensive device management:

- **Real-time Discovery**: WebSocket-based device discovery
- **Pool Integration**: Shows devices from existing pool
- **Status Monitoring**: Battery and signal tracking
- **Search and Filter**: Easy device location
- **Refresh Controls**: Manual pool refresh and discovery

## 🎨 Visual Design

### Color Coding
- **Green**: Successful assignments, good battery/signal
- **Yellow**: Warnings, fair battery/signal, timer-related
- **Red**: Errors, poor battery/signal, assignment conflicts
- **Blue**: Drag operations, pool devices, interactive elements
- **Gray**: Default states, disabled elements

### Responsive Design
- **Mobile-First**: Touch-friendly interfaces
- **Tablet Optimized**: Efficient layout for kiosk displays
- **Desktop Enhanced**: Full feature set with detailed information

## 📊 Validation System

### Device Validation Rules
- **Type Compatibility**: Sensors only to targets, timers only to timer slot
- **Battery Requirements**: Minimum 15% battery level
- **Signal Quality**: RSSI-based distance validation
- **Duplicate Prevention**: One device per assignment
- **Target Limits**: One sensor per target maximum

### Stage Validation
- **Timer Requirement**: Timer must be assigned for stage operation
- **Target Coverage**: Warnings for unassigned targets
- **Setup Completeness**: Real-time completion status
- **Conflict Detection**: Prevents duplicate assignments

### Error Handling
- **User-Friendly Messages**: Clear error descriptions
- **Contextual Suggestions**: Actionable improvement recommendations
- **Graceful Degradation**: Fallback discovery methods
- **API Error Recovery**: Retry mechanisms and user feedback

## 🚀 Usage Guide

### Basic Workflow

1. **Select Stage**: Choose league and stage configuration
2. **Discover Devices**: Use device pool or discover new devices
3. **Drag to Assign**: Drag devices to appropriate drop zones
4. **Validate Setup**: Review assignment summary and warnings
5. **Deploy Configuration**: Save and activate the configuration

### Advanced Features

- **Bulk Operations**: Multiple device management
- **Signal Optimization**: RSSI-based placement suggestions
- **Battery Monitoring**: Proactive low-battery warnings
- **Pool Management**: Device leasing and session management

## 🔗 API Integration

### Device Discovery
- `POST /api/admin/devices/discover` - Standard discovery
- WebSocket `/ws/device-discovery` - Real-time discovery

### Device Pool Management
- `GET /api/admin/pool/devices` - List pool devices
- `POST /api/admin/pool/sessions/{id}/lease` - Lease device

### Assignment APIs
- `POST /api/admin/targets/{id}/assign-sensor` - Assign sensor to target
- `DELETE /api/admin/targets/{id}/sensor` - Remove sensor assignment

## 📱 Accessibility

### Touch Support
- **Large Touch Targets**: Minimum 44px interactive elements
- **Touch Feedback**: Visual response to touch interactions
- **Gesture Support**: Native drag and drop on touch devices

### Keyboard Navigation
- **Tab Order**: Logical keyboard navigation
- **Space/Enter**: Alternative activation methods
- **Focus Indicators**: Clear focus visualization

### Screen Reader Support
- **ARIA Labels**: Descriptive element labels
- **Role Definitions**: Proper semantic roles
- **State Announcements**: Dynamic state changes

## 🧪 Testing Considerations

### Unit Testing
- Drag and drop state management
- Validation rule enforcement
- API integration error handling

### Integration Testing
- Device discovery workflows
- Assignment persistence
- Cross-component communication

### User Testing
- Drag and drop usability
- Error message clarity
- Mobile/touch experience

## 🔄 Migration from Dropdown Interface

The drag and drop system is designed to coexist with the existing dropdown-based interface:

1. **Parallel Routes**: Both interfaces available during transition
2. **Shared APIs**: Uses same backend endpoints
3. **Data Compatibility**: Assignments work with existing data structures
4. **Feature Parity**: All existing functionality preserved

## 🚧 Future Enhancements

### Planned Features
- **Multi-Select Drag**: Drag multiple devices simultaneously
- **Auto-Assignment**: Intelligent automatic device assignment
- **Template System**: Save and reuse stage configurations
- **Advanced Filtering**: Complex device search and filter options
- **Analytics Dashboard**: Usage patterns and optimization insights

### Performance Optimizations
- **Virtual Scrolling**: Handle large device lists efficiently
- **Caching Strategy**: Optimize API calls and data persistence
- **Bundle Splitting**: Lazy load drag and drop components
- **Memory Management**: Efficient cleanup of event listeners

---

## 📋 Quick Reference

### Key Components
- `EnhancedStageSetupPage` - Main interface at `/stage-setup-enhanced`
- `useDragAndDrop` - Core state management hook
- `DraggableDevice` - Device representation component
- `DropZone` - Assignment target component
- `DevicePool` - Device discovery and management

### Validation Functions
- `validateDeviceAssignment()` - Single assignment validation
- `validateStageSetup()` - Complete setup validation
- `getSetupSuggestions()` - Improvement recommendations

### Utility Functions
- `estimateDistanceFromRSSI()` - Distance calculation
- `getSignalStrengthCategory()` - Signal quality assessment
- `getBatteryLevelCategory()` - Battery status evaluation

This implementation provides a modern, intuitive interface for device assignment while maintaining compatibility with the existing LeadVille Bridge system architecture.