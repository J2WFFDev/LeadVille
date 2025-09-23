#!/usr/bin/env python3
"""
🔍 LeadVille Console Log Viewer - LATEST VERSION
==================================================
A Python CLI tool for viewing LeadVille console logs from the CORRECT LeadVille_latest folder

Usage:
    python3 console_viewer_latest.py          # One-time snapshot  
    python3 console_viewer_latest.py live     # Live monitoring mode
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configuration for LeadVille_latest
API_BASE_URL = "http://localhost:8001"
LOG_DIRS = [
    "/home/jrwest/projects/LeadVille_latest/logs/console",  # Console logs (like your screenshot)
    "/home/jrwest/projects/LeadVille_latest/logs/debug",   # Debug logs  
    "/home/jrwest/projects/LeadVille_latest/logs",         # Root logs
]

def get_emoji_for_level(level: str) -> str:
    """Get emoji indicator for log level"""
    level_emojis = {
        'DEBUG': '⚪',
        'INFO': '🔵', 
        'WARNING': '🟡',
        'ERROR': '🔴',
        'CRITICAL': '🟣'
    }
    return level_emojis.get(level.upper(), '⚫')

def fetch_logs() -> List[Dict[str, Any]]:
    """Fetch logs from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/logs", timeout=5)
        response.raise_for_status()
        data = response.json()
        # Handle both list and dict response formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('logs', [])
        else:
            return []
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Is device_api.py running?")
        print("💡 To start: cd /home/jrwest/projects/LeadVille_latest && python3 scripts/device_api.py")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        sys.exit(1)

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display"""
    try:
        # Handle various timestamp formats
        if 'T' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%H:%M:%S')
    except:
        return timestamp_str

def display_logs(logs: List[Dict[str, Any]]) -> None:
    """Display logs in a formatted way"""
    if not logs:
        print("📭 No logs found")
        return
        
    print(f"✅ Retrieved {len(logs)} log entries")
    print("=" * 100)
    
    for i, log in enumerate(logs, 1):
        level = log.get('level', 'INFO')
        source = log.get('source', 'Unknown')
        message = log.get('message', '')
        timestamp = log.get('timestamp', '')
        
        emoji = get_emoji_for_level(level)
        formatted_time = format_timestamp(timestamp)
        
        # Truncate long source names
        if len(source) > 25:
            source = source[:22] + "..."
            
        # Truncate very long messages
        if len(message) > 80:
            message = message[:77] + "..."
        
        print(f"{i:2}. [{emoji} {level:<8}] {source:<25} | {formatted_time}")
        print(f"    {message}")
        print()

def live_monitor() -> None:
    """Run in live monitoring mode"""
    print("🔴 LIVE MONITORING MODE (refreshing every 3s)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Clear screen (works on most terminals)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("=" * 100)
            print(f"📡 LeadVille Console Log Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 100)
            
            logs = fetch_logs()
            display_logs(logs)
            
            print("🔄 Next refresh in 3 seconds... (Ctrl+C to stop)")
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
        sys.exit(0)

def main():
    """Main entry point"""
    print("🔍 LeadVille Console Log Viewer")
    print("==================================================")
    
    # Check if we're in live mode
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'live':
        live_monitor()
    else:
        # One-time snapshot
        logs = fetch_logs()
        print("📊 SNAPSHOT MODE")
        print("=" * 100)
        display_logs(logs)
        print("💡 Use 'python3 console_viewer_latest.py live' for continuous monitoring")

if __name__ == "__main__":
    main()