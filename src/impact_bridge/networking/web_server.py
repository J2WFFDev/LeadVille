"""Web server with API endpoints for network management."""

import logging
import asyncio
import threading
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from typing import Optional

from .network_manager import NetworkManager
from .network_monitor import NetworkMonitor

logger = logging.getLogger(__name__)


class NetworkWebServer:
    """Web server providing API endpoints for network management."""
    
    def __init__(self, network_manager: NetworkManager, network_monitor: NetworkMonitor):
        """Initialize NetworkWebServer.
        
        Args:
            network_manager: NetworkManager instance
            network_monitor: NetworkMonitor instance
        """
        self.network_manager = network_manager
        self.network_monitor = network_monitor
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for API endpoints
        
        self._setup_routes()
        
    def _setup_routes(self) -> None:
        """Setup web server routes."""
        
        @self.app.route('/')
        def index():
            """Main interface page."""
            return self._get_main_interface()
        
        @self.app.route('/api/network/status')
        def network_status():
            """Get current network status."""
            try:
                status = self.network_manager.get_status()
                monitor_status = self.network_monitor.get_monitoring_status()
                
                return jsonify({
                    "network": status,
                    "monitor": monitor_status,
                    "success": True
                })
            except Exception as e:
                logger.error(f"Failed to get network status: {e}")
                return jsonify({"error": str(e), "success": False}), 500
        
        @self.app.route('/api/network/mode', methods=['POST'])
        def switch_network_mode():
            """Switch network mode."""
            try:
                data = request.get_json() or {}
                mode = data.get('mode')
                
                if mode not in [NetworkManager.MODE_AP, NetworkManager.MODE_CLIENT]:
                    return jsonify({
                        "error": f"Invalid mode. Must be '{NetworkManager.MODE_AP}' or '{NetworkManager.MODE_CLIENT}'",
                        "success": False
                    }), 400
                
                # Handle AP mode switch
                if mode == NetworkManager.MODE_AP:
                    success = self.network_manager.switch_to_ap_mode()
                    
                # Handle Client mode switch
                else:
                    ssid = data.get('ssid')
                    password = data.get('password')
                    
                    if not ssid:
                        return jsonify({
                            "error": "SSID required for client mode",
                            "success": False
                        }), 400
                    
                    success = self.network_manager.switch_to_client_mode(ssid, password)
                
                if success:
                    return jsonify({
                        "message": f"Successfully switched to {mode} mode",
                        "mode": mode,
                        "success": True
                    })
                else:
                    return jsonify({
                        "error": f"Failed to switch to {mode} mode",
                        "success": False
                    }), 500
                    
            except Exception as e:
                logger.error(f"Failed to switch network mode: {e}")
                return jsonify({"error": str(e), "success": False}), 500
        
        @self.app.route('/api/network/scan')
        def scan_networks():
            """Scan for available WiFi networks."""
            try:
                import subprocess
                
                # Use iwlist to scan for networks
                result = subprocess.run(
                    ["sudo", "iwlist", "wlan0", "scan"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                networks = []
                if result.returncode == 0:
                    networks = self._parse_iwlist_output(result.stdout)
                
                return jsonify({
                    "networks": networks,
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"Failed to scan networks: {e}")
                return jsonify({"error": str(e), "success": False}), 500
        
        @self.app.route('/api/network/connectivity')
        def check_connectivity():
            """Check internet connectivity."""
            try:
                has_internet = self.network_manager.has_internet_connectivity()
                return jsonify({
                    "has_internet": has_internet,
                    "success": True
                })
            except Exception as e:
                logger.error(f"Failed to check connectivity: {e}")
                return jsonify({"error": str(e), "success": False}), 500
    
    def _parse_iwlist_output(self, output: str) -> list:
        """Parse iwlist scan output to extract network information."""
        networks = []
        current_network = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if 'Cell' in line and 'Address:' in line:
                # New network found, save previous if exists
                if current_network:
                    networks.append(current_network)
                current_network = {}
                
            elif 'ESSID:' in line:
                essid = line.split('ESSID:')[1].strip().strip('"')
                if essid != "":
                    current_network['ssid'] = essid
                    
            elif 'Quality=' in line:
                # Extract signal quality
                try:
                    quality_part = line.split('Quality=')[1].split()[0]
                    if '/' in quality_part:
                        current, max_val = quality_part.split('/')
                        quality_percent = int((int(current) / int(max_val)) * 100)
                        current_network['quality'] = quality_percent
                except:
                    pass
                    
            elif 'Encryption key:' in line:
                encrypted = 'key:on' in line.lower()
                current_network['encrypted'] = encrypted
        
        # Add last network
        if current_network:
            networks.append(current_network)
            
        # Filter out networks without SSID and sort by quality
        networks = [n for n in networks if 'ssid' in n]
        networks.sort(key=lambda x: x.get('quality', 0), reverse=True)
        
        return networks
    
    def _get_main_interface(self) -> str:
        """Get main web interface HTML."""
        interface_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>LeadVille Bridge - Network Management</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .status-panel {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #007bff;
        }
        .mode-panel {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .mode-card {
            flex: 1;
            padding: 20px;
            border: 2px solid #ddd;
            border-radius: 5px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .mode-card:hover {
            border-color: #007bff;
        }
        .mode-card.active {
            border-color: #28a745;
            background-color: #f8fff8;
        }
        .button {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .button:hover {
            background-color: #0056b3;
        }
        .button:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        .network-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .network-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
        }
        .network-item:hover {
            background-color: #f8f9fa;
        }
        .hidden {
            display: none;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 3px;
            box-sizing: border-box;
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .alert-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .alert-error {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 LeadVille Bridge - Network Management</h1>
        
        <div id="alert" class="alert hidden"></div>
        
        <div class="status-panel">
            <h3>Current Status</h3>
            <div id="status-content">Loading...</div>
        </div>
        
        <div class="mode-panel">
            <div id="ap-mode" class="mode-card" onclick="selectMode('ap')">
                <h4>📡 Access Point Mode</h4>
                <p>Offline mode - Creates WiFi hotspot</p>
                <p><strong>SSID:</strong> LeadVille-Bridge</p>
            </div>
            <div id="client-mode" class="mode-card" onclick="selectMode('client')">
                <h4>🌐 Client Mode</h4>
                <p>Online mode - Connects to existing WiFi</p>
                <p><strong>Requires:</strong> WiFi credentials</p>
            </div>
        </div>
        
        <div id="client-config" class="hidden">
            <h3>WiFi Configuration</h3>
            <div class="form-group">
                <label for="ssid">Network Name (SSID):</label>
                <input type="text" id="ssid" placeholder="Enter WiFi network name">
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" placeholder="Enter WiFi password">
            </div>
            <button class="button" onclick="scanNetworks()">Scan Networks</button>
            <div id="network-list" class="network-list hidden"></div>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button id="apply-btn" class="button" onclick="applyMode()" disabled>
                Apply Network Mode
            </button>
        </div>
    </div>
    
    <script>
        let selectedMode = null;
        let currentStatus = null;
        
        // Load initial status
        loadStatus();
        
        // Refresh status every 10 seconds
        setInterval(loadStatus, 10000);
        
        function loadStatus() {
            fetch('/api/network/status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        currentStatus = data;
                        updateStatusDisplay(data);
                        highlightCurrentMode(data.network.mode);
                    } else {
                        showAlert('Failed to load status: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    showAlert('Network error: ' + error.message, 'error');
                });
        }
        
        function updateStatusDisplay(data) {
            const content = document.getElementById('status-content');
            const network = data.network;
            const connected = network.connected ? '✅ Connected' : '❌ Disconnected';
            
            content.innerHTML = `
                <strong>Mode:</strong> ${network.mode.toUpperCase()}<br>
                <strong>Status:</strong> ${connected}<br>
                ${network.ip_address ? '<strong>IP Address:</strong> ' + network.ip_address + '<br>' : ''}
                ${network.ssid ? '<strong>Network:</strong> ' + network.ssid + '<br>' : ''}
                <strong>Monitoring:</strong> ${data.monitor.is_monitoring ? 'Active' : 'Inactive'}
            `;
        }
        
        function highlightCurrentMode(mode) {
            document.getElementById('ap-mode').classList.remove('active');
            document.getElementById('client-mode').classList.remove('active');
            document.getElementById(mode + '-mode').classList.add('active');
        }
        
        function selectMode(mode) {
            selectedMode = mode;
            
            // Update UI
            document.getElementById('ap-mode').classList.remove('active');
            document.getElementById('client-mode').classList.remove('active');
            document.getElementById(mode + '-mode').classList.add('active');
            
            // Show/hide client config
            const clientConfig = document.getElementById('client-config');
            if (mode === 'client') {
                clientConfig.classList.remove('hidden');
            } else {
                clientConfig.classList.add('hidden');
            }
            
            // Enable apply button
            document.getElementById('apply-btn').disabled = false;
        }
        
        function scanNetworks() {
            showAlert('Scanning for networks...', 'success');
            
            fetch('/api/network/scan')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayNetworks(data.networks);
                    } else {
                        showAlert('Failed to scan networks: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    showAlert('Scan error: ' + error.message, 'error');
                });
        }
        
        function displayNetworks(networks) {
            const listDiv = document.getElementById('network-list');
            listDiv.innerHTML = '';
            
            if (networks.length === 0) {
                listDiv.innerHTML = '<div class="network-item">No networks found</div>';
            } else {
                networks.forEach(network => {
                    const item = document.createElement('div');
                    item.className = 'network-item';
                    item.innerHTML = `
                        <strong>${network.ssid}</strong>
                        ${network.encrypted ? '🔒' : '🔓'}
                        ${network.quality ? ` (${network.quality}%)` : ''}
                    `;
                    item.onclick = () => selectNetwork(network.ssid);
                    listDiv.appendChild(item);
                });
            }
            
            listDiv.classList.remove('hidden');
        }
        
        function selectNetwork(ssid) {
            document.getElementById('ssid').value = ssid;
        }
        
        function applyMode() {
            if (!selectedMode) {
                showAlert('Please select a network mode', 'error');
                return;
            }
            
            const data = { mode: selectedMode };
            
            if (selectedMode === 'client') {
                const ssid = document.getElementById('ssid').value;
                const password = document.getElementById('password').value;
                
                if (!ssid) {
                    showAlert('Please enter WiFi network name', 'error');
                    return;
                }
                
                data.ssid = ssid;
                data.password = password;
            }
            
            showAlert('Switching network mode...', 'success');
            document.getElementById('apply-btn').disabled = true;
            
            fetch('/api/network/mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Network mode switched successfully!', 'success');
                    setTimeout(loadStatus, 2000);
                } else {
                    showAlert('Failed to switch mode: ' + data.error, 'error');
                }
                document.getElementById('apply-btn').disabled = false;
            })
            .catch(error => {
                showAlert('Error: ' + error.message, 'error');
                document.getElementById('apply-btn').disabled = false;
            });
        }
        
        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = 'alert alert-' + type;
            alert.classList.remove('hidden');
            
            if (type === 'success') {
                setTimeout(() => {
                    alert.classList.add('hidden');
                }, 5000);
            }
        }
    </script>
</body>
</html>
        '''
        
        return interface_html
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
        """Run the web server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        logger.info(f"Starting network web server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
        
    def get_app(self) -> Flask:
        """Get the Flask app instance."""
        return self.app