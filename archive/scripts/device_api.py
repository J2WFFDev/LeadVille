#!/usr/bin/env python3
"""
LeadVille Device API Server
Flask-SocketIO server providing REST API and WebSocket support for console log streaming.
Configured for original LeadVille folder structure.
"""

import os
import sys
import json
import time
import glob
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Web framework imports
try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    from flask_socketio import SocketIO, emit
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("💡 Install with: pip install flask flask-cors flask-socketio")
    sys.exit(1)

class LeadVilleAPI:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'leadville-console-logs-2024'
        
        # Enable CORS for all domains
        CORS(self.app, origins="*")
        
        # Initialize Socket.IO with CORS support
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins="*",
            async_mode='threading'
        )
        
        # Log directories for original LeadVille structure
        self.log_dirs = [
            str(project_root / "logs/console"),     # Console logs first priority
            str(project_root / "logs/debug"),      # Debug logs second  
            str(project_root / "logs/main"),       # Main logs third
        ]
        
        self.setup_routes()
        self.setup_websocket_events()
        self.setup_auth_routes()
        
    def setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'project': 'LeadVille Impact Bridge',
                'version': '2.0.0'
            })
        
        @self.app.route('/api/logs', methods=['GET'])
        def get_logs():
            """Get recent logs from original LeadVille structure"""
            try:
                limit = request.args.get('limit', 100, type=int)
                logs = self.fetch_logs(limit)
                
                return jsonify(logs)
                
            except Exception as e:
                return jsonify({
                    'error': f'Failed to fetch logs: {str(e)}',
                    'logs': []
                }), 500
    
    def setup_websocket_events(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect', namespace='/ws/logs')
        def handle_connect():
            print(f"🔌 Client connected to /ws/logs namespace")
            emit('status', {'message': 'Connected to LeadVille log stream'})
        
        @self.socketio.on('disconnect', namespace='/ws/logs')
        def handle_disconnect():
            print(f"🔌 Client disconnected from /ws/logs namespace")
        
        @self.socketio.on('request_logs', namespace='/ws/logs')
        def handle_log_request(data):
            """Handle log request from client"""
            try:
                limit = data.get('limit', 50)
                logs = self.fetch_logs(limit)
                emit('log_batch', {'logs': logs})
            except Exception as e:
                emit('error', {'message': f'Failed to fetch logs: {str(e)}'})
    
    def setup_auth_routes(self):
        """Setup authentication routes"""
        try:
            import sys
            sys.path.insert(0, str(project_root))
            from src.impact_bridge.auth.api import create_auth_routes
            create_auth_routes(self.app)
            print("✅ Authentication routes enabled")
        except ImportError as e:
            print(f"⚠️  Authentication not available: {e}")
    
    def fetch_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch logs from original LeadVille log directories
        Returns list of parsed log entries
        """
        all_logs = []
        
        for log_dir in self.log_dirs:
            if not os.path.exists(log_dir):
                continue
                
            # Get all log files from this directory
            log_patterns = [
                os.path.join(log_dir, '*.log'),
                os.path.join(log_dir, '*.ndjson'),
                os.path.join(log_dir, '*.csv')
            ]
            
            for pattern in log_patterns:
                log_files = glob.glob(pattern)
                
                # Sort by modification time (newest first)
                log_files.sort(key=os.path.getmtime, reverse=True)
                
                # Process most recent files first
                for log_file in log_files[:5]:  # Limit to 5 most recent files per pattern
                    try:
                        entries = self.parse_log_file(log_file, limit)
                        all_logs.extend(entries)
                        
                        # Stop once we have enough logs
                        if len(all_logs) >= limit:
                            break
                            
                    except Exception as e:
                        print(f"⚠️ Error parsing {log_file}: {e}")
                        continue
                
                if len(all_logs) >= limit:
                    break
            
            if len(all_logs) >= limit:
                break
        
        # Sort all logs by timestamp (newest first) and limit
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return all_logs[:limit]
    
    def parse_log_file(self, file_path: str, max_entries: int = 100) -> List[Dict[str, Any]]:
        """
        Parse a log file and return structured log entries
        Supports multiple formats: console logs, debug logs, NDJSON, CSV
        """
        entries = []
        file_name = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Process lines in reverse order (newest first)
            for line in reversed(lines[-max_entries:]):
                line = line.strip()
                if not line:
                    continue
                    
                entry = self.parse_log_entry(line, file_name)
                if entry:
                    entries.append(entry)
                    
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")
            
        return entries
    
    def parse_log_entry(self, line: str, source_file: str) -> Dict[str, Any]:
        """
        Parse a single log line into structured format
        Handles multiple log formats
        """
        try:
            # Try NDJSON format first
            if line.startswith('{'):
                try:
                    data = json.loads(line)
                    return {
                        'timestamp': data.get('timestamp', datetime.now().isoformat()),
                        'level': data.get('level', 'INFO'),
                        'source': data.get('source', source_file),
                        'message': data.get('message', line),
                        'raw': line
                    }
                except json.JSONDecodeError:
                    pass
            
            # Try console log format: [YYYY-MM-DD HH:MM:SS] LEVEL: message
            if line.startswith('[') and ']' in line:
                try:
                    # Extract timestamp
                    end_bracket = line.find(']')
                    timestamp_str = line[1:end_bracket]
                    remainder = line[end_bracket + 1:].strip()
                    
                    # Extract level and message
                    if ':' in remainder:
                        level_part, message = remainder.split(':', 1)
                        level = level_part.strip()
                        message = message.strip()
                    else:
                        level = 'INFO'
                        message = remainder
                    
                    # Determine source from message content or filename
                    source = source_file
                    if 'FixedBridge' in message:
                        source = 'FixedBridge'
                    elif 'bleak' in message:
                        source = 'bleak.backends.bluezdbus.manager'
                    elif 'BT50' in message:
                        source = 'BT50Sensor'
                    
                    return {
                        'timestamp': timestamp_str,
                        'level': level,
                        'source': source,
                        'message': message,
                        'raw': line
                    }
                except (ValueError, IndexError):
                    pass
            
            # Fallback: treat as plain message
            return {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'source': source_file,
                'message': line,
                'raw': line
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing log line: {e}")
            return None
    
    def run(self, host='0.0.0.0', port=8001, debug=False):
        """Start the API server"""
        print("=" * 60)
        print("🚀 LeadVille Device API Server Starting")
        print("=" * 60)
        print(f"📊 Project: LeadVille Impact Bridge (Original)")
        print(f"🌐 Host: {host}:{port}")
        print(f"📁 Log directories:")
        for log_dir in self.log_dirs:
            exists = "✅" if os.path.exists(log_dir) else "❌"
            print(f"   {exists} {log_dir}")
        print()
        print("🌐 API Endpoints:")
        print(f"   📊 Health: http://{host}:{port}/api/health")
        print(f"   📝 Logs: http://{host}:{port}/api/logs")
        print(f"   🔌 WebSocket: ws://{host}:{port}/ws/logs")
        print(f"   🔐 Login: POST http://{host}:{port}/api/auth/login")
        print(f"   🔑 Auth Health: http://{host}:{port}/api/auth/health")
        print()
        print("🎯 Frontend URLs:")
        print(f"   📱 React App: http://{host}:3001")
        print(f"   📝 Console: http://{host}:3001/#/console") 
        print("=" * 60)
        
        try:
            self.socketio.run(
                self.app,
                host=host,
                port=port,
                debug=debug,
                allow_unsafe_werkzeug=True
            )
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")


def main():
    """Main entry point"""
    api = LeadVilleAPI()
    api.run()


if __name__ == '__main__':
    main()