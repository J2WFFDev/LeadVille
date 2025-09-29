#!/usr/bin/env python3
"""
LeadVille Shot Test Analysis Tool
Captures and analyzes shot/impact correlation data from all available sources
"""

import asyncio
import json
import sqlite3
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import argparse
from dataclasses import dataclass

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class ShotEvent:
    timestamp: datetime
    event_type: str  # 'SHOT', 'START', 'STOP'
    device_id: str
    shot_number: Optional[int] = None
    shot_time: Optional[float] = None
    string_time: Optional[float] = None
    raw_data: Optional[str] = None

@dataclass  
class ImpactEvent:
    timestamp: datetime
    sensor_id: str
    magnitude: float
    target_number: Optional[int] = None
    raw_data: Optional[Dict] = None

@dataclass
class CorrelatedEvent:
    shot: Optional[ShotEvent]
    impact: Optional[ImpactEvent]
    time_diff: Optional[float]  # seconds between shot and impact
    correlation_quality: str   # 'excellent', 'good', 'fair', 'poor', 'none'

class LeadVilleShotAnalyzer:
    """Comprehensive shot test analysis tool"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.db_path = project_root / "db" / "leadville.db"  # Configuration database
        self.runtime_db_path = project_root / "db" / "leadville_runtime.db"  # Runtime database (PRIMARY - contains shot data)
        self.logs_dir = project_root / "logs"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Event storage
        self.shot_events: List[ShotEvent] = []
        self.impact_events: List[ImpactEvent] = []
        self.correlated_events: List[CorrelatedEvent] = []
    
    def analyze_shot_test(self, since_minutes: int = 30) -> Dict[str, Any]:
        """Comprehensive analysis of recent shot test data"""
        self.logger.info(f"🔍 Analyzing shot test data from last {since_minutes} minutes...")
        
        cutoff_time = datetime.now() - timedelta(minutes=since_minutes)
        
        # Load data from all sources
        self._load_database_events(cutoff_time)
        self._load_log_file_events(cutoff_time)
        self._load_csv_events(cutoff_time)
        
        # Correlate shots and impacts
        self._correlate_events()
        
        # Generate analysis report
        return self._generate_analysis_report()
    
    def _load_database_events(self, since_time: datetime):
        """Load events from SQLite databases"""
        self.logger.info("📊 Loading events from databases...")
        
        # Load from runtime database (PRIMARY - where bridge writes runtime data)
        self._load_runtime_database_events(since_time)
        
        # Also check configuration database (secondary)
        self._load_config_database_events(since_time)
    
    def _load_runtime_database_events(self, since_time: datetime):
        """Load events from the runtime database (db/leadville_runtime.db)"""
        if not self.runtime_db_path.exists():
            self.logger.warning(f"Runtime database not found: {self.runtime_db_path}")
            return
        
        try:
            conn = sqlite3.connect(str(self.runtime_db_path))
            cursor = conn.cursor()
            
            # Load timer events from runtime database
            cursor.execute("""
                SELECT id, ts_utc, type, raw
                FROM timer_events 
                WHERE datetime(ts_utc) >= ?
                ORDER BY ts_utc
            """, (since_time.isoformat(),))
            
            for row in cursor.fetchall():
                event_id, ts_str, event_type, raw_data = row
                timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                
                # Parse raw data if JSON
                parsed_data = {}
                if raw_data:
                    try:
                        parsed_data = json.loads(raw_data)
                    except:
                        pass
                
                shot_event = ShotEvent(
                    timestamp=timestamp,
                    event_type=event_type,
                    device_id=parsed_data.get('device_id', f'timer_{event_id}'),
                    shot_number=parsed_data.get('current_shot'),
                    shot_time=parsed_data.get('shot_time'),
                    string_time=parsed_data.get('string_time'),
                    raw_data=raw_data
                )
                self.shot_events.append(shot_event)
            
            # Load sensor events (impacts) from runtime database
            cursor.execute("""
                SELECT id, ts_utc, sensor_id, magnitude, features_json
                FROM sensor_events
                WHERE datetime(ts_utc) >= ?
                ORDER BY ts_utc  
            """, (since_time.isoformat(),))
            
            for row in cursor.fetchall():
                event_id, ts_str, sensor_id, magnitude, features_json = row
                timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                
                features = {}
                if features_json:
                    try:
                        features = json.loads(features_json)
                    except:
                        pass
                
                impact_event = ImpactEvent(
                    timestamp=timestamp,
                    sensor_id=str(sensor_id),
                    magnitude=magnitude or 0.0,
                    target_number=features.get('target_number'),
                    raw_data=features
                )
                self.impact_events.append(impact_event)
            
            # Also load from impacts table if it exists
            cursor.execute("""
                SELECT sensor_mac, impact_ts_ns, peak_mag, duration_ms
                FROM impacts
                WHERE datetime(impact_ts_ns/1e9, 'unixepoch') >= ?
                ORDER BY impact_ts_ns  
            """, (since_time.isoformat(),))
            
            for row in cursor.fetchall():
                sensor_mac, impact_ts_ns, peak_mag, duration_ms = row
                timestamp = datetime.fromtimestamp(impact_ts_ns / 1e9)
                
                impact_event = ImpactEvent(
                    timestamp=timestamp,
                    sensor_id=sensor_mac,
                    magnitude=peak_mag or 0.0,
                    raw_data={'duration_ms': duration_ms}
                )
                self.impact_events.append(impact_event)
            
            conn.close()
            self.logger.info(f"✅ Loaded {len(self.shot_events)} timer events, {len(self.impact_events)} impacts from runtime database")
            
        except Exception as e:
            self.logger.error(f"Runtime database loading error: {e}")
    
    def _load_config_database_events(self, since_time: datetime):
        """Load events from the configuration database (db/leadville.db) - secondary check"""
        if not self.db_path.exists():
            self.logger.warning(f"Configuration database not found: {self.db_path}")
            return
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Check if timer_events table exists in config database
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='timer_events'
            """)
            
            if cursor.fetchone():
                # Load timer events from config database (secondary)
                cursor.execute("""
                    SELECT ts_utc, type, raw, id
                    FROM timer_events 
                    WHERE ts_utc >= ?
                    ORDER BY ts_utc
                """, (since_time.isoformat(),))
                
                config_timer_events = 0
                for row in cursor.fetchall():
                    ts_str, event_type, raw_data, event_id = row
                    timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    
                    # Parse raw data if JSON
                    parsed_data = {}
                    if raw_data:
                        try:
                            parsed_data = json.loads(raw_data)
                        except:
                            pass
                    
                    shot_event = ShotEvent(
                        timestamp=timestamp,
                        event_type=event_type,
                        device_id=parsed_data.get('device_id', f'config_timer_{event_id}'),
                        shot_number=parsed_data.get('current_shot'),
                        shot_time=parsed_data.get('shot_time'),
                        string_time=parsed_data.get('string_time'),
                        raw_data=raw_data
                    )
                    self.shot_events.append(shot_event)
                    config_timer_events += 1
                
                if config_timer_events > 0:
                    self.logger.info(f"✅ Also loaded {config_timer_events} timer events from config database")
            
            # Check for sensor events in config database
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sensor_events'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT ts_utc, sensor_id, magnitude, features_json, id
                    FROM sensor_events
                    WHERE ts_utc >= ?
                    ORDER BY ts_utc  
                """, (since_time.isoformat(),))
                
                config_sensor_events = 0
                for row in cursor.fetchall():
                    ts_str, sensor_id, magnitude, features_json, event_id = row
                    timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    
                    features = {}
                    if features_json:
                        try:
                            features = json.loads(features_json)
                        except:
                            pass
                    
                    impact_event = ImpactEvent(
                        timestamp=timestamp,
                        sensor_id=str(sensor_id),
                        magnitude=magnitude,
                        target_number=features.get('target_number'),
                        raw_data=features
                    )
                    self.impact_events.append(impact_event)
                    config_sensor_events += 1
                
                if config_sensor_events > 0:
                    self.logger.info(f"✅ Also loaded {config_sensor_events} impact events from config database")
            
            conn.close()
            
        except Exception as e:
            self.logger.debug(f"Config database check error: {e}")
    
    def _load_log_file_events(self, since_time: datetime):
        """Load events from debug/console log files"""
        self.logger.info("📝 Scanning log files for events...")
        
        # Scan debug logs for shot/impact events
        debug_dir = self.logs_dir / "debug"
        if debug_dir.exists():
            for log_file in debug_dir.glob("*.log"):
                try:
                    # Only check recent log files
                    if log_file.stat().st_mtime < since_time.timestamp():
                        continue
                    
                    with open(log_file, 'r') as f:
                        for line in f:
                            # Look for shot detection patterns
                            if 'shot detected' in line.lower() or 'amg shot' in line.lower():
                                self._parse_log_shot_event(line, log_file.name)
                            
                            # Look for impact detection patterns  
                            if 'impact detected' in line.lower() or 'sensor impact' in line.lower():
                                self._parse_log_impact_event(line, log_file.name)
                                
                except Exception as e:
                    self.logger.debug(f"Error reading {log_file}: {e}")
        
        # Scan console logs
        console_dir = self.logs_dir / "console"
        if console_dir.exists():
            for log_file in console_dir.glob("*.log"):
                try:
                    if log_file.stat().st_mtime < since_time.timestamp():
                        continue
                    
                    with open(log_file, 'r') as f:
                        for line in f:
                            if any(keyword in line.lower() for keyword in ['shot', 'impact', 'beep']):
                                self._parse_console_event(line, log_file.name)
                                
                except Exception as e:
                    self.logger.debug(f"Error reading {log_file}: {e}")
    
    def _parse_log_shot_event(self, line: str, filename: str):
        """Parse shot event from log line"""
        try:
            # Extract timestamp and details from log line
            parts = line.split(' - ')
            if len(parts) >= 3:
                timestamp_str = parts[0]
                timestamp = datetime.fromisoformat(timestamp_str.replace(',', '.'))
                
                # Look for shot details in the message
                message = parts[-1].strip()
                
                shot_event = ShotEvent(
                    timestamp=timestamp,
                    event_type='SHOT',
                    device_id=f'parsed_from_{filename}',
                    raw_data=message
                )
                self.shot_events.append(shot_event)
                
        except Exception as e:
            self.logger.debug(f"Error parsing shot event from: {line[:100]}...")
    
    def _parse_log_impact_event(self, line: str, filename: str):
        """Parse impact event from log line"""
        try:
            # Extract timestamp and details from log line
            parts = line.split(' - ')
            if len(parts) >= 3:
                timestamp_str = parts[0]
                timestamp = datetime.fromisoformat(timestamp_str.replace(',', '.'))
                
                message = parts[-1].strip()
                
                # Try to extract magnitude from message
                magnitude = 0.0
                if 'magnitude' in message.lower():
                    # Look for magnitude value
                    import re
                    mag_match = re.search(r'magnitude[:\s]+(\d+\.?\d*)', message.lower())
                    if mag_match:
                        magnitude = float(mag_match.group(1))
                
                impact_event = ImpactEvent(
                    timestamp=timestamp,
                    sensor_id=f'parsed_from_{filename}',
                    magnitude=magnitude,
                    raw_data={'log_message': message}
                )
                self.impact_events.append(impact_event)
                
        except Exception as e:
            self.logger.debug(f"Error parsing impact event from: {line[:100]}...")
    
    def _parse_console_event(self, line: str, filename: str):
        """Parse events from console logs"""
        # Console logs might have different formats - adapt as needed
        pass
    
    def _load_csv_events(self, since_time: datetime):
        """Load events from CSV log files"""
        self.logger.info("📄 Scanning CSV log files...")
        
        main_dir = self.logs_dir / "main"
        if main_dir.exists():
            for csv_file in main_dir.glob("*.csv"):
                try:
                    if csv_file.stat().st_mtime < since_time.timestamp():
                        continue
                    
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Parse timestamp
                            try:
                                if 'timestamp_iso' in row:
                                    timestamp = datetime.fromisoformat(row['timestamp_iso'])
                                elif 'datetime' in row:
                                    # Handle CSV datetime format
                                    timestamp = self._parse_csv_datetime(row['datetime'])
                                else:
                                    continue
                                
                                if timestamp < since_time:
                                    continue
                                
                                # Classify event type
                                event_type = row.get('type', '').lower()
                                
                                if event_type == 'shot' or 'shot' in row.get('details', '').lower():
                                    shot_event = ShotEvent(
                                        timestamp=timestamp,
                                        event_type='SHOT',
                                        device_id=row.get('device_id', row.get('device', 'unknown')),
                                        raw_data=json.dumps(row)
                                    )
                                    self.shot_events.append(shot_event)
                                
                                elif event_type == 'impact' or 'impact' in row.get('details', '').lower():
                                    # Extract magnitude from details
                                    magnitude = 0.0
                                    details = row.get('details', '')
                                    import re
                                    mag_match = re.search(r'(\d+\.?\d*)', details)
                                    if mag_match:
                                        magnitude = float(mag_match.group(1))
                                    
                                    impact_event = ImpactEvent(
                                        timestamp=timestamp,
                                        sensor_id=row.get('device_id', 'unknown'),
                                        magnitude=magnitude,
                                        raw_data=row
                                    )
                                    self.impact_events.append(impact_event)
                                    
                            except Exception as e:
                                self.logger.debug(f"Error parsing CSV row: {e}")
                                continue
                                
                except Exception as e:
                    self.logger.debug(f"Error reading CSV {csv_file}: {e}")
    
    def _parse_csv_datetime(self, datetime_str: str) -> datetime:
        """Parse CSV datetime format"""
        # Handle format like "09/28/25 11:16:36.123pm"
        import re
        # Add parsing logic for your specific CSV datetime format
        # This is a placeholder - adjust based on your actual CSV format
        return datetime.now()
    
    def _correlate_events(self):
        """Correlate shots with impacts based on timing"""
        self.logger.info("🔗 Correlating shots with impacts...")
        
        # Sort events by timestamp
        self.shot_events.sort(key=lambda x: x.timestamp)
        self.impact_events.sort(key=lambda x: x.timestamp)
        
        # For each shot, find the best matching impact
        for shot in self.shot_events:
            if shot.event_type != 'SHOT':
                continue
                
            best_impact = None
            best_time_diff = float('inf')
            
            # Look for impacts within 3 seconds of the shot
            for impact in self.impact_events:
                time_diff = (impact.timestamp - shot.timestamp).total_seconds()
                
                # Only consider impacts that come after the shot (within reason)
                if -0.5 <= time_diff <= 3.0 and abs(time_diff) < best_time_diff:
                    best_impact = impact
                    best_time_diff = abs(time_diff)
            
            # Determine correlation quality
            correlation_quality = 'none'
            if best_impact:
                if best_time_diff <= 0.2:
                    correlation_quality = 'excellent'
                elif best_time_diff <= 0.5:
                    correlation_quality = 'good'
                elif best_time_diff <= 1.0:
                    correlation_quality = 'fair'
                else:
                    correlation_quality = 'poor'
            
            correlated = CorrelatedEvent(
                shot=shot,
                impact=best_impact,
                time_diff=best_time_diff if best_impact else None,
                correlation_quality=correlation_quality
            )
            self.correlated_events.append(correlated)
        
        # Also add unmatched impacts
        matched_impacts = {c.impact for c in self.correlated_events if c.impact}
        for impact in self.impact_events:
            if impact not in matched_impacts:
                correlated = CorrelatedEvent(
                    shot=None,
                    impact=impact,
                    time_diff=None,
                    correlation_quality='orphaned'
                )
                self.correlated_events.append(correlated)
    
    def _generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        self.logger.info("📊 Generating analysis report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_shots': len([e for e in self.shot_events if e.event_type == 'SHOT']),
                'total_impacts': len(self.impact_events),
                'correlated_pairs': len([c for c in self.correlated_events if c.shot and c.impact]),
                'orphaned_impacts': len([c for c in self.correlated_events if c.impact and not c.shot]),
                'missed_shots': len([c for c in self.correlated_events if c.shot and not c.impact])
            },
            'correlations': [],
            'quality_breakdown': {
                'excellent': 0,
                'good': 0, 
                'fair': 0,
                'poor': 0,
                'none': 0,
                'orphaned': 0
            },
            'raw_events': {
                'shots': [self._shot_to_dict(s) for s in self.shot_events],
                'impacts': [self._impact_to_dict(i) for i in self.impact_events]
            }
        }
        
        # Build correlation details
        for corr in self.correlated_events:
            corr_data = {
                'correlation_quality': corr.correlation_quality,
                'time_diff': corr.time_diff
            }
            
            if corr.shot:
                corr_data['shot'] = self._shot_to_dict(corr.shot)
            
            if corr.impact:
                corr_data['impact'] = self._impact_to_dict(corr.impact)
            
            report['correlations'].append(corr_data)
            
            # Update quality breakdown
            report['quality_breakdown'][corr.correlation_quality] += 1
        
        return report
    
    def _shot_to_dict(self, shot: ShotEvent) -> Dict:
        """Convert ShotEvent to dictionary"""
        return {
            'timestamp': shot.timestamp.isoformat(),
            'event_type': shot.event_type,
            'device_id': shot.device_id,
            'shot_number': shot.shot_number,
            'shot_time': shot.shot_time,
            'string_time': shot.string_time,
            'raw_data': shot.raw_data
        }
    
    def _impact_to_dict(self, impact: ImpactEvent) -> Dict:
        """Convert ImpactEvent to dictionary"""
        return {
            'timestamp': impact.timestamp.isoformat(),
            'sensor_id': impact.sensor_id,
            'magnitude': impact.magnitude,
            'target_number': impact.target_number,
            'raw_data': impact.raw_data
        }
    
    def print_analysis_summary(self, report: Dict[str, Any]):
        """Print human-readable analysis summary"""
        print("\n" + "="*60)
        print("🎯 LEADVILLE SHOT TEST ANALYSIS REPORT")
        print("="*60)
        
        summary = report['summary']
        print(f"\n📊 SUMMARY:")
        print(f"   Total Shots Detected: {summary['total_shots']}")
        print(f"   Total Impacts Detected: {summary['total_impacts']}")
        print(f"   Successfully Correlated: {summary['correlated_pairs']}")
        print(f"   Orphaned Impacts: {summary['orphaned_impacts']}")
        print(f"   Missed Shots: {summary['missed_shots']}")
        
        if summary['total_shots'] > 0:
            correlation_rate = (summary['correlated_pairs'] / summary['total_shots']) * 100
            print(f"   Correlation Rate: {correlation_rate:.1f}%")
        
        quality = report['quality_breakdown']
        print(f"\n🎯 CORRELATION QUALITY:")
        print(f"   Excellent (≤0.2s): {quality['excellent']}")
        print(f"   Good (≤0.5s): {quality['good']}")
        print(f"   Fair (≤1.0s): {quality['fair']}")
        print(f"   Poor (>1.0s): {quality['poor']}")
        print(f"   No Impact Found: {quality['none']}")
        print(f"   Orphaned Impacts: {quality['orphaned']}")
        
        print(f"\n🔗 DETAILED CORRELATIONS:")
        for i, corr in enumerate(report['correlations'][:10], 1):  # Show first 10
            if corr['correlation_quality'] in ['excellent', 'good', 'fair']:
                shot = corr.get('shot', {})
                impact = corr.get('impact', {})
                time_diff = corr.get('time_diff', 0)
                
                print(f"   {i}. Shot→Impact: {time_diff:.3f}s ({corr['correlation_quality']})")
                print(f"      Shot: {shot.get('device_id', 'unknown')} at {shot.get('timestamp', 'unknown')}")
                print(f"      Impact: {impact.get('sensor_id', 'unknown')} magnitude {impact.get('magnitude', 0):.1f}")
        
        if len(report['correlations']) > 10:
            print(f"   ... and {len(report['correlations']) - 10} more")
        
        print(f"\n📝 Report saved with full details available in JSON format")
    
    def save_report(self, report: Dict[str, Any], output_file: Path):
        """Save detailed report to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"📄 Detailed report saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='LeadVille Shot Test Analysis Tool')
    parser.add_argument('--minutes', type=int, default=30, help='Analyze events from last N minutes (default: 30)')
    parser.add_argument('--project-root', type=str, default='/home/jrwest/projects/LeadVille', help='Project root directory')
    parser.add_argument('--output', type=str, help='Output JSON file path (default: shot_analysis_TIMESTAMP.json)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    project_root = Path(args.project_root)
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)
    
    # Default output file
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"shot_analysis_{timestamp}.json"
    
    output_path = Path(args.output)
    
    # Run analysis
    analyzer = LeadVilleShotAnalyzer(project_root)
    report = analyzer.analyze_shot_test(args.minutes)
    
    # Print summary
    analyzer.print_analysis_summary(report)
    
    # Save detailed report
    analyzer.save_report(report, output_path)
    
    print(f"\n🎉 Analysis complete! Use the JSON report for detailed investigation.")


if __name__ == "__main__":
    main()