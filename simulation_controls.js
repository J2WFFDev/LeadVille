/**
 * LeadVille Simulation Controls JavaScript
 * Handles the interactive simulation control interface
 */

class SimulationController {
    constructor() {
        this.isRunning = false;
        this.isPaused = false;
        this.simulationStartTime = null;
        this.simulationTimer = null;
        this.websocket = null;
        
        // Statistics
        this.stats = {
            shotsFired: 0,
            impactsDetected: 0,
            errorsInjected: 0,
            sensorSamples: 0,
            simulationTime: 0
        };
        
        this.initializeControls();
        this.setupEventListeners();
        this.loadScenarioDefaults();
    }
    
    initializeControls() {
        // Initialize range input displays
        this.updateRangeDisplay('shot-interval', 'shot-interval-value', (val) => `${val}s`);
        this.updateRangeDisplay('shooter-skill', 'shooter-skill-value', (val) => `${Math.round(val * 100)}%`);
        this.updateRangeDisplay('error-rate', 'error-rate-value', (val) => `${Math.round(val * 100)}%`);
        this.updateRangeDisplay('sim-speed', 'sim-speed-value', (val) => `${val}x`);
        this.updateRangeDisplay('miss-probability', 'miss-probability-value', (val) => `${Math.round(val * 100)}%`);
        this.updateRangeDisplay('temperature', 'temperature-value', (val) => `${val}°C`);
        this.updateRangeDisplay('humidity', 'humidity-value', (val) => `${val}%`);
        this.updateRangeDisplay('wind-speed', 'wind-speed-value', (val) => `${val} m/s`);
        
        this.logEvent('System initialized', 'info');
    }
    
    setupEventListeners() {
        // Range input listeners
        document.getElementById('shot-interval').addEventListener('input', (e) => {
            this.updateRangeDisplay('shot-interval', 'shot-interval-value', (val) => `${val}s`);
        });
        
        document.getElementById('shooter-skill').addEventListener('input', (e) => {
            this.updateRangeDisplay('shooter-skill', 'shooter-skill-value', (val) => `${Math.round(val * 100)}%`);
        });
        
        document.getElementById('error-rate').addEventListener('input', (e) => {
            this.updateRangeDisplay('error-rate', 'error-rate-value', (val) => `${Math.round(val * 100)}%`);
        });
        
        document.getElementById('sim-speed').addEventListener('input', (e) => {
            this.updateRangeDisplay('sim-speed', 'sim-speed-value', (val) => `${val}x`);
        });
        
        document.getElementById('miss-probability').addEventListener('input', (e) => {
            this.updateRangeDisplay('miss-probability', 'miss-probability-value', (val) => `${Math.round(val * 100)}%`);
        });
        
        document.getElementById('temperature').addEventListener('input', (e) => {
            this.updateRangeDisplay('temperature', 'temperature-value', (val) => `${val}°C`);
        });
        
        document.getElementById('humidity').addEventListener('input', (e) => {
            this.updateRangeDisplay('humidity', 'humidity-value', (val) => `${val}%`);
        });
        
        document.getElementById('wind-speed').addEventListener('input', (e) => {
            this.updateRangeDisplay('wind-speed', 'wind-speed-value', (val) => `${val} m/s`);
        });
        
        // Scenario selection
        document.getElementById('scenario-select').addEventListener('change', (e) => {
            this.loadScenarioDefaults();
        });
        
        // Control buttons
        document.getElementById('start-simulation').addEventListener('click', () => {
            this.startSimulation();
        });
        
        document.getElementById('pause-simulation').addEventListener('click', () => {
            this.pauseSimulation();
        });
        
        document.getElementById('stop-simulation').addEventListener('click', () => {
            this.stopSimulation();
        });
        
        document.getElementById('clear-log').addEventListener('click', () => {
            this.clearLog();
        });
    }
    
    updateRangeDisplay(inputId, displayId, formatter) {
        const input = document.getElementById(inputId);
        const display = document.getElementById(displayId);
        display.textContent = formatter(input.value);
    }
    
    loadScenarioDefaults() {
        const scenario = document.getElementById('scenario-select').value;
        
        const scenarios = {
            steel_challenge: {
                numShots: 5,
                shotInterval: 0.8,
                shooterSkill: 0.9,
                errorRate: 0.02,
                impactDelay: 300,
                missProbability: 0.05,
                errors: ['error-sensor']
            },
            uspsa_match: {
                numShots: 8,
                shotInterval: 2.0,
                shooterSkill: 0.8,
                errorRate: 0.05,
                impactDelay: 520,
                missProbability: 0.08,
                errors: ['error-sensor', 'error-timing']
            },
            precision_match: {
                numShots: 10,
                shotInterval: 8.0,
                shooterSkill: 0.85,
                errorRate: 0.01,
                impactDelay: 520,
                missProbability: 0.03,
                errors: ['error-timing']
            },
            training_session: {
                numShots: 15,
                shotInterval: 2.5,
                shooterSkill: 0.6,
                errorRate: 0.15,
                impactDelay: 480,
                missProbability: 0.15,
                errors: ['error-ble', 'error-sensor', 'error-false', 'error-missed']
            },
            custom: {
                // Keep current values for custom scenario
                return: true
            }
        };
        
        const config = scenarios[scenario];
        if (!config || config.return) return;
        
        // Update form values
        document.getElementById('num-shots').value = config.numShots;
        document.getElementById('shot-interval').value = config.shotInterval;
        document.getElementById('shooter-skill').value = config.shooterSkill;
        document.getElementById('error-rate').value = config.errorRate;
        document.getElementById('impact-delay').value = config.impactDelay;
        document.getElementById('miss-probability').value = config.missProbability;
        
        // Update error checkboxes
        const errorCheckboxes = ['error-ble', 'error-sensor', 'error-timing', 'error-false', 'error-missed', 'error-battery'];
        errorCheckboxes.forEach(id => {
            document.getElementById(id).checked = config.errors.includes(id);
        });
        
        // Update range displays
        this.updateRangeDisplay('shot-interval', 'shot-interval-value', (val) => `${val}s`);
        this.updateRangeDisplay('shooter-skill', 'shooter-skill-value', (val) => `${Math.round(val * 100)}%`);
        this.updateRangeDisplay('error-rate', 'error-rate-value', (val) => `${Math.round(val * 100)}%`);
        this.updateRangeDisplay('miss-probability', 'miss-probability-value', (val) => `${Math.round(val * 100)}%`);
        
        this.logEvent(`Loaded ${scenario.replace('_', ' ')} scenario defaults`, 'info');
    }
    
    startSimulation() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.isPaused = false;
        this.simulationStartTime = Date.now();
        
        // Reset statistics
        this.resetStats();
        
        // Update button states
        document.getElementById('start-simulation').disabled = true;
        document.getElementById('pause-simulation').disabled = false;
        document.getElementById('stop-simulation').disabled = false;
        
        // Get simulation configuration
        const config = this.getSimulationConfig();
        
        this.logEvent(`Starting simulation: ${config.scenario}`, 'success');
        this.logEvent(`Configuration: ${config.numShots} shots, ${config.shotInterval}s interval`, 'info');
        
        // Start simulation timer
        this.simulationTimer = setInterval(() => {
            this.updateSimulationTime();
            this.simulateEvents();
        }, 100); // Update every 100ms
        
        // Start progress tracking
        this.startProgressTracking(config);
        
        // Try to connect WebSocket for real backend integration
        this.connectWebSocket();
    }
    
    pauseSimulation() {
        if (!this.isRunning || this.isPaused) return;
        
        this.isPaused = true;
        
        if (this.simulationTimer) {
            clearInterval(this.simulationTimer);
            this.simulationTimer = null;
        }
        
        document.getElementById('start-simulation').disabled = false;
        document.getElementById('pause-simulation').disabled = true;
        
        this.logEvent('Simulation paused', 'warning');
    }
    
    stopSimulation() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        this.isPaused = false;
        
        if (this.simulationTimer) {
            clearInterval(this.simulationTimer);
            this.simulationTimer = null;
        }
        
        // Reset button states
        document.getElementById('start-simulation').disabled = false;
        document.getElementById('pause-simulation').disabled = true;
        document.getElementById('stop-simulation').disabled = true;
        
        // Reset progress bar
        document.getElementById('simulation-progress').style.width = '0%';
        
        this.logEvent('Simulation stopped', 'error');
        this.logEvent(`Final stats: ${this.stats.shotsFired} shots, ${this.stats.impactsDetected} impacts`, 'info');
        
        // Disconnect WebSocket
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
    
    getSimulationConfig() {
        const selectedErrors = [];
        ['error-ble', 'error-sensor', 'error-timing', 'error-false', 'error-missed', 'error-battery'].forEach(id => {
            if (document.getElementById(id).checked) {
                selectedErrors.push(id.replace('error-', ''));
            }
        });
        
        return {
            scenario: document.getElementById('scenario-select').value,
            numShots: parseInt(document.getElementById('num-shots').value),
            shotInterval: parseFloat(document.getElementById('shot-interval').value),
            shooterSkill: parseFloat(document.getElementById('shooter-skill').value),
            errorRate: parseFloat(document.getElementById('error-rate').value),
            simSpeed: parseFloat(document.getElementById('sim-speed').value),
            impactDelay: parseInt(document.getElementById('impact-delay').value),
            missProbability: parseFloat(document.getElementById('miss-probability').value),
            temperature: parseFloat(document.getElementById('temperature').value),
            humidity: parseFloat(document.getElementById('humidity').value),
            windSpeed: parseFloat(document.getElementById('wind-speed').value),
            errorTypes: selectedErrors
        };
    }
    
    simulateEvents() {
        if (!this.isRunning || this.isPaused) return;
        
        const config = this.getSimulationConfig();
        
        // Simulate sensor samples (100Hz rate)
        if (Math.random() < 0.1) { // 10% chance per 100ms = ~10Hz display rate
            this.stats.sensorSamples += Math.floor(Math.random() * 10) + 1;
            this.updateStatistics();
        }
        
        // Simulate shots based on interval and speed multiplier
        const shotProbability = (1.0 / (config.shotInterval * 10)) * config.simSpeed;
        if (Math.random() < shotProbability && this.stats.shotsFired < config.numShots) {
            this.simulateShot(config);
        }
        
        // Simulate errors
        if (config.errorTypes.length > 0 && Math.random() < config.errorRate * 0.001) {
            this.simulateError(config);
        }
    }
    
    simulateShot(config) {
        this.stats.shotsFired++;
        this.logEvent(`💥 Shot #${this.stats.shotsFired} fired`, 'success');
        
        // Simulate impact with miss probability
        setTimeout(() => {
            if (Math.random() > config.missProbability) {
                this.stats.impactsDetected++;
                const amplitude = (Math.random() * 30 + 10).toFixed(1);
                this.logEvent(`🎯 Impact detected (Amplitude: ${amplitude})`, 'success');
            } else {
                this.logEvent(`❌ Shot missed target`, 'warning');
            }
            this.updateStatistics();
        }, config.impactDelay / config.simSpeed);
        
        this.updateStatistics();
    }
    
    simulateError(config) {
        if (config.errorTypes.length === 0) return;
        
        const errorType = config.errorTypes[Math.floor(Math.random() * config.errorTypes.length)];
        this.stats.errorsInjected++;
        
        const errorMessages = {
            ble: '🔌 BLE connection lost - reconnecting...',
            sensor: '📊 Sensor noise detected',
            timing: '⏱️ Timer drift correction applied',
            false: '⚠️ False positive filtered out',
            missed: '❌ Impact detection missed',
            battery: '🔋 Low battery warning'
        };
        
        const message = errorMessages[errorType] || `⚠️ ${errorType} error occurred`;
        this.logEvent(message, 'warning');
        
        this.updateStatistics();
    }
    
    startProgressTracking(config) {
        const totalDuration = config.numShots * config.shotInterval * 1000; // Convert to ms
        const updateInterval = 100; // Update every 100ms
        
        const progressTimer = setInterval(() => {
            if (!this.isRunning) {
                clearInterval(progressTimer);
                return;
            }
            
            const elapsed = Date.now() - this.simulationStartTime;
            const progress = Math.min((elapsed / totalDuration) * 100, 100);
            
            document.getElementById('simulation-progress').style.width = `${progress}%`;
            
            if (progress >= 100 && this.stats.shotsFired >= config.numShots) {
                clearInterval(progressTimer);
                setTimeout(() => this.stopSimulation(), 1000); // Auto-stop after completion
            }
        }, updateInterval);
    }
    
    updateSimulationTime() {
        if (!this.simulationStartTime || this.isPaused) return;
        
        const elapsed = (Date.now() - this.simulationStartTime) / 1000;
        this.stats.simulationTime = elapsed;
        
        const minutes = Math.floor(elapsed / 60);
        const seconds = Math.floor(elapsed % 60);
        const display = minutes > 0 ? `${minutes}:${seconds.toString().padStart(2, '0')}` : `${seconds}s`;
        
        document.getElementById('simulation-time').textContent = display;
    }
    
    updateStatistics() {
        document.getElementById('shots-fired').textContent = this.stats.shotsFired;
        document.getElementById('impacts-detected').textContent = this.stats.impactsDetected;
        document.getElementById('errors-injected').textContent = this.stats.errorsInjected;
        document.getElementById('sensor-samples').textContent = this.stats.sensorSamples.toLocaleString();
        
        // Calculate accuracy
        const accuracy = this.stats.shotsFired > 0 ? 
            Math.round((this.stats.impactsDetected / this.stats.shotsFired) * 100) : 0;
        document.getElementById('accuracy-rate').textContent = `${accuracy}%`;
    }
    
    resetStats() {
        this.stats = {
            shotsFired: 0,
            impactsDetected: 0,
            errorsInjected: 0,
            sensorSamples: 0,
            simulationTime: 0
        };
        this.updateStatistics();
    }
    
    logEvent(message, type = 'info') {
        const logPanel = document.getElementById('event-log');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span> 
            <span>${message}</span>
        `;
        
        logPanel.appendChild(logEntry);
        logPanel.scrollTop = logPanel.scrollHeight;
        
        // Limit log entries to prevent memory issues
        while (logPanel.children.length > 200) {
            logPanel.removeChild(logPanel.firstChild);
        }
    }
    
    clearLog() {
        const logPanel = document.getElementById('event-log');
        logPanel.innerHTML = `
            <div class="log-entry log-info">
                <span class="log-timestamp">[${new Date().toLocaleTimeString()}]</span> 
                <span>Event log cleared</span>
            </div>
        `;
    }
    
    connectWebSocket() {
        // Try to connect to the LeadVille WebSocket server
        try {
            this.websocket = new WebSocket('ws://localhost:8765');
            
            this.websocket.onopen = () => {
                this.logEvent('🌐 Connected to LeadVille WebSocket server', 'success');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (e) {
                    this.logEvent(`📡 WebSocket: ${event.data}`, 'info');
                }
            };
            
            this.websocket.onclose = () => {
                this.logEvent('🌐 WebSocket connection closed', 'warning');
                this.websocket = null;
            };
            
            this.websocket.onerror = (error) => {
                this.logEvent('🌐 WebSocket connection failed (using simulation mode)', 'warning');
                this.websocket = null;
            };
            
        } catch (error) {
            this.logEvent('🌐 WebSocket not available (using simulation mode)', 'info');
        }
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'simulation_update') {
            // Update statistics from real backend
            const backendStats = data.data;
            if (backendStats.shots_fired !== undefined) {
                this.stats.shotsFired = backendStats.shots_fired;
            }
            if (backendStats.impacts_detected !== undefined) {
                this.stats.impactsDetected = backendStats.impacts_detected;
            }
            if (backendStats.sensor_samples !== undefined) {
                this.stats.sensorSamples = backendStats.sensor_samples;
            }
            this.updateStatistics();
        } else if (data.type === 'event') {
            // Log backend events
            this.logEvent(`📡 ${data.message}`, data.level || 'info');
        }
    }
}

// Initialize the simulation controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const controller = new SimulationController();
    
    // Make controller available globally for debugging
    window.simulationController = controller;
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case ' ':
                    e.preventDefault();
                    if (controller.isRunning) {
                        if (controller.isPaused) {
                            controller.startSimulation();
                        } else {
                            controller.pauseSimulation();
                        }
                    } else {
                        controller.startSimulation();
                    }
                    break;
                case 'Escape':
                    e.preventDefault();
                    controller.stopSimulation();
                    break;
            }
        }
    });
    
    console.log('LeadVille Simulation Controls loaded');
    console.log('Keyboard shortcuts:');
    console.log('  Ctrl/Cmd + Space: Start/Pause simulation');
    console.log('  Ctrl/Cmd + Escape: Stop simulation');
});