#!/usr/bin/env python3
"""
Console Log Viewer - Python Command Line Interface
Access live console logs from the LeadVille API
"""

import requests
import json
import time
from datetime import datetime

def fetch_logs(limit=10):
    """Fetch logs from the API"""
    try:
        response = requests.get(f'http://localhost:8001/api/logs?limit={limit}')
        if response.status_code == 200:
            return response.json()
        else:
            print(f'❌ API request failed with status: {response.status_code}')
            print(f'Response: {response.text}')
            return []
    except Exception as e:
        print(f'❌ Error accessing API: {e}')
        return []

def display_logs(logs):
    """Display logs in a formatted way"""
    if not logs:
        print('📭 No logs available')
        return
    
    print(f'✅ Retrieved {len(logs)} log entries')
    print('=' * 100)
    
    for i, log in enumerate(logs, 1):
        level = log.get('level', 'UNKNOWN')
        source = log.get('source', 'unknown')
        message = log.get('message', '')
        timestamp = log.get('timestamp', '')
        
        # Color coding for levels
        if level == 'ERROR':
            level_display = f'🔴 {level}'
        elif level == 'WARNING':
            level_display = f'🟡 {level}'
        elif level == 'INFO':
            level_display = f'🔵 {level}'
        elif level == 'DEBUG':
            level_display = f'⚪ {level}'
        else:
            level_display = f'⚫ {level}'
        
        # Parse timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_display = dt.strftime('%H:%M:%S')
        except:
            time_display = timestamp[:19] if len(timestamp) > 19 else timestamp
        
        print(f'{i:2d}. [{level_display:12}] {source:20} | {time_display}')
        
        # Display message with proper wrapping
        if len(message) > 80:
            print(f'    {message[:80]}...')
        else:
            print(f'    {message}')
        print()

def live_monitor(refresh_seconds=3):
    """Live monitoring mode"""
    print(f'🔴 LIVE MONITORING MODE (refreshing every {refresh_seconds}s)')
    print('Press Ctrl+C to stop')
    print('=' * 100)
    
    try:
        while True:
            # Clear screen (works on most terminals)
            print('\033[2J\033[H', end='')
            
            print(f'📡 LeadVille Console Log Monitor - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            print('=' * 100)
            
            logs = fetch_logs(15)  # Get more logs for live view
            display_logs(logs)
            
            print(f'🔄 Next refresh in {refresh_seconds} seconds... (Ctrl+C to stop)')
            time.sleep(refresh_seconds)
            
    except KeyboardInterrupt:
        print('\n\n🛑 Live monitoring stopped')

if __name__ == '__main__':
    import sys
    
    print('🔍 LeadVille Console Log Viewer')
    print('=' * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'live':
        live_monitor()
    else:
        print('📋 Fetching latest console logs...')
        logs = fetch_logs(15)
        display_logs(logs)
        print()
        print('💡 Tip: Run with "live" argument for continuous monitoring')
        print('   Example: python3 console_viewer.py live')