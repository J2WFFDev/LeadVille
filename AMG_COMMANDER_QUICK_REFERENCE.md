# AMG Commander Quick Reference

**Quick access guide for AMG Commander timer integration**

## 🚀 Quick Start

### Test Your AMG Timer
```bash
# SSH to Pi and run comprehensive test
ssh jrwest@192.168.1.125
cd /home/jrwest/projects/LeadVille
python3 amg_enhanced_test_comprehensive.py --mac 60:09:C3:1F:DC:1A
```

### API Quick Commands
```bash
# Check timer status
curl http://192.168.1.125:8001/api/admin/amg/timer/60:09:C3:1F:DC:1A/status

# Remote start (timer beeps)
curl -X POST http://192.168.1.125:8001/api/admin/amg/timer/60:09:C3:1F:DC:1A/remote-start

# Set sensitivity to 7
curl -X POST http://192.168.1.125:8001/api/admin/amg/timer/60:09:C3:1F:DC:1A/sensitivity/7

# Start shot monitoring
curl -X POST http://192.168.1.125:8001/api/admin/amg/timer/60:09:C3:1F:DC:1A/monitoring/start
```

## 🔧 Protocol Essentials

### BLE UUIDs
- **Service**: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- **Write**: `6e400002-b5a3-f393-e0a9-e50e24dcca9e` (commands TO timer)
- **Notify**: `6e400003-b5a3-f393-e0a9-e50e24dcca9e` (data FROM timer)

### Key Commands
- `COM START` - Remote start timer beep
- `SET SENSITIVITY 07` - Set sensitivity (01-10)
- `REQ STRING HEX` - Request shot sequence data
- `REQ SCREEN HEX` - Request display/screen data

### Known Timer MACs
- Timer 1: `60:09:C3:1F:DC:1A` 
- Timer 2: `60:09:C3:84:7F:F4`

## 📊 Enhanced Shot Data Structure
```json
{
  "time_now": 4.23,        // Current shot time
  "time_split": 1.15,      // Split time
  "time_first": 0.87,      // First shot time
  "unknown_field": 2.34,   // Additional data (bytes[10..11])
  "series_batch": 1.0,     // Series/batch info (bytes[12..13])
  "device": "60:09:C3:1F:DC:1A",
  "raw_data": "01 03 00 00 01 07 00 73..."
}
```

## 🛠️ Troubleshooting

### Service Check
```bash
# Check FastAPI is running
curl http://192.168.1.125:8001/api/health

# Restart if needed
ssh jrwest@192.168.1.125 "sudo fuser -k 8001/tcp"
ssh jrwest@192.168.1.125 "cd /home/jrwest/projects/LeadVille && nohup python3 -m uvicorn src.impact_bridge.fastapi_backend:app --host 0.0.0.0 --port 8001 --reload > fastapi.log 2>&1 &"
```

### Bluetooth Check
```bash
ssh jrwest@192.168.1.125 "bluetoothctl power on"
ssh jrwest@192.168.1.125 "bluetoothctl discoverable on"
```

## 📁 Key Files

### Implementation Files
- `src/impact_bridge/amg_commander_handler.py` - Core AMG handler
- `src/impact_bridge/amg_api.py` - REST API endpoints
- `src/impact_bridge/device_manager.py` - Device discovery
- `amg_enhanced_test_comprehensive.py` - Complete test suite

### Documentation Files  
- `docs/AMG_COMMANDER_COMPLETE_DOCUMENTATION.md` - Full documentation
- `AMG_COMMANDER_CAPABILITIES.md` - Feature summary
- `AMG_COMMANDER_QUICK_REFERENCE.md` - This file

## 🎯 What Works Now
- ✅ Enhanced device detection (Denis Zhadan's logic)
- ✅ Remote timer control (start, sensitivity)
- ✅ Real-time shot monitoring with enhanced data
- ✅ Screen data retrieval and parsing
- ✅ Complete shot sequence tracking
- ✅ Battery and signal monitoring
- ✅ Comprehensive API endpoints
- ✅ Full test suite validation

## 🔮 Future Possibilities
- Multi-timer synchronization
- Advanced shot analysis
- Mobile app integration  
- Competition management system
- Target system integration

---
*For complete details, see `docs/AMG_COMMANDER_COMPLETE_DOCUMENTATION.md`*