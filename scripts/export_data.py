#!/usr/bin/env python3
"""
LeadVille Data Export Management Script

This script provides command-line interface for data export and analytics functionality.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from impact_bridge.data_export import DataExporter


def setup_logging(verbose: bool = False):
    """Setup logging for the export script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )


def find_log_files(log_dir: Path, pattern: str = "*") -> list[Path]:
    """Find log files in the specified directory."""
    log_files = []
    
    # Look for different log file types
    if pattern == "*":
        patterns = ['*.jsonl', '*.csv', '*.log']
    else:
        patterns = [f"*{pattern}*.jsonl", f"*{pattern}*.csv", f"*{pattern}*.log"]
    
    for pat in patterns:
        log_files.extend(log_dir.rglob(pat))
    
    # Filter out empty files
    log_files = [f for f in log_files if f.is_file() and f.stat().st_size > 0]
    
    return sorted(log_files)


def export_data(args):
    """Export data in specified formats."""
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"Error: Log directory does not exist: {log_dir}")
        return 1
    
    # Find log files
    log_files = find_log_files(log_dir, args.pattern)
    if not log_files:
        print(f"No log files found in {log_dir}")
        return 1
    
    print(f"Found {len(log_files)} log files to process")
    for f in log_files:
        print(f"  - {f}")
    
    # Initialize exporter
    exporter = DataExporter(
        export_dir=args.export_dir,
        enable_parquet=not args.no_parquet,
        compression=args.compression
    )
    
    try:
        # Export in requested formats
        if args.format in ['csv', 'all']:
            print("\n=== CSV Export ===")
            csv_path = exporter.export_run_data_csv(
                log_files, 
                output_file=args.output,
                include_debug=args.include_debug
            )
            print(f"CSV export completed: {csv_path}")
        
        if args.format in ['ndjson', 'all']:
            print("\n=== NDJSON Export ===")
            ndjson_path = exporter.export_ndjson(
                log_files,
                output_file=args.output,
                include_raw_data=not args.no_raw_data,
                filter_events=args.filter_events.split(',') if args.filter_events else None
            )
            print(f"NDJSON export completed: {ndjson_path}")
        
        if args.format in ['parquet', 'all'] and not args.no_parquet:
            print("\n=== Parquet Export ===")
            parquet_path = exporter.export_parquet(
                log_files,
                output_file=args.output,
                partition_by=args.partition_by
            )
            print(f"Parquet export completed: {parquet_path}")
    
    except Exception as e:
        print(f"Export failed: {e}")
        return 1
    
    print("\nExport completed successfully!")
    return 0


def create_match_archive(args):
    """Create a match archive."""
    log_dir = Path(args.log_dir)
    
    # Find log files
    log_files = find_log_files(log_dir, args.pattern)
    if not log_files:
        print(f"No log files found in {log_dir}")
        return 1
    
    print(f"Creating match archive for: {args.match_id}")
    print(f"Including {len(log_files)} log files")
    
    # Find database file if it exists
    db_path = None
    db_file = Path(args.db_path) if args.db_path else log_dir.parent / "timer_events.db"
    if db_file.exists():
        db_path = db_file
        print(f"Including database: {db_path}")
    
    # Initialize exporter
    exporter = DataExporter(export_dir=args.export_dir)
    
    try:
        archive_path = exporter.create_match_archive(
            match_id=args.match_id,
            log_files=log_files,
            database_path=db_path,
            include_all_formats=not args.logs_only
        )
        print(f"Match archive created: {archive_path}")
        return 0
    
    except Exception as e:
        print(f"Archive creation failed: {e}")
        return 1


def offload_data(args):
    """Offload old data to archive."""
    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"Error: Source directory does not exist: {source_dir}")
        return 1
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=args.days_old)
    
    print(f"Data offload from: {source_dir}")
    print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Delete source files: {args.delete_source}")
    
    if not args.yes:
        response = input("Continue with offload? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Offload cancelled.")
            return 0
    
    # Initialize exporter
    exporter = DataExporter(export_dir=args.export_dir)
    
    try:
        archive_path = exporter.offload_data(
            source_dir=source_dir,
            cutoff_date=cutoff_date,
            archive_name=args.archive_name,
            delete_source=args.delete_source
        )
        print(f"Data offload completed: {archive_path}")
        return 0
    
    except Exception as e:
        print(f"Offload failed: {e}")
        return 1


def list_exports(args):
    """List existing exports."""
    export_dir = Path(args.export_dir)
    if not export_dir.exists():
        print(f"Export directory does not exist: {export_dir}")
        return 0
    
    print(f"Exports in {export_dir}:")
    
    for subdir in ['csv', 'ndjson', 'parquet', 'archives']:
        subdir_path = export_dir / subdir
        if subdir_path.exists():
            files = list(subdir_path.rglob("*"))
            files = [f for f in files if f.is_file()]
            
            if files:
                print(f"\n{subdir.upper()}:")
                for f in sorted(files):
                    size = f.stat().st_size
                    size_str = f"{size:,} bytes"
                    if size > 1024*1024:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    elif size > 1024:
                        size_str = f"{size/1024:.1f} KB"
                    
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    print(f"  {f.name} ({size_str}, {mtime.strftime('%Y-%m-%d %H:%M')})")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='LeadVille Data Export Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all data to CSV and NDJSON
  %(prog)s export --format all
  
  # Export only CSV with debug data
  %(prog)s export --format csv --include-debug
  
  # Create match archive
  %(prog)s archive --match-id "Match_2024_001"
  
  # Offload data older than 30 days
  %(prog)s offload --days-old 30 --delete-source
  
  # List existing exports
  %(prog)s list
        """
    )
    
    parser.add_argument('--export-dir', default='exports', help='Export directory')
    parser.add_argument('--log-dir', default='logs', help='Logs directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--format', choices=['csv', 'ndjson', 'parquet', 'all'], 
                              default='all', help='Export format')
    export_parser.add_argument('--output', help='Output filename (optional)')
    export_parser.add_argument('--pattern', default='*', help='Log file pattern')
    export_parser.add_argument('--include-debug', action='store_true', 
                              help='Include debug data in CSV')
    export_parser.add_argument('--no-raw-data', action='store_true', 
                              help='Exclude raw data from NDJSON')
    export_parser.add_argument('--no-parquet', action='store_true', 
                              help='Disable Parquet export')
    export_parser.add_argument('--compression', default='gzip', 
                              choices=['gzip', 'brotli', 'lz4', 'zstd'],
                              help='Compression for Parquet')
    export_parser.add_argument('--partition-by', help='Partition Parquet by column')
    export_parser.add_argument('--filter-events', help='Comma-separated event types to include')
    
    # Archive command
    archive_parser = subparsers.add_parser('archive', help='Create match archive')
    archive_parser.add_argument('--match-id', required=True, help='Match identifier')
    archive_parser.add_argument('--pattern', default='*', help='Log file pattern')
    archive_parser.add_argument('--db-path', help='Database file path')
    archive_parser.add_argument('--logs-only', action='store_true', 
                               help='Include only log files')
    
    # Offload command
    offload_parser = subparsers.add_parser('offload', help='Offload old data')
    offload_parser.add_argument('--source-dir', default='logs', help='Source directory')
    offload_parser.add_argument('--days-old', type=int, default=30, 
                               help='Days old threshold')
    offload_parser.add_argument('--archive-name', help='Archive filename')
    offload_parser.add_argument('--delete-source', action='store_true', 
                               help='Delete source files')
    offload_parser.add_argument('--yes', '-y', action='store_true', 
                               help='Skip confirmation')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List exports')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    setup_logging(args.verbose)
    
    # Execute command
    if args.command == 'export':
        return export_data(args)
    elif args.command == 'archive':
        return create_match_archive(args)
    elif args.command == 'offload':
        return offload_data(args)
    elif args.command == 'list':
        return list_exports(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())