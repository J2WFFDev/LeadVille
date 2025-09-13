// LeadVille MVP-1 Application Logic

class SensorManager {
    constructor() {
        this.isActive = false;
        this.sensorInterval = null;
        this.currentTemperature = 20.0; // Starting temperature in Celsius
    }

    start() {
        if (this.isActive) return;
        
        this.isActive = true;
        this.updateStatus('online');
        this.updateSystemStatus('sensor', 'Connected', 'connected');
        
        // Simulate sensor readings every 2 seconds
        this.sensorInterval = setInterval(() => {
            this.simulateReading();
        }, 2000);
        
        console.log('Sensor monitoring started');
    }

    stop() {
        if (!this.isActive) return;
        
        this.isActive = false;
        this.updateStatus('offline');
        this.updateSystemStatus('sensor', 'Disconnected', 'disconnected');
        
        if (this.sensorInterval) {
            clearInterval(this.sensorInterval);
            this.sensorInterval = null;
        }
        
        document.getElementById('temperature').textContent = '--°C';
        console.log('Sensor monitoring stopped');
    }

    simulateReading() {
        // Simulate realistic temperature fluctuations (18-25°C range)
        const variation = (Math.random() - 0.5) * 0.8; // ±0.4°C variation
        this.currentTemperature += variation;
        
        // Keep within realistic bounds
        this.currentTemperature = Math.max(18, Math.min(25, this.currentTemperature));
        
        const displayTemp = this.currentTemperature.toFixed(1);
        document.getElementById('temperature').textContent = `${displayTemp}°C`;
    }

    updateStatus(status) {
        const statusElement = document.getElementById('sensor-status');
        statusElement.textContent = status === 'online' ? 'Online' : 'Offline';
        statusElement.className = `status-indicator ${status}`;
    }

    updateSystemStatus(component, text, className) {
        const element = document.getElementById(`system-${component}-status`);
        if (element) {
            element.textContent = text;
            element.className = className;
        }
    }
}

class TimerManager {
    constructor() {
        this.isRunning = false;
        this.timeLeft = 0; // Time in seconds
        this.timerInterval = null;
        this.defaultMinutes = 5;
        
        // Timer vendor support
        this.currentVendor = 'amg_labs'; // Default vendor
        this.availableVendors = {
            'amg_labs': 'AMG Labs Commander',
            'specialpie': 'SpecialPie Pro Timer'
        };
    }

    start() {
        if (this.isRunning) return;
        
        // If timer is at 0, set it to the input value
        if (this.timeLeft <= 0) {
            const minutes = parseInt(document.getElementById('timer-minutes').value) || this.defaultMinutes;
            this.timeLeft = minutes * 60;
        }
        
        this.isRunning = true;
        this.updateSystemStatus('timer', `${this.availableVendors[this.currentVendor]} - Running`, 'running');
        
        this.timerInterval = setInterval(() => {
            this.tick();
        }, 1000);
        
        this.updateButtons();
        console.log(`Timer started with ${this.currentVendor} vendor`);
    }

    pause() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        this.updateSystemStatus('timer', `${this.availableVendors[this.currentVendor]} - Paused`, 'ready');
        
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        this.updateButtons();
        console.log('Timer paused');
    }

    reset() {
        this.isRunning = false;
        this.timeLeft = 0;
        this.updateSystemStatus('timer', `${this.availableVendors[this.currentVendor]} - Ready`, 'ready');
        
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        this.updateDisplay();
        this.updateButtons();
        console.log('Timer reset');
    }

    switchVendor(vendorId) {
        if (vendorId in this.availableVendors) {
            const oldVendor = this.currentVendor;
            this.currentVendor = vendorId;
            
            // Reset timer when switching vendors for safety
            this.reset();
            
            // Update status display
            this.updateSystemStatus('timer', 
                `${this.availableVendors[vendorId]} - Ready`, 
                'ready'
            );
            
            // Update vendor selector
            document.getElementById('timer-vendor').value = vendorId;
            
            console.log(`Timer vendor switched from ${oldVendor} to ${vendorId}`);
            
            // In a real implementation, this would make an API call to switch the backend
            // For now, just log the change
            return true;
        }
        return false;
    }

    getCurrentVendor() {
        return {
            id: this.currentVendor,
            name: this.availableVendors[this.currentVendor]
        };
    }

    tick() {
        this.timeLeft--;
        this.updateDisplay();
        
        if (this.timeLeft <= 0) {
            this.onTimerComplete();
        }
    }

    onTimerComplete() {
        this.isRunning = false;
        this.timeLeft = 0;
        this.updateSystemStatus('timer', `${this.availableVendors[this.currentVendor]} - Completed`, 'ready');
        
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        this.updateDisplay();
        this.updateButtons();
        
        // Visual and audio notification
        alert('Timer completed!');
        console.log('Timer completed');
    }

    updateDisplay() {
        const hours = Math.floor(this.timeLeft / 3600);
        const minutes = Math.floor((this.timeLeft % 3600) / 60);
        const seconds = this.timeLeft % 60;
        
        const display = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('timer-display').textContent = display;
    }

    updateButtons() {
        const startBtn = document.getElementById('start-timer');
        const pauseBtn = document.getElementById('pause-timer');
        const resetBtn = document.getElementById('reset-timer');
        
        startBtn.disabled = this.isRunning;
        pauseBtn.disabled = !this.isRunning;
        resetBtn.disabled = false;
    }

    updateSystemStatus(component, text, className) {
        const element = document.getElementById(`system-${component}-status`);
        if (element) {
            element.textContent = text;
            element.className = className;
        }
    }
}

class InterfaceManager {
    constructor() {
        this.sensor = new SensorManager();
        this.timer = new TimerManager();
        this.initializeInterface();
    }

    initializeInterface() {
        // Set initial system status
        this.updateSystemStatus('interface', 'Active', 'active');
        
        // Initialize timer display
        this.timer.updateDisplay();
        this.timer.updateButtons();
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('LeadVille MVP-1 Interface initialized');
    }

    setupEventListeners() {
        // Sensor controls
        document.getElementById('start-sensor').addEventListener('click', () => {
            this.sensor.start();
        });
        
        document.getElementById('stop-sensor').addEventListener('click', () => {
            this.sensor.stop();
        });
        
        // Timer controls
        document.getElementById('start-timer').addEventListener('click', () => {
            this.timer.start();
        });
        
        document.getElementById('pause-timer').addEventListener('click', () => {
            this.timer.pause();
        });
        
        document.getElementById('reset-timer').addEventListener('click', () => {
            this.timer.reset();
        });
        
        // Timer vendor switching
        document.getElementById('switch-vendor').addEventListener('click', () => {
            const vendorSelect = document.getElementById('timer-vendor');
            const selectedVendor = vendorSelect.value;
            
            if (this.timer.switchVendor(selectedVendor)) {
                console.log(`Successfully switched to ${selectedVendor} timer`);
            } else {
                console.error(`Failed to switch to ${selectedVendor} timer`);
            }
        });
        
        // Timer input validation
        document.getElementById('timer-minutes').addEventListener('change', (e) => {
            let value = parseInt(e.target.value);
            if (isNaN(value) || value < 0) {
                e.target.value = 0;
            } else if (value > 59) {
                e.target.value = 59;
            }
        });
    }

    updateSystemStatus(component, text, className) {
        const element = document.getElementById(`system-${component}-status`);
        if (element) {
            element.textContent = text;
            element.className = className;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new InterfaceManager();
    console.log('LeadVille MVP-1 Application loaded successfully');
});