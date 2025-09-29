#!/usr/bin/env python3
"""
Real-Time Shot Test Monitor
Live monitoring of shot/impact events with immediate correlation analysis
"""

import asyncio
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import argparse
import signal
from dataclasses import dataclass, asdict

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class LiveEvent:
    timestamp: datetime
    event_type: str  # 'SHOT', 'IMPACT', 'START', 'STOP'
    device_id: str
    details: Dict[str, Any]
    raw_data: Optional[str] = None

class RealTimeShotMonitor:
    """Real-time monitoring of shot test events"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.db_path = project_root / "db" / "leadville.db"  # Configuration database
        self.samples_db_path = project_root / "logs" / "bt50_samples.db"  # Samples database (PRIMARY)
        self.logs_dir = project_root / "logs"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Event tracking
        self.recent_events: List[LiveEvent] = []
        self.shot_count = 0
        self.impact_count = 0
        self.correlations = []
        self.running = True
        
        # Database tracking
        self.last_timer_id = 0
        self.last_sensor_id = 0
        
        # File tracking
        self.monitored_files = {}
        
        print("🎯 LeadVille Real-Time Shot Monitor")
        print("=" * 50)
        print("✅ Monitoring database for new events...")
        print("✅ Watching log files for real-time data...")
        print("🔥 Ready for shot testing!")
        print("\nPress Ctrl+C to stop monitoring\n")
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Get initial database state
        self._get_initial_state()
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_database()),
            asyncio.create_task(self._monitor_log_files()),
            asyncio.create_task(self._correlation_analyzer()),
            asyncio.create_task(self._status_reporter())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self.logger.info("🛑 Monitoring stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Stopping monitor...")
        self.running = False
    
    def _get_initial_state(self):
        """Get current database state to track new events"""
        if not self.db_path.exists():
            self.logger.warning(f"Database not found: {self.db_path}")
            return
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get last timer event ID
            cursor.execute("SELECT MAX(id) FROM timer_events")
            result = cursor.fetchone()
            self.last_timer_id = result[0] if result[0] else 0
            
            # Get last sensor event ID
            cursor.execute("SELECT MAX(id) FROM sensor_events")
            result = cursor.fetchone()  
            self.last_sensor_id = result[0] if result[0] else 0
            
            conn.close()
            
            self.logger.info(f"📊 Initial state: timer_events={self.last_timer_id}, sensor_events={self.last_sensor_id}")
            
        except Exception as e:
            self.logger.error(f"Error getting initial state: {e}")
    
    async def _monitor_database(self):
        """Monitor database for new events"""
        while self.running:
            try:
                await self._check_new_database_events()
                await asyncio.sleep(0.5)  # Check every 500ms
            except Exception as e:
                self.logger.error(f"Database monitoring error: {e}")
                await asyncio.sleep(1)
    
    async def _check_new_database_events(self):
        """Check for new database events"""
        if not self.db_path.exists():
            return
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Check for new timer events
            cursor.execute("""
                SELECT id, ts_utc, type, raw
                FROM timer_events 
                WHERE id > ?
                ORDER BY id
            """, (self.last_timer_id,))
            
            new_timer_events = cursor.fetchall()
            for event_id, ts_utc, event_type, raw_data in new_timer_events:
                timestamp = datetime.fromisoformat(ts_utc.replace('Z', '+00:00'))
                
                # Parse raw data
                details = {'event_type': event_type}
                if raw_data:
                    try:
                        parsed = json.loads(raw_data)
                        details.update(parsed)
                    except:
                        details['raw'] = raw_data
                
                event = LiveEvent(
                    timestamp=timestamp,
                    event_type=event_type,
                    device_id=details.get('device_id', f'timer_{event_id}'),
                    details=details,
                    raw_data=raw_data
                )
                
                await self._process_live_event(event)
                self.last_timer_id = event_id
            
            # Check for new sensor events
            cursor.execute("""
                SELECT id, ts_utc, sensor_id, magnitude, features_json
                FROM sensor_events
                WHERE id > ?
                ORDER BY id
            """, (self.last_sensor_id,))
            
            new_sensor_events = cursor.fetchall()
            for event_id, ts_utc, sensor_id, magnitude, features_json in new_sensor_events:
                timestamp = datetime.fromisoformat(ts_utc.replace('Z', '+00:00'))
                
                details = {
                    'sensor_id': sensor_id,
                    'magnitude': magnitude
                }
                
                if features_json:
                    try:
                        features = json.loads(features_json)
                        details.update(features)
                    except:
                        pass
                
                event = LiveEvent(
                    timestamp=timestamp,
                    event_type='IMPACT',
                    device_id=str(sensor_id),
                    details=details,
                    raw_data=features_json
                )
                
                await self._process_live_event(event)
                self.last_sensor_id = event_id
            
            conn.close()
            
        except Exception as e:
            self.logger.debug(f"Database check error: {e}")
    
    async def _monitor_log_files(self):
        """Monitor log files for real-time events"""
        while self.running:
            try:
                await self._check_log_files()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Log monitoring error: {e}")
                await asyncio.sleep(2)
    
    async def _check_log_files(self):
        """Check log files for new events"""
        # Monitor debug logs
        debug_dir = self.logs_dir / "debug"
        if debug_dir.exists():
            for log_file in debug_dir.glob("*.log"):
                await self._check_log_file_updates(log_file)
        
        # Monitor console logs  
        console_dir = self.logs_dir / "console"
        if console_dir.exists():
            for log_file in console_dir.glob("*.log"):
                await self._check_log_file_updates(log_file)
    
    async def _check_log_file_updates(self, log_file: Path):
        """Check individual log file for updates"""
        try:
            stat = log_file.stat()
            current_size = stat.st_size
            
            # Track file size to detect new content
            if str(log_file) not in self.monitored_files:
                self.monitored_files[str(log_file)] = current_size
                return
            
            last_size = self.monitored_files[str(log_file)]
            if current_size <= last_size:
                return  # No new content
            
            # Read new content
            with open(log_file, 'r') as f:
                f.seek(last_size)
                new_lines = f.readlines()
            
            # Process new lines
            for line in new_lines:
                await self._parse_log_line(line.strip(), log_file.name)
            
            self.monitored_files[str(log_file)] = current_size
            
        except Exception as e:
            self.logger.debug(f"Error checking {log_file}: {e}")
    
    async def _parse_log_line(self, line: str, filename: str):
        """Parse log line for events"""
        line_lower = line.lower()
        
        # Look for shot events
        if any(keyword in line_lower for keyword in ['shot detected', 'amg shot', 'timer shot']):
            await self._parse_log_shot(line, filename)
        
        # Look for impact events
        elif any(keyword in line_lower for keyword in ['impact detected', 'sensor impact', 'magnitude']):
            await self._parse_log_impact(line, filename)
        
        # Look for timer events
        elif any(keyword in line_lower for keyword in ['timer start', 'timer stop', 'beep']):
            await self._parse_log_timer_event(line, filename)
    
    async def _parse_log_shot(self, line: str, filename: str):
        """Parse shot event from log line"""
        try:
            # Extract timestamp if available
            parts = line.split(' - ')
            if len(parts) >= 3:
                timestamp_str = parts[0]
                timestamp = datetime.fromisoformat(timestamp_str.replace(',', '.'))
                message = parts[-1].strip()
            else:
                timestamp = datetime.now()
                message = line
            
            event = LiveEvent(
                timestamp=timestamp,
                event_type='SHOT',
                device_id=f'log_{filename}',
                details={'message': message, 'source': 'log'},
                raw_data=line
            )
            
            await self._process_live_event(event)
            
        except Exception as e:
            self.logger.debug(f"Error parsing shot from log: {e}")
    
    async def _parse_log_impact(self, line: str, filename: str):
        """Parse impact event from log line"""
        try:
            # Extract timestamp if available
            parts = line.split(' - ')
            if len(parts) >= 3:
                timestamp_str = parts[0]
                timestamp = datetime.fromisoformat(timestamp_str.replace(',', '.'))
                message = parts[-1].strip()
            else:
                timestamp = datetime.now()
                message = line
            
            # Try to extract magnitude
            magnitude = 0.0
            import re
            mag_match = re.search(r'magnitude[:\s]+(\d+\.?\d*)', message.lower())
            if mag_match:
                magnitude = float(mag_match.group(1))
            
            event = LiveEvent(
                timestamp=timestamp,
                event_type='IMPACT',
                device_id=f'log_{filename}',
                details={'magnitude': magnitude, 'message': message, 'source': 'log'},
                raw_data=line
            )
            
            await self._process_live_event(event)
            
        except Exception as e:
            self.logger.debug(f"Error parsing impact from log: {e}")
    
    async def _parse_log_timer_event(self, line: str, filename: str):
        """Parse timer control events from log line"""
        try:
            line_lower = line.lower()
            
            if 'start' in line_lower:
                event_type = 'START'
            elif 'stop' in line_lower:
                event_type = 'STOP'
            else:
                event_type = 'TIMER_EVENT'
            
            # Extract timestamp if available
            parts = line.split(' - ')
            if len(parts) >= 3:
                timestamp_str = parts[0]
                timestamp = datetime.fromisoformat(timestamp_str.replace(',', '.'))
                message = parts[-1].strip()
            else:
                timestamp = datetime.now()
                message = line
            
            event = LiveEvent(
                timestamp=timestamp,
                event_type=event_type,
                device_id=f'log_{filename}',
                details={'message': message, 'source': 'log'},
                raw_data=line
            )
            
            await self._process_live_event(event)
            
        except Exception as e:
            self.logger.debug(f"Error parsing timer event from log: {e}")
    
    async def _process_live_event(self, event: LiveEvent):
        """Process a new live event"""
        # Add to recent events (keep last 100)
        self.recent_events.append(event)
        if len(self.recent_events) > 100:
            self.recent_events.pop(0)
        
        # Update counters
        if event.event_type == 'SHOT':
            self.shot_count += 1
            print(f"🎯 SHOT #{self.shot_count} detected at {event.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"   Device: {event.device_id}")
            if 'shot_time' in event.details:
                print(f"   Shot Time: {event.details['shot_time']:.3f}s")
        
        elif event.event_type == 'IMPACT':
            self.impact_count += 1
            magnitude = event.details.get('magnitude', 0)
            print(f"💥 IMPACT #{self.impact_count} detected at {event.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"   Sensor: {event.device_id}, Magnitude: {magnitude:.1f}")
        
        elif event.event_type in ['START', 'STOP']:
            print(f"⏱️  TIMER {event.event_type} at {event.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
        
        # Trigger correlation analysis
        await asyncio.sleep(0.1)  # Brief delay to allow correlations
    
    async def _correlation_analyzer(self):
        """Continuous correlation analysis"""
        while self.running:
            try:
                await self._analyze_recent_correlations()
                await asyncio.sleep(2)  # Analyze every 2 seconds
            except Exception as e:
                self.logger.error(f"Correlation analysis error: {e}")
                await asyncio.sleep(5)
    
    async def _analyze_recent_correlations(self):
        """Analyze recent events for correlations"""
        if len(self.recent_events) < 2:
            return
        
        # Look for recent shot/impact pairs
        recent_shots = [e for e in self.recent_events[-20:] if e.event_type == 'SHOT']
        recent_impacts = [e for e in self.recent_events[-20:] if e.event_type == 'IMPACT']
        
        for shot in recent_shots:
            best_impact = None
            best_time_diff = float('inf')
            
            for impact in recent_impacts:
                time_diff = (impact.timestamp - shot.timestamp).total_seconds()
                
                # Look for impacts 0-2 seconds after shot
                if 0 <= time_diff <= 2.0 and time_diff < best_time_diff:
                    best_impact = impact
                    best_time_diff = time_diff
            
            if best_impact and best_time_diff < 1.0:
                # Check if we've already reported this correlation
                correlation_key = f"{shot.timestamp.isoformat()}_{best_impact.timestamp.isoformat()}"
                if correlation_key not in [c.get('key') for c in self.correlations]:
                    
                    correlation = {
                        'key': correlation_key,
                        'shot': shot,
                        'impact': best_impact,
                        'time_diff': best_time_diff,
                        'quality': self._get_correlation_quality(best_time_diff)
                    }
                    self.correlations.append(correlation)
                    
                    # Report correlation
                    quality_emoji = {'excellent': '🎯', 'good': '✅', 'fair': '⚠️', 'poor': '❌'}
                    emoji = quality_emoji.get(correlation['quality'], '❓')
                    
                    print(f"\n{emoji} CORRELATION DETECTED!")
                    print(f"   Shot→Impact delay: {best_time_diff:.3f}s ({correlation['quality']})")
                    print(f"   Shot device: {shot.device_id}")
                    print(f"   Impact sensor: {best_impact.device_id}")
                    magnitude = best_impact.details.get('magnitude', 0)
                    print(f"   Impact magnitude: {magnitude:.1f}")
                    print()
    
    def _get_correlation_quality(self, time_diff: float) -> str:
        """Determine correlation quality based on time difference"""
        if time_diff <= 0.2:
            return 'excellent'
        elif time_diff <= 0.5:
            return 'good'
        elif time_diff <= 1.0:
            return 'fair'
        else:
            return 'poor'
    
    async def _status_reporter(self):
        """Periodic status reporting"""
        while self.running:
            await asyncio.sleep(30)  # Report every 30 seconds
            
            if self.shot_count > 0 or self.impact_count > 0:
                correlations = len(self.correlations)
                correlation_rate = (correlations / max(self.shot_count, 1)) * 100
                
                print(f"\n📊 STATUS UPDATE:")
                print(f"   Shots: {self.shot_count}, Impacts: {self.impact_count}")
                print(f"   Correlations: {correlations} ({correlation_rate:.1f}% success rate)")
                print(f"   Monitoring active for {(datetime.now() - self.start_time).seconds // 60} minutes")
                print()
    
    def generate_session_report(self) -> Dict[str, Any]:
        """Generate session summary report"""
        return {
            'session_start': getattr(self, 'start_time', datetime.now()).isoformat(),
            'session_end': datetime.now().isoformat(),
            'total_shots': self.shot_count,
            'total_impacts': self.impact_count,
            'total_correlations': len(self.correlations),
            'correlation_rate': (len(self.correlations) / max(self.shot_count, 1)) * 100,
            'correlations': [
                {
                    'time_diff': c['time_diff'],
                    'quality': c['quality'],
                    'shot_device': c['shot'].device_id,
                    'impact_device': c['impact'].device_id,
                    'shot_timestamp': c['shot'].timestamp.isoformat(),
                    'impact_timestamp': c['impact'].timestamp.isoformat()
                }
                for c in self.correlations
            ],
            'recent_events': [asdict(e) for e in self.recent_events[-50:]]  # Last 50 events
        }


async def main():
    parser = argparse.ArgumentParser(description='LeadVille Real-Time Shot Monitor')
    parser.add_argument('--project-root', type=str, default='/home/jrwest/projects/LeadVille', help='Project root directory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    project_root = Path(args.project_root)
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)
    
    # Start monitoring
    monitor = RealTimeShotMonitor(project_root)
    monitor.start_time = datetime.now()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        pass
    finally:
        # Generate session report
        report = monitor.generate_session_report()
        
        # Save session report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"shot_monitor_session_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Session report saved: {report_file}")
        print("👋 Monitoring stopped!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")