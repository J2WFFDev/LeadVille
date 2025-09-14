// Range Officer (RO) View Application Logic

const API_BASE_URL = '/v1/ro';

// API client utility
class ROApiClient {
    async get(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API GET error for ${endpoint}:`, error);
            throw error;
        }
    }

    async post(endpoint, data = null) {
        try {
            const options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API POST error for ${endpoint}:`, error);
            throw error;
        }
    }

    async delete(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API DELETE error for ${endpoint}:`, error);
            throw error;
        }
    }
}

class ROTargetManager {
    constructor() {
        this.apiClient = new ROApiClient();
        this.targets = [];
        this.stageLayout = null;
        this.svgElement = null;
        this.currentStage = 'stage1';
        this.hits = [];
        this.initializeTargets();
    }

    async initializeTargets() {
        try {
            // Load stage layouts from API
            const stages = await this.apiClient.get('/stages');
            this.stageConfigs = {};
            
            stages.forEach(stage => {
                this.stageConfigs[stage.stage_id] = stage;
            });

            // Set initial stage
            if (stages.length > 0) {
                this.currentStage = stages[0].stage_id;
                this.targets = stages[0].targets;
            }
            
            this.renderStage();
            this.updateTargetStatusGrid();
        } catch (error) {
            console.error('Failed to load stage layouts:', error);
            // Fallback to demo data
            this.initializeDemoTargets();
        }
    }

    initializeDemoTargets() {
        // Fallback demo data if API is not available
        this.stageConfigs = {
            'stage1': {
                stage_id: 'stage1',
                name: 'Pistol Bay',
                targets: [
                    { id: 1, x: 150, y: 200, status: 'online', label: 'T1' },
                    { id: 2, x: 300, y: 200, status: 'online', label: 'T2' },
                    { id: 3, x: 450, y: 200, status: 'degraded', label: 'T3' },
                    { id: 4, x: 600, y: 200, status: 'online', label: 'T4' },
                    { id: 5, x: 750, y: 200, status: 'offline', label: 'T5' }
                ]
            }
        };
        
        this.currentStage = 'stage1';
        this.targets = this.stageConfigs[this.currentStage].targets;
        this.hits = [];
    }

    async setStage(stageId) {
        try {
            const stage = await this.apiClient.get(`/stages/${stageId}`);
            this.currentStage = stageId;
            this.targets = stage.targets;
            this.hits = []; // Clear hits when changing stage
            this.renderStage();
            this.updateTargetStatusGrid();
        } catch (error) {
            console.error('Failed to load stage:', error);
            // Fallback to demo data
            if (this.stageConfigs[stageId]) {
                this.currentStage = stageId;
                this.targets = this.stageConfigs[stageId].targets;
                this.hits = [];
                this.renderStage();
                this.updateTargetStatusGrid();
            }
        }
    }

    renderStage() {
        const svg = document.getElementById('stage-svg');
        if (!svg) return;

        // Clear existing content
        svg.innerHTML = '';

        // Draw firing line
        const firingLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        firingLine.setAttribute('x1', '50');
        firingLine.setAttribute('y1', '350');
        firingLine.setAttribute('x2', '750');
        firingLine.setAttribute('y2', '350');
        firingLine.setAttribute('stroke', '#667eea');
        firingLine.setAttribute('stroke-width', '3');
        firingLine.setAttribute('stroke-dasharray', '10,5');
        svg.appendChild(firingLine);

        // Add firing line label
        const firingLineLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        firingLineLabel.setAttribute('x', '400');
        firingLineLabel.setAttribute('y', '370');
        firingLineLabel.setAttribute('class', 'target-label');
        firingLineLabel.setAttribute('fill', '#667eea');
        firingLineLabel.textContent = 'FIRING LINE';
        svg.appendChild(firingLineLabel);

        // Draw targets
        this.targets.forEach(target => this.drawTarget(svg, target));

        // Draw existing hits
        this.hits.forEach(hit => this.drawHitMarker(svg, hit));
    }

    drawTarget(svg, target) {
        // Target circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', target.x);
        circle.setAttribute('cy', target.y);
        circle.setAttribute('r', '30');
        circle.setAttribute('class', `target-circle ${target.status}`);
        circle.setAttribute('data-target-id', target.id);
        
        // Add click handler for target interaction
        circle.addEventListener('click', () => this.onTargetClick(target));
        
        svg.appendChild(circle);

        // Target label
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', target.x);
        label.setAttribute('y', target.y + 5);
        label.setAttribute('class', 'target-label');
        label.textContent = target.label;
        svg.appendChild(label);

        // Status indicator (small colored dot)
        const statusDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        statusDot.setAttribute('cx', target.x + 20);
        statusDot.setAttribute('cy', target.y - 20);
        statusDot.setAttribute('r', '5');
        statusDot.setAttribute('fill', this.getStatusColor(target.status));
        statusDot.setAttribute('stroke', 'white');
        statusDot.setAttribute('stroke-width', '2');
        svg.appendChild(statusDot);
    }

    drawHitMarker(svg, hit) {
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        marker.setAttribute('cx', hit.x);
        marker.setAttribute('cy', hit.y);
        marker.setAttribute('r', '6');
        marker.setAttribute('class', `hit-marker ${hit.recent ? 'recent' : ''}`);
        marker.setAttribute('data-hit-id', hit.id);
        
        // Add timestamp tooltip
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = `Hit at ${hit.timestamp}`;
        marker.appendChild(title);
        
        svg.appendChild(marker);
    }

    addHit(targetId, timestamp = null) {
        const target = this.targets.find(t => t.id === targetId);
        if (!target) return;

        const hit = {
            id: Date.now(),
            targetId: targetId,
            x: target.x + (Math.random() - 0.5) * 40, // Random position near target
            y: target.y + (Math.random() - 0.5) * 40,
            timestamp: timestamp || new Date().toLocaleTimeString(),
            recent: true
        };

        this.hits.push(hit);
        
        // Re-render to show new hit
        this.renderStage();
        
        // Remove 'recent' class after animation
        setTimeout(() => {
            hit.recent = false;
            const hitElement = document.querySelector(`[data-hit-id="${hit.id}"]`);
            if (hitElement) {
                hitElement.classList.remove('recent');
            }
        }, 2000);

        return hit;
    }

    onTargetClick(target) {
        console.log(`Target ${target.label} clicked`);
        // Toggle target status for demo purposes
        const statuses = ['online', 'degraded', 'offline'];
        const currentIndex = statuses.indexOf(target.status);
        target.status = statuses[(currentIndex + 1) % statuses.length];
        
        this.renderStage();
        this.updateTargetStatusGrid();
        this.updateSystemStatus();
    }

    updateTargetStatusGrid() {
        const grid = document.getElementById('target-status-grid');
        if (!grid) return;

        grid.innerHTML = '';
        
        this.targets.forEach(target => {
            const badge = document.createElement('div');
            badge.className = `target-badge ${target.status}`;
            badge.textContent = `${target.label}: ${target.status.toUpperCase()}`;
            badge.addEventListener('click', () => this.onTargetClick(target));
            grid.appendChild(badge);
        });
    }

    getStatusColor(status) {
        switch (status) {
            case 'online': return '#28a745';
            case 'degraded': return '#ffc107';
            case 'offline': return '#dc3545';
            default: return '#6c757d';
        }
    }

    getStatusCounts() {
        const counts = { online: 0, degraded: 0, offline: 0 };
        this.targets.forEach(target => {
            counts[target.status]++;
        });
        return counts;
    }
}

class ROStringManager {
    constructor(targetManager) {
        this.targetManager = targetManager;
        this.apiClient = new ROApiClient();
        this.currentString = null;
        this.stringHistory = [];
        this.stringCounter = 1;
        this.isActive = false;
        this.startTime = null;
        this.hits = [];
        
        this.setupEventListeners();
        this.loadStringHistory();
    }

    async loadStringHistory() {
        try {
            const strings = await this.apiClient.get('/strings');
            this.stringHistory = strings.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
            this.updateStringHistory();
            this.updateLastStringSummary();
            
            // Check for active string
            const activeString = await this.apiClient.get('/strings/active');
            if (activeString) {
                this.currentString = activeString;
                this.isActive = true;
                this.startTime = new Date(activeString.start_time);
                this.updateStringDisplay();
                this.updateControls();
            }
        } catch (error) {
            console.error('Failed to load string history:', error);
        }
    }

    setupEventListeners() {
        document.getElementById('start-string')?.addEventListener('click', () => this.startString());
        document.getElementById('stop-string')?.addEventListener('click', () => this.stopString());
        document.getElementById('reset-string')?.addEventListener('click', () => this.resetString());
    }

    async startString() {
        if (this.isActive) return;

        try {
            // Generate shooter name for demo
            const shooterName = `Competitor ${Date.now().toString().slice(-3)}`;
            
            const response = await this.apiClient.post('/strings/start', {
                shooter: shooterName,
                stage_id: this.targetManager.currentStage
            });
            
            if (response.success) {
                this.currentString = response.string;
                this.isActive = true;
                this.startTime = new Date(this.currentString.start_time);
                this.hits = [];
                
                this.updateStringDisplay();
                this.updateControls();
                
                // Simulate hits for demo
                this.simulateHits();
                
                console.log(`String ${this.currentString.id} started via API`);
            }
        } catch (error) {
            console.error('Failed to start string via API:', error);
            // Fallback to local mode
            this.startStringLocal();
        }
    }

    startStringLocal() {
        // Fallback implementation for when API is not available
        this.isActive = true;
        this.startTime = new Date();
        this.hits = [];
        
        this.currentString = {
            id: this.stringCounter,
            start_time: this.startTime.toISOString(),
            end_time: null,
            hits: [],
            shooter: 'Competitor ' + this.stringCounter,
            stage_id: this.targetManager.currentStage,
            status: 'active'
        };

        this.updateStringDisplay();
        this.updateControls();

        this.simulateHits();
        console.log(`String ${this.stringCounter} started locally`);
    }

    async stopString() {
        if (!this.isActive) return;

        try {
            const response = await this.apiClient.post('/strings/complete');
            
            if (response.success) {
                this.currentString = response.string;
                this.isActive = false;
                
                // Load updated history
                await this.loadStringHistory();
                
                this.updateStringDisplay();
                this.updateControls();
                
                console.log(`String ${this.currentString.id} completed via API`);
            }
        } catch (error) {
            console.error('Failed to complete string via API:', error);
            // Fallback to local mode
            this.stopStringLocal();
        }
    }

    stopStringLocal() {
        // Fallback implementation
        this.isActive = false;
        this.currentString.end_time = new Date().toISOString();
        this.currentString.status = 'completed';
        this.currentString.hits = [...this.hits];

        this.stringHistory.unshift({ ...this.currentString });
        
        this.updateStringDisplay();
        this.updateStringHistory();
        this.updateLastStringSummary();
        this.updateControls();
        
        this.stringCounter++;
        console.log(`String ${this.currentString.id} completed locally`);
    }

    async resetString() {
        try {
            if (this.isActive) {
                await this.apiClient.post('/strings/cancel');
            }
        } catch (error) {
            console.error('Failed to cancel string via API:', error);
        }
        
        // Reset local state regardless of API success
        this.isActive = false;
        this.currentString = null;
        this.hits = [];
        this.startTime = null;
        
        // Clear hits from stage
        this.targetManager.hits = [];
        this.targetManager.renderStage();
        
        this.updateStringDisplay();
        this.updateControls();
        
        console.log('String reset');
    }

    simulateHits() {
        if (!this.isActive) return;

        // Simulate random hits during the string
        const hitInterval = setInterval(() => {
            if (!this.isActive) {
                clearInterval(hitInterval);
                return;
            }

            // Random chance of hit
            if (Math.random() < 0.3) {
                const targetId = Math.floor(Math.random() * this.targetManager.targets.length) + 1;
                this.addHit(targetId);
            }
        }, 1500);

        // Auto-stop after 30 seconds for demo
        setTimeout(() => {
            if (this.isActive) {
                this.stopString();
            }
        }, 30000);
    }

    async addHit(targetId) {
        if (!this.isActive) return;

        try {
            // Try to register hit via API if string is active
            if (this.currentString) {
                const response = await this.apiClient.post('/hits', {
                    target_id: targetId,
                    timestamp: new Date().toISOString()
                });
                
                if (response.success) {
                    console.log(`Hit registered via API on target ${targetId}`);
                }
            }
        } catch (error) {
            console.error('Failed to register hit via API:', error);
        }
        
        // Add hit locally regardless of API success
        const timestamp = new Date();
        const hit = {
            id: Date.now(),
            target_id: targetId,
            timestamp: timestamp,
            timeFromStart: timestamp - this.startTime
        };

        this.hits.push(hit);
        
        // Add visual hit marker to stage
        this.targetManager.addHit(targetId, timestamp.toLocaleTimeString());
        
        // Update hit timeline
        this.updateHitTimeline();
        
        console.log(`Hit registered on target ${targetId}`);
    }

    updateStringDisplay() {
        const stringNumber = document.getElementById('current-string-number');
        const startTime = document.getElementById('string-start-time');
        const shooter = document.getElementById('current-shooter');
        const hitCount = document.getElementById('current-hit-count');
        const lastHit = document.getElementById('last-hit-time');

        if (stringNumber) {
            stringNumber.textContent = this.currentString ? this.currentString.id : this.stringCounter;
        }

        if (startTime) {
            if (this.startTime) {
                startTime.textContent = this.startTime.toLocaleTimeString();
            } else if (this.currentString && this.currentString.start_time) {
                startTime.textContent = new Date(this.currentString.start_time).toLocaleTimeString();
            } else {
                startTime.textContent = '--:--:--';
            }
        }

        if (shooter) {
            shooter.textContent = this.currentString ? this.currentString.shooter : 'Ready';
        }

        if (hitCount) {
            hitCount.textContent = this.hits.length;
        }

        if (lastHit) {
            const lastHitTime = this.hits.length > 0 ? 
                this.hits[this.hits.length - 1].timestamp.toLocaleTimeString() : 'None';
            lastHit.textContent = lastHitTime;
        }
    }

    updateHitTimeline() {
        const timeline = document.getElementById('hits-timeline');
        if (!timeline) return;

        timeline.innerHTML = '';

        this.hits.forEach((hit, index) => {
            const marker = document.createElement('div');
            marker.className = 'hit-marker-timeline';
            marker.textContent = hit.target_id || hit.targetId; // Handle both API and local formats
            const hitTime = typeof hit.timestamp === 'string' ? 
                new Date(hit.timestamp).toLocaleTimeString() : 
                hit.timestamp.toLocaleTimeString();
            marker.title = `Target ${hit.target_id || hit.targetId} at ${hitTime}`;
            timeline.appendChild(marker);
        });
    }

    updateControls() {
        const startBtn = document.getElementById('start-string');
        const stopBtn = document.getElementById('stop-string');
        const resetBtn = document.getElementById('reset-string');

        if (startBtn) startBtn.disabled = this.isActive;
        if (stopBtn) stopBtn.disabled = !this.isActive;
        if (resetBtn) resetBtn.disabled = false;
    }

    updateStringHistory() {
        const historyList = document.getElementById('history-list');
        if (!historyList) return;

        historyList.innerHTML = '';

        this.stringHistory.forEach(string => {
            const item = document.createElement('div');
            item.className = 'history-item';
            
            const startTime = typeof string.start_time === 'string' ? 
                new Date(string.start_time) : string.startTime;
            const endTime = typeof string.end_time === 'string' ? 
                new Date(string.end_time) : string.endTime;
            
            let duration = 0;
            if (endTime && startTime) {
                duration = Math.round((endTime - startTime) / 1000);
            }
            
            const hitCount = string.hits ? string.hits.length : 0;
            
            item.innerHTML = `
                <div class="history-item-header">
                    <span class="history-item-id">String #${string.id}</span>
                    <span class="history-item-time">${startTime.toLocaleTimeString()}</span>
                </div>
                <div class="history-item-stats">
                    ${hitCount} hits • ${duration}s • ${string.shooter}
                </div>
            `;
            
            item.addEventListener('click', () => this.showStringDetails(string));
            historyList.appendChild(item);
        });
    }

    updateLastStringSummary() {
        const summaryContainer = document.getElementById('last-string-summary');
        if (!summaryContainer) return;

        if (this.stringHistory.length === 0) {
            summaryContainer.innerHTML = '<div class="summary-placeholder"><p>No completed strings yet</p></div>';
            return;
        }

        const lastString = this.stringHistory[0];
        
        const startTime = typeof lastString.start_time === 'string' ? 
            new Date(lastString.start_time) : lastString.startTime;
        const endTime = typeof lastString.end_time === 'string' ? 
            new Date(lastString.end_time) : lastString.endTime;
        
        let duration = 0;
        if (endTime && startTime) {
            duration = Math.round((endTime - startTime) / 1000);
        }
        
        const hitCount = lastString.hits ? lastString.hits.length : 0;

        summaryContainer.innerHTML = `
            <div class="summary-data">
                <div class="summary-stat">
                    <span class="summary-stat-label">String ID:</span>
                    <span class="summary-stat-value">#${lastString.id}</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Shooter:</span>
                    <span class="summary-stat-value">${lastString.shooter}</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Total Hits:</span>
                    <span class="summary-stat-value">${hitCount}</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Duration:</span>
                    <span class="summary-stat-value">${duration}s</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Start Time:</span>
                    <span class="summary-stat-value">${startTime.toLocaleTimeString()}</span>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">End Time:</span>
                    <span class="summary-stat-value">${endTime ? endTime.toLocaleTimeString() : 'N/A'}</span>
                </div>
            </div>
        `;
    }

    showStringDetails(string) {
        console.log('Showing details for string:', string);
        
        const startTime = typeof string.start_time === 'string' ? 
            new Date(string.start_time) : string.startTime;
        const endTime = typeof string.end_time === 'string' ? 
            new Date(string.end_time) : string.endTime;
        
        let duration = 0;
        if (endTime && startTime) {
            duration = Math.round((endTime - startTime) / 1000);
        }
        
        const hitCount = string.hits ? string.hits.length : 0;
        
        alert(`String #${string.id}\n${hitCount} hits\nDuration: ${duration}s\nShooter: ${string.shooter}`);
    }

    async clearHistory() {
        try {
            await this.apiClient.delete('/data/clear');
            console.log('History cleared via API');
        } catch (error) {
            console.error('Failed to clear history via API:', error);
        }
        
        // Clear local history regardless
        this.stringHistory = [];
        this.updateStringHistory();
        this.updateLastStringSummary();
        console.log('Local history cleared');
    }

    exportData() {
        const data = {
            strings: this.stringHistory,
            stage: this.targetManager.currentStage,
            exportTime: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `leadville-ro-data-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        console.log('Data exported');
    }
}

class ROSystemManager {
    constructor(targetManager, stringManager) {
        this.targetManager = targetManager;
        this.stringManager = stringManager;
        this.setupEventListeners();
        this.updateSystemStatus();
        
        // Update status periodically
        setInterval(() => this.updateSystemStatus(), 5000);
    }

    setupEventListeners() {
        document.getElementById('stage-select')?.addEventListener('change', (e) => {
            this.targetManager.setStage(e.target.value);
            this.updateSystemStatus();
        });

        document.getElementById('refresh-targets')?.addEventListener('click', () => {
            this.refreshTargets();
        });

        document.getElementById('clear-history')?.addEventListener('click', () => {
            this.stringManager.clearHistory();
        });

        document.getElementById('export-data')?.addEventListener('click', () => {
            this.stringManager.exportData();
        });
    }

    refreshTargets() {
        // Simulate refreshing target connections
        this.targetManager.targets.forEach(target => {
            // Random chance to change status
            if (Math.random() < 0.2) {
                const statuses = ['online', 'degraded', 'offline'];
                target.status = statuses[Math.floor(Math.random() * statuses.length)];
            }
        });

        this.targetManager.renderStage();
        this.targetManager.updateTargetStatusGrid();
        this.updateSystemStatus();
        
        console.log('Targets refreshed');
    }

    updateSystemStatus() {
        // System status
        const systemStatus = document.getElementById('system-status');
        if (systemStatus) {
            systemStatus.textContent = 'Online';
            systemStatus.className = 'status-value online';
        }

        // Target status
        const targetCounts = this.targetManager.getStatusCounts();
        const onlineTargets = document.getElementById('online-targets');
        const totalTargets = document.getElementById('total-targets');
        
        if (onlineTargets && totalTargets) {
            onlineTargets.textContent = targetCounts.online;
            totalTargets.textContent = this.targetManager.targets.length;
        }

        // Timer status
        const timerStatus = document.getElementById('timer-status');
        if (timerStatus) {
            timerStatus.textContent = 'Ready';
            timerStatus.className = 'status-value ready';
        }

        // Match status
        const matchStatus = document.getElementById('match-status');
        if (matchStatus) {
            if (this.stringManager.isActive) {
                matchStatus.textContent = 'Active String';
                matchStatus.className = 'status-value running';
            } else {
                matchStatus.textContent = 'Standby';
                matchStatus.className = 'status-value ready';
            }
        }
    }
}

// Initialize the Range Officer application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Range Officer View...');
    
    const targetManager = new ROTargetManager();
    const stringManager = new ROStringManager(targetManager);
    const systemManager = new ROSystemManager(targetManager, stringManager);
    
    // Initial render
    targetManager.renderStage();
    targetManager.updateTargetStatusGrid();
    stringManager.updateStringDisplay();
    systemManager.updateSystemStatus();
    
    console.log('Range Officer View initialized successfully');
    
    // Make managers globally available for debugging
    window.ROApp = {
        targetManager,
        stringManager,
        systemManager
    };
});