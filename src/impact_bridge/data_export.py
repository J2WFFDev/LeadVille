"""Data export and analytics module for LeadVille Impact Bridge.

Provides comprehensive data export capabilities with CSV, NDJSON, and Parquet formats.
Supports batch export, match archiving, and data offload functionality.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import shutil
import sqlite3
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Iterator, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

# Schema version for NDJSON exports
EXPORT_SCHEMA_VERSION = "1.0.0"


class DataExporter:
    """Comprehensive data export functionality for LeadVille Impact Bridge."""
    
    def __init__(
        self,
        export_dir: str = "exports",
        enable_parquet: bool = True,
        compression: str = "gzip",
        batch_size: int = 10000
    ):
        self.export_dir = Path(export_dir)
        self.enable_parquet = enable_parquet
        self.compression = compression
        self.batch_size = batch_size
        
        # Ensure export directory exists
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different export types
        (self.export_dir / "csv").mkdir(exist_ok=True)
        (self.export_dir / "ndjson").mkdir(exist_ok=True)
        (self.export_dir / "archives").mkdir(exist_ok=True)
        if self.enable_parquet:
            (self.export_dir / "parquet").mkdir(exist_ok=True)
    
    def export_run_data_csv(
        self,
        log_files: List[Path],
        output_file: Optional[str] = None,
        include_debug: bool = False
    ) -> Path:
        """Export run data as CSV with one row per run containing all data.
        
        Args:
            log_files: List of log files to process
            output_file: Optional output filename
            include_debug: Whether to include debug data
            
        Returns:
            Path to the exported CSV file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"run_data_{timestamp}.csv"
        
        output_path = self.export_dir / "csv" / output_file
        
        # Process logs and aggregate by runs
        runs = self._aggregate_runs_from_logs(log_files, include_debug)
        
        # Write CSV with comprehensive run data
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if not runs:
                # Write empty CSV with headers
                writer = csv.writer(csvfile)
                writer.writerow(self._get_csv_headers())
                logger.info(f"Exported empty CSV to {output_path}")
                return output_path
            
            writer = csv.DictWriter(csvfile, fieldnames=self._get_csv_headers())
            writer.writeheader()
            
            for run_data in runs:
                writer.writerow(run_data)
        
        logger.info(f"Exported {len(runs)} runs to CSV: {output_path}")
        return output_path
    
    def export_ndjson(
        self,
        log_files: List[Path],
        output_file: Optional[str] = None,
        include_raw_data: bool = True,
        filter_events: Optional[List[str]] = None
    ) -> Path:
        """Export data as NDJSON with schema versioning for raw analysis.
        
        Args:
            log_files: List of log files to process
            output_file: Optional output filename
            include_raw_data: Whether to include raw sensor data
            filter_events: Optional list of event types to include
            
        Returns:
            Path to the exported NDJSON file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"raw_data_{timestamp}.jsonl"
        
        output_path = self.export_dir / "ndjson" / output_file
        
        with open(output_path, 'w', encoding='utf-8') as jsonlfile:
            # Write schema header
            schema_record = {
                "_type": "schema",
                "_version": EXPORT_SCHEMA_VERSION,
                "_timestamp": datetime.now(timezone.utc).isoformat(),
                "_description": "LeadVille Impact Bridge export data",
                "fields": {
                    "timestamp_iso": "ISO8601 timestamp",
                    "event_type": "Type of event (shot_detected, impact_detected, etc.)",
                    "device": "Device type (Timer, Sensor, Bridge)",
                    "device_id": "Device identifier",
                    "device_position": "Physical position of device",
                    "details": "Event details",
                    "raw_data": "Raw device data (if available)",
                    "session_id": "Session identifier",
                    "seq": "Sequence number"
                }
            }
            json.dump(schema_record, jsonlfile, separators=(',', ':'))
            jsonlfile.write('\n')
            
            # Process and write log data
            event_count = 0
            for record in self._process_logs_for_ndjson(log_files, include_raw_data, filter_events):
                json.dump(record, jsonlfile, separators=(',', ':'))
                jsonlfile.write('\n')
                event_count += 1
        
        logger.info(f"Exported {event_count} events to NDJSON: {output_path}")
        return output_path
    
    def export_parquet(
        self,
        log_files: List[Path],
        output_file: Optional[str] = None,
        partition_by: Optional[str] = None
    ) -> Path:
        """Export data as Parquet for analytics (batch export).
        
        Args:
            log_files: List of log files to process
            output_file: Optional output filename
            partition_by: Optional column to partition by ('date', 'session', etc.)
            
        Returns:
            Path to the exported Parquet file
        """
        if not self.enable_parquet:
            raise ValueError("Parquet export is disabled")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_data_{timestamp}.parquet"
        
        output_path = self.export_dir / "parquet" / output_file
        
        # Convert log data to DataFrame
        df = self._logs_to_dataframe(log_files)
        
        if df.empty:
            logger.warning("No data to export to Parquet")
            # Create empty parquet file with schema
            df = pd.DataFrame(columns=self._get_parquet_columns())
        
        # Save as Parquet with optional partitioning
        if partition_by and partition_by in df.columns:
            df.to_parquet(
                output_path,
                engine='pyarrow',
                compression=self.compression,
                partition_cols=[partition_by]
            )
        else:
            df.to_parquet(
                output_path,
                engine='pyarrow',
                compression=self.compression
            )
        
        logger.info(f"Exported {len(df)} records to Parquet: {output_path}")
        return output_path
    
    def create_match_archive(
        self,
        match_id: str,
        log_files: List[Path],
        database_path: Optional[Path] = None,
        include_all_formats: bool = True
    ) -> Path:
        """Create comprehensive match archive with all data formats.
        
        Args:
            match_id: Unique identifier for the match
            log_files: List of log files to include
            database_path: Optional path to database file
            include_all_formats: Whether to include all export formats
            
        Returns:
            Path to the created archive
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"match_{match_id}_{timestamp}.zip"
        archive_path = self.export_dir / "archives" / archive_name
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            # Add original log files
            for log_file in log_files:
                if log_file.exists():
                    archive.write(log_file, f"logs/{log_file.name}")
            
            # Add database if provided
            if database_path and database_path.exists():
                archive.write(database_path, f"database/{database_path.name}")
            
            if include_all_formats:
                # Create and add CSV export
                csv_file = self.export_run_data_csv(log_files, f"match_{match_id}_runs.csv")
                archive.write(csv_file, f"exports/{csv_file.name}")
                
                # Create and add NDJSON export
                ndjson_file = self.export_ndjson(log_files, f"match_{match_id}_raw.jsonl")
                archive.write(ndjson_file, f"exports/{ndjson_file.name}")
                
                # Create and add Parquet export if enabled
                if self.enable_parquet:
                    parquet_file = self.export_parquet(log_files, f"match_{match_id}_analytics.parquet")
                    archive.write(parquet_file, f"exports/{parquet_file.name}")
            
            # Add metadata
            metadata = {
                "match_id": match_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": EXPORT_SCHEMA_VERSION,
                "log_files": [f.name for f in log_files],
                "database_included": database_path is not None,
                "formats_included": ["logs", "csv", "ndjson"] + (["parquet"] if self.enable_parquet else [])
            }
            archive.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        logger.info(f"Created match archive: {archive_path}")
        return archive_path
    
    def offload_data(
        self,
        source_dir: Path,
        cutoff_date: datetime,
        archive_name: Optional[str] = None,
        delete_source: bool = False
    ) -> Path:
        """Data offload feature - archive old data for storage.
        
        Args:
            source_dir: Directory containing data to offload
            cutoff_date: Files older than this date will be archived
            archive_name: Optional name for the archive
            delete_source: Whether to delete source files after archiving
            
        Returns:
            Path to the created archive
        """
        if not archive_name:
            cutoff_str = cutoff_date.strftime("%Y%m%d")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"offload_before_{cutoff_str}_{timestamp}.zip"
        
        archive_path = self.export_dir / "archives" / archive_name
        files_archived = 0
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)
                    
                    if file_mtime < cutoff_date:
                        # Add to archive maintaining directory structure
                        relative_path = file_path.relative_to(source_dir)
                        archive.write(file_path, relative_path)
                        files_archived += 1
                        
                        # Delete source file if requested
                        if delete_source:
                            file_path.unlink()
            
            # Add offload metadata
            metadata = {
                "offload_type": "data_offload",
                "cutoff_date": cutoff_date.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_directory": str(source_dir),
                "files_archived": files_archived,
                "delete_source": delete_source
            }
            archive.writestr("offload_metadata.json", json.dumps(metadata, indent=2))
        
        logger.info(f"Data offload complete: {files_archived} files archived to {archive_path}")
        return archive_path
    
    def _aggregate_runs_from_logs(
        self,
        log_files: List[Path],
        include_debug: bool = False
    ) -> List[Dict[str, Any]]:
        """Aggregate run data from log files."""
        runs = []
        current_run = None
        
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            try:
                # Process different log file types
                if log_file.suffix == '.jsonl':
                    for record in self._read_jsonl_file(log_file):
                        event_type = record.get('type', record.get('event_type', ''))
                        
                        if 'Timer Start' in record.get('details', ''):
                            # Start new run
                            current_run = self._init_run_record(record)
                        elif current_run and 'Shot detected' in record.get('details', ''):
                            current_run['shots_detected'] += 1
                            current_run['last_shot_time'] = record.get('timestamp_iso', '')
                        elif current_run and 'Impact detected' in record.get('details', ''):
                            current_run['impacts_detected'] += 1
                            current_run['last_impact_time'] = record.get('timestamp_iso', '')
                        elif current_run and 'StringSummary' in event_type:
                            # Finish current run
                            self._finalize_run_record(current_run, record)
                            runs.append(current_run)
                            current_run = None
                
                elif log_file.suffix == '.csv':
                    # Process CSV log files
                    runs.extend(self._process_csv_log(log_file))
                    
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {e}")
        
        # Handle incomplete run
        if current_run:
            runs.append(current_run)
        
        return runs
    
    def _process_logs_for_ndjson(
        self,
        log_files: List[Path],
        include_raw_data: bool,
        filter_events: Optional[List[str]]
    ) -> Iterator[Dict[str, Any]]:
        """Process log files for NDJSON export."""
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            try:
                if log_file.suffix == '.jsonl':
                    for record in self._read_jsonl_file(log_file):
                        # Add schema version and export metadata
                        export_record = {
                            "_schema_version": EXPORT_SCHEMA_VERSION,
                            "_exported_at": datetime.now(timezone.utc).isoformat(),
                            "_source_file": log_file.name,
                            **record
                        }
                        
                        # Filter by event type if specified
                        event_type = record.get('type', record.get('event_type', ''))
                        if filter_events and event_type not in filter_events:
                            continue
                        
                        # Include raw data if requested and available
                        if not include_raw_data and 'raw_data' in export_record:
                            del export_record['raw_data']
                        
                        yield export_record
                        
            except Exception as e:
                logger.error(f"Error processing log file {log_file} for NDJSON: {e}")
    
    def _logs_to_dataframe(self, log_files: List[Path]) -> pd.DataFrame:
        """Convert log files to pandas DataFrame for Parquet export."""
        records = []
        
        for log_file in log_files:
            if not log_file.exists():
                continue
            
            try:
                if log_file.suffix == '.jsonl':
                    for record in self._read_jsonl_file(log_file):
                        # Flatten record for tabular format
                        flat_record = self._flatten_record(record)
                        records.append(flat_record)
                        
            except Exception as e:
                logger.error(f"Error processing log file {log_file} for DataFrame: {e}")
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Convert timestamp columns to datetime
        timestamp_cols = [col for col in df.columns if 'timestamp' in col.lower()]
        for col in timestamp_cols:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception:
                pass
        
        return df
    
    def _read_jsonl_file(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """Read JSONL file line by line."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON in {file_path}: {line[:100]}...")
        except Exception as e:
            logger.error(f"Error reading JSONL file {file_path}: {e}")
    
    def _init_run_record(self, start_record: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new run record."""
        return {
            'run_id': f"run_{start_record.get('seq', 0)}",
            'start_time': start_record.get('timestamp_iso', ''),
            'start_device': start_record.get('device', ''),
            'start_device_id': start_record.get('device_id', ''),
            'shots_detected': 0,
            'impacts_detected': 0,
            'duration_seconds': 0.0,
            'last_shot_time': '',
            'last_impact_time': '',
            'end_time': '',
            'correlation_success_rate': 0.0,
            'status': 'active'
        }
    
    def _finalize_run_record(self, run_record: Dict[str, Any], end_record: Dict[str, Any]) -> None:
        """Finalize a run record with end data."""
        run_record['end_time'] = end_record.get('timestamp_iso', '')
        run_record['status'] = 'completed'
        
        # Parse duration from details if available
        details = end_record.get('details', '')
        if 'String Time:' in details:
            try:
                duration_str = details.split('String Time:')[1].split('s')[0].strip()
                run_record['duration_seconds'] = float(duration_str)
            except (IndexError, ValueError):
                pass
        
        # Calculate correlation success rate
        if run_record['shots_detected'] > 0:
            run_record['correlation_success_rate'] = (
                run_record['impacts_detected'] / run_record['shots_detected']
            )
    
    def _process_csv_log(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process CSV log file for run data."""
        runs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                current_run = None
                
                for row in reader:
                    event_type = row.get('Type', row.get('type', ''))
                    
                    if 'Timer Start' in row.get('Details', ''):
                        current_run = self._init_run_record(row)
                    elif current_run and 'Shot detected' in row.get('Details', ''):
                        current_run['shots_detected'] += 1
                    elif current_run and 'Impact detected' in row.get('Details', ''):
                        current_run['impacts_detected'] += 1
                    elif current_run and 'StringSummary' in event_type:
                        self._finalize_run_record(current_run, row)
                        runs.append(current_run)
                        current_run = None
                
                if current_run:
                    runs.append(current_run)
                    
        except Exception as e:
            logger.error(f"Error processing CSV log {file_path}: {e}")
        
        return runs
    
    def _flatten_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested record for tabular format."""
        flat = {}
        
        for key, value in record.items():
            if isinstance(value, dict):
                # Flatten nested dictionaries
                for nested_key, nested_value in value.items():
                    flat[f"{key}_{nested_key}"] = nested_value
            elif isinstance(value, list):
                # Convert lists to strings for tabular format
                flat[key] = json.dumps(value) if value else None
            else:
                flat[key] = value
        
        return flat
    
    def _get_csv_headers(self) -> List[str]:
        """Get CSV headers for run data export."""
        return [
            'run_id', 'start_time', 'end_time', 'duration_seconds',
            'start_device', 'start_device_id', 'shots_detected', 'impacts_detected',
            'last_shot_time', 'last_impact_time', 'correlation_success_rate', 'status'
        ]
    
    def _get_parquet_columns(self) -> List[str]:
        """Get column names for Parquet export schema."""
        return [
            'timestamp_iso', 'event_type', 'device', 'device_id', 'device_position',
            'details', 'seq', 'session_id', 'raw_data_type', 'raw_data_value'
        ]


def create_export_cli():
    """Create command-line interface for data export."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LeadVille Data Export Tool')
    parser.add_argument('--export-dir', default='exports', help='Export directory')
    parser.add_argument('--log-dir', default='logs', help='Logs directory')
    parser.add_argument('--format', choices=['csv', 'ndjson', 'parquet', 'all'], 
                       default='all', help='Export format')
    parser.add_argument('--match-id', help='Create match archive with ID')
    parser.add_argument('--offload', action='store_true', help='Create data offload archive')
    parser.add_argument('--days-old', type=int, default=30, 
                       help='Days old for offload (default: 30)')
    parser.add_argument('--delete-source', action='store_true', 
                       help='Delete source files after offload')
    
    return parser


if __name__ == "__main__":
    # CLI usage
    parser = create_export_cli()
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize exporter
    exporter = DataExporter(export_dir=args.export_dir)
    
    # Find log files
    log_dir = Path(args.log_dir)
    log_files = []
    for pattern in ['*.jsonl', '*.csv', '*.log']:
        log_files.extend(log_dir.rglob(pattern))
    
    if args.offload:
        # Data offload
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=args.days_old)
        archive_path = exporter.offload_data(
            log_dir, cutoff_date, delete_source=args.delete_source
        )
        print(f"Data offload complete: {archive_path}")
    
    elif args.match_id:
        # Match archive
        archive_path = exporter.create_match_archive(args.match_id, log_files)
        print(f"Match archive created: {archive_path}")
    
    else:
        # Regular export
        if args.format in ['csv', 'all']:
            csv_path = exporter.export_run_data_csv(log_files)
            print(f"CSV export: {csv_path}")
        
        if args.format in ['ndjson', 'all']:
            ndjson_path = exporter.export_ndjson(log_files)
            print(f"NDJSON export: {ndjson_path}")
        
        if args.format in ['parquet', 'all'] and exporter.enable_parquet:
            parquet_path = exporter.export_parquet(log_files)
            print(f"Parquet export: {parquet_path}")