# LeadVille Impact Bridge - Copilot Instructions

## Project Overview
LeadVille Impact Bridge is a production BLE-based impact sensor system for shooting sports that integrates AMG timers and BT50 acceleration sensors for real-time shot detection and impact correlation. This system evolved from the TinTown codebase with enhanced structure and production-ready features.

## Hardware Device Configuration
**Critical Device Constants - DO NOT MODIFY:**
- **AMG Timer MAC**: `60:09:C3:1F:DC:1A` 
  - UUID: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
  - Frame Types: START (0x0105), SHOT (0x0103), STOP (0x0108)
- **BT50 Sensor MAC**: `F8:FE:92:31:12:E3`
  - UUID: `0000ffe4-0000-1000-8000-00805f9a34fb`
  - Protocol: WitMotion 5561 with corrected 1mg scale factor

These are hardcoded device addresses tied to specific physical hardware. Never modify without corresponding hardware changes.

## Project Structure Guidelines
```
LeadVille/
├── leadville_bridge.py          # Main entry point (legacy monolithic)
├── src/impact_bridge/           # Core library (modular structure)
│   ├── wtvb_parse.py           # BT50 parser (corrected 1mg scale)
│   ├── shot_detector.py        # Advanced shot detection
│   ├── timing_calibration.py   # Real-time timing correlation
│   └── statistical_timing_calibration.py  # Statistical analysis
├── config/dev_config.json      # Primary configuration file
└── logs/                       # Multi-format logging output
    ├── console/                # Complete console logs
    ├── debug/                  # Detailed debug information
    └── main/                   # Structured event data (CSV/JSON)
```

**Maintain both legacy and modular structures for compatibility.**

## Critical Configuration Parameters
When working with detection and timing settings:

```json
{
  "enhanced_impact": {
    "peak_threshold": 10.0,      // Primary detection threshold
    "onset_threshold": 3.0,      // Onset detection threshold
    "lookback_samples": 10       // Samples for onset analysis
  },
  "timing": {
    "expected_delay_ms": 526.0,  // Calibrated shot-to-impact delay
    "correlation_window_ms": 2000 // Maximum correlation window
  },
  "sensor": {
    "calibration_samples": 100,  // Required for baseline establishment
    "auto_calibrate_on_startup": true
  }
}
```

**Key Point**: BT50 scale factor is 1mg (corrected from previous versions) - this is critical for accurate sensor readings.

## Development Guidelines

### Async/BLE Patterns
- Use `async/await` for all BLE operations
- Implement connection retry logic with exponential backoff
- Always handle BLE disconnection gracefully with auto-reconnect
- Use proper notification handlers for real-time data streaming

### Detection Algorithm Flow
1. **Calibration Phase**: Collect 100+ samples for baseline (stationary sensor required)
2. **Detection Phase**: Dual-threshold system (peak + onset detection)
3. **Correlation Phase**: Statistical timing correlation between shots and impacts
4. **Logging Phase**: Multi-format output (console, debug, CSV, NDJSON)

### Code Patterns to Follow
```python
# Statistical calibration pattern
from impact_bridge.statistical_timing_calibration import StatisticalTimingCalibration

# Dual-threshold detection pattern  
if raw_change > config.peak_threshold:
    onset_time = detect_onset_with_lookback(buffer, config.onset_threshold)

# Proper BLE notification handling
async def notification_handler(sender, data):
    try:
        parsed_data = parse_sensor_data(data)
        await process_sensor_reading(parsed_data)
    except Exception as e:
        logger.error(f"Notification error: {e}")
```

### Anti-patterns to Avoid
- Never modify MAC addresses or UUIDs without hardware verification
- Don't change the TinTown console output format (compatibility requirement)
- Avoid blocking operations in BLE notification handlers
- Don't skip sensor calibration phase - critical for accuracy

## Performance Requirements
- **Detection Latency**: <50ms from sensor to log entry
- **Sampling Rate**: ~100Hz continuous acceleration data
- **Memory Usage**: <50MB during typical operation
- **Connection Time**: 2-3 seconds for both BLE devices
- **Calibration Time**: 10-15 seconds for 100+ samples

## Testing & Deployment Considerations
- **Physical Hardware Required**: Full testing requires actual BLE devices
- **Raspberry Pi Target**: Primary deployment platform (see `setup_pi.sh`)
- **Windows Development**: Supported for development and testing
- **Virtual Environments**: Always use for dependency isolation
- **Systemd Service**: Available for production Pi deployment

## Common Development Tasks

### Adding New Detection Features
1. Modify detection thresholds in `config/dev_config.json`
2. Update detection logic in `enhanced_impact_detection.py`
3. Test with physical hardware for validation
4. Update statistical calibration if timing changes

### Debugging BLE Issues
1. Check `logs/debug/` for detailed BLE connection logs
2. Verify MAC addresses match physical devices
3. Monitor calibration completion in startup logs
4. Use `enable_raw_data_logging: true` for sensor data analysis

### Configuration Management
- Primary config: `config/dev_config.json`
- YAML support: `config/development.yaml`
- Environment-specific configs supported
- Always validate config changes against schema

## Integration Points
- **TinTown Compatibility**: Maintain exact console output format
- **Statistical Analysis**: Use built-in calibration systems
- **Multi-format Logging**: Support CSV, JSON, and plain text outputs
- **Service Integration**: Systemd service configuration included