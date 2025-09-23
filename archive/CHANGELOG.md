# LeadVille Impact Bridge - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-09-12

### Added - Initial LeadVille Release
- **Clean Architecture**: Complete rewrite with modular design
- **Production Ready**: Stable, tested codebase ready for deployment
- **Enhanced Impact Detection**: Dual-threshold onset timing detection
- **Real-time Correlation**: Shot-impact timing correlation system
- **Statistical Calibration**: Self-learning timing optimization
- **Auto-Calibration**: Dynamic baseline establishment on startup
- **Comprehensive Logging**: Multi-level logging with structured output
- **JSON Configuration**: Flexible configuration management
- **Professional Documentation**: Complete README and API documentation

### Core Components
- **BT50 Parser**: Corrected 1mg scale factor parser for WitMotion 5561 protocol
- **Shot Detector**: Advanced validation with duration and interval checking
- **Timing Calibrator**: Real-time shot-impact correlation with persistence
- **Enhanced Detector**: Precise onset timing with lookback analysis
- **Statistical Engine**: Statistical timing analysis and optimization
- **Configuration System**: Centralized JSON-based parameter management

### Technical Improvements
- **BLE Stability**: Robust connection handling and error recovery
- **Memory Management**: Efficient sample buffering and cleanup
- **Performance Optimization**: <50ms detection latency, <5% CPU usage
- **Error Handling**: Comprehensive exception handling and recovery
- **Type Safety**: Full type hints and static analysis support

### Device Support
- **AMG Timer**: Full integration with shot/start/stop event detection
- **BT50 Sensor**: Complete 3-axis acceleration data processing
- **Dual Device**: Simultaneous BLE connection management

### Logging & Monitoring
- **Console Logs**: Real-time operational feedback
- **Debug Logs**: Comprehensive debugging information
- **Event Logs**: Structured CSV and NDJSON event data
- **Statistics**: Runtime performance and correlation statistics

### Configuration
- **Detection Parameters**: Configurable thresholds and timing
- **System Settings**: BLE, calibration, and logging options
- **Runtime Tuning**: Live parameter adjustment capability

---

## Previous Versions

### TinTown Development Series
The LeadVille project is a clean rewrite based on lessons learned from the TinTown 
development series (2024-2025), which included extensive experimentation with:
- BLE protocol analysis and optimization
- Shot detection algorithm development  
- Timing correlation research
- Sensor calibration methodologies
- Performance optimization techniques

LeadVille represents the production-ready distillation of all successful 
TinTown innovations into a clean, maintainable codebase.