// LeadVille Spectator Dashboard

class SpectatorDashboard {
    constructor() {
        this.privacyMode = true;
        this.lastUpdateTime = new Date();
        this.updateInterval = null;
        this.mockData = {
            stages: [
                { id: 1, name: "Speed Steel Challenge", targets: 6, courseOfFire: "6 rounds minimum, freestyle" },
                { id: 2, name: "Plate Rack Run", targets: 8, courseOfFire: "8 rounds, strong hand only" },
                { id: 3, name: "Steel Challenge", targets: 5, courseOfFire: "5 rounds, weak hand optional" }
            ],
            shooters: [
                { id: 1, name: "J. Smith", number: 42, classification: "A-Class" },
                { id: 2, name: "M. Johnson", number: 15, classification: "A-Class" },
                { id: 3, name: "K. Williams", number: 23, classification: "B-Class" },
                { id: 4, name: "R. Davis", number: 67, classification: "C-Class" },
                { id: 5, name: "L. Brown", number: 89, classification: "B-Class" }
            ],
            impacts: [],
            leaderboard: []
        };
        this.currentStage = 1;
        this.activeShooter = null;
        this.runStartTime = null;
        this.systemStatus = {
            sensors: 'connected',
            timer: 'connected',
            dataQuality: 'excellent'
        };
    }

    init() {
        this.setupEventListeners();
        this.initializeDisplay();
        this.startDataUpdates();
        this.simulateMatchData();
    }

    setupEventListeners() {
        // Privacy mode toggle
        const privacyToggle = document.getElementById('privacy-mode');
        if (privacyToggle) {
            privacyToggle.addEventListener('change', (e) => {
                this.privacyMode = e.target.checked;
                this.updatePrivacyDisplay();
                console.log('Privacy mode:', this.privacyMode ? 'ON' : 'OFF');
            });
        }
    }

    initializeDisplay() {
        this.updateStageInfo();
        this.updateSystemStatus();
        this.updatePrivacyDisplay();
        this.updateLastUpdateTime();
    }

    updatePrivacyDisplay() {
        // In privacy mode, anonymize shooter names
        const shooterElements = document.querySelectorAll('.shooter-name, #active-shooter');
        const currentStage = this.mockData.stages[this.currentStage - 1];
        
        if (this.privacyMode) {
            document.getElementById('active-shooter').textContent = 'Shooter XX';
        } else {
            const activeShooter = this.activeShooter 
                ? this.mockData.shooters.find(s => s.id === this.activeShooter)
                : null;
            document.getElementById('active-shooter').textContent = 
                activeShooter ? `${activeShooter.name} (#${activeShooter.number})` : 'No active shooter';
        }
        
        this.updateLeaderboard();
    }

    updateStageInfo() {
        const currentStage = this.mockData.stages[this.currentStage - 1];
        if (currentStage) {
            document.getElementById('current-stage').textContent = `Stage ${currentStage.id}`;
            document.getElementById('stage-name').textContent = currentStage.name;
            document.getElementById('target-count').textContent = `${currentStage.targets} targets`;
            document.getElementById('course-fire').textContent = currentStage.courseOfFire;
        }
    }

    updateSystemStatus() {
        const statusMap = {
            'connected': { class: 'connected', text: 'Connected' },
            'disconnected': { class: 'disconnected', text: 'Disconnected' },
            'running': { class: 'running', text: 'Running' },
            'ready': { class: 'ready', text: 'Ready' },
            'excellent': { class: 'active', text: 'Excellent' },
            'good': { class: 'ready', text: 'Good' },
            'poor': { class: 'disconnected', text: 'Poor' }
        };

        // Update sensor status
        const sensorStatus = document.getElementById('spectator-sensor-status');
        const sensorInfo = statusMap[this.systemStatus.sensors];
        sensorStatus.textContent = sensorInfo.text;
        sensorStatus.className = `status ${sensorInfo.class}`;

        // Update timer status  
        const timerStatus = document.getElementById('spectator-timer-status');
        const timerInfo = statusMap[this.systemStatus.timer];
        timerStatus.textContent = timerInfo.text;
        timerStatus.className = `status ${timerInfo.class}`;

        // Update data quality
        const dataQuality = document.getElementById('data-quality');
        const qualityInfo = statusMap[this.systemStatus.dataQuality];
        dataQuality.textContent = qualityInfo.text;
        dataQuality.className = `status ${qualityInfo.class}`;

        // Update timer status in match status panel
        const matchTimerStatus = document.getElementById('timer-status');
        if (this.runStartTime) {
            matchTimerStatus.textContent = 'Running';
            matchTimerStatus.className = 'status running';
        } else {
            matchTimerStatus.textContent = 'Ready';
            matchTimerStatus.className = 'status ready';
        }
    }

    updateElapsedTime() {
        if (this.runStartTime) {
            const elapsed = (Date.now() - this.runStartTime) / 1000;
            const minutes = Math.floor(elapsed / 60);
            const seconds = (elapsed % 60).toFixed(2);
            document.getElementById('elapsed-time').textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.padStart(5, '0')}`;
        } else {
            document.getElementById('elapsed-time').textContent = '00:00.00';
        }
    }

    addImpact(time, target, zone) {
        const impact = {
            time: time,
            target: target,
            zone: zone,
            timestamp: Date.now()
        };
        
        this.mockData.impacts.unshift(impact);
        if (this.mockData.impacts.length > 10) {
            this.mockData.impacts.pop();
        }
        
        this.updateImpactsList();
    }

    updateImpactsList() {
        const impactsList = document.getElementById('impact-list');
        if (!impactsList) return;

        impactsList.innerHTML = '';
        
        this.mockData.impacts.forEach(impact => {
            const impactElement = document.createElement('div');
            impactElement.className = 'impact-item';
            
            impactElement.innerHTML = `
                <span class="impact-time">${impact.time}</span>
                <span class="impact-target">${impact.target}</span>
                <span class="impact-zone">${impact.zone}</span>
            `;
            
            impactsList.appendChild(impactElement);
        });
    }

    updateLeaderboard() {
        const leaderboardList = document.getElementById('leaderboard-list');
        if (!leaderboardList) return;

        // Sort leaderboard by time (ascending)
        const sortedLeaderboard = [...this.mockData.leaderboard].sort((a, b) => a.time - b.time);
        
        leaderboardList.innerHTML = '';
        
        sortedLeaderboard.forEach((entry, index) => {
            const position = index + 1;
            const leaderboardElement = document.createElement('div');
            leaderboardElement.className = `leaderboard-item position-${Math.min(position, 3)}`;
            
            const shooter = this.mockData.shooters.find(s => s.id === entry.shooterId);
            const displayName = this.privacyMode ? `Shooter ${shooter.number}` : shooter.name;
            
            leaderboardElement.innerHTML = `
                <span class="position">${position}</span>
                <span class="shooter-name">${displayName}</span>
                <span class="time">${entry.time.toFixed(2)}</span>
                <span class="score">${shooter.classification}</span>
            `;
            
            leaderboardList.appendChild(leaderboardElement);
        });
    }

    updateLastUpdateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        document.getElementById('last-update').textContent = timeString;
        this.lastUpdateTime = now;
    }

    simulateMatchData() {
        // Initialize some mock leaderboard data
        this.mockData.leaderboard = [
            { shooterId: 1, time: 156.23 },
            { shooterId: 2, time: 162.45 },
            { shooterId: 3, time: 168.89 },
            { shooterId: 4, time: 174.12 },
            { shooterId: 5, time: 178.56 }
        ];
        
        this.updateLeaderboard();

        // Simulate some impacts
        setTimeout(() => {
            this.addImpact('01:18.05', 'Target A3', 'Alpha');
        }, 2000);
        
        setTimeout(() => {
            this.addImpact('01:42.17', 'Target B2', 'Charlie');
        }, 5000);
        
        setTimeout(() => {
            this.addImpact('02:15.23', 'Target A1', 'Alpha');
        }, 8000);

        // Simulate active shooter
        setTimeout(() => {
            this.startSimulatedRun(2); // M. Johnson
        }, 10000);
    }

    startSimulatedRun(shooterId) {
        this.activeShooter = shooterId;
        this.runStartTime = Date.now();
        this.updatePrivacyDisplay();
        
        console.log('Started simulated run for shooter:', shooterId);
        
        // Simulate some impacts during the run
        setTimeout(() => {
            this.addImpact('00:03.45', 'Target A1', 'Alpha');
        }, 3000);
        
        setTimeout(() => {
            this.addImpact('00:06.78', 'Target B1', 'Charlie');
        }, 6000);
        
        setTimeout(() => {
            this.addImpact('00:09.12', 'Target C1', 'Alpha');
        }, 9000);
        
        // End run after 15 seconds
        setTimeout(() => {
            this.endSimulatedRun();
        }, 15000);
    }

    endSimulatedRun() {
        if (this.runStartTime) {
            const finalTime = (Date.now() - this.runStartTime) / 1000;
            
            // Update leaderboard with new time
            const existingEntry = this.mockData.leaderboard.find(e => e.shooterId === this.activeShooter);
            if (existingEntry) {
                existingEntry.time = finalTime;
            } else {
                this.mockData.leaderboard.push({
                    shooterId: this.activeShooter,
                    time: finalTime
                });
            }
            
            this.updateLeaderboard();
        }
        
        this.activeShooter = null;
        this.runStartTime = null;
        this.updatePrivacyDisplay();
        
        console.log('Ended simulated run');
        
        // Start another run after a delay
        setTimeout(() => {
            const randomShooter = Math.floor(Math.random() * this.mockData.shooters.length) + 1;
            this.startSimulatedRun(randomShooter);
        }, 20000);
    }

    startDataUpdates() {
        // Update elapsed time every 100ms when a run is active
        this.updateInterval = setInterval(() => {
            this.updateElapsedTime();
            this.updateLastUpdateTime();
            
            // Occasionally update system status
            if (Math.random() < 0.01) {
                this.updateSystemStatus();
            }
        }, 100);
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize spectator dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new SpectatorDashboard();
    dashboard.init();
    
    // Store reference globally for debugging
    window.spectatorDashboard = dashboard;
    
    console.log('LeadVille Spectator Dashboard initialized');
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.spectatorDashboard) {
        window.spectatorDashboard.destroy();
    }
});