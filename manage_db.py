#!/usr/bin/env python3
"""
Database management script for LeadVille Impact Bridge

Commands:
  init    - Initialize database with tables
  reset   - Drop and recreate all tables
  info    - Show database information
  stats   - Show database statistics
  migrate - Run database migrations
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from impact_bridge.config import DatabaseConfig
from impact_bridge.database import init_database, get_database_session, DatabaseCRUD


def cmd_init(args):
    """Initialize database"""
    config = DatabaseConfig(dir=args.db_dir, file=args.db_file)
    
    # Ensure directory exists
    os.makedirs(config.dir, exist_ok=True)
    
    print(f"Initializing database: {config.path}")
    db_session = init_database(config)
    print("✓ Database initialized successfully")
    
    # Show info
    with get_database_session() as session:
        stats = DatabaseCRUD.get_system_stats(session)
        print(f"✓ Created {len(stats)} tables")


def cmd_reset(args):
    """Reset database (drop and recreate)"""
    config = DatabaseConfig(dir=args.db_dir, file=args.db_file)
    
    if not args.force:
        response = input(f"This will delete ALL data in {config.path}. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
    
    print(f"Resetting database: {config.path}")
    
    # Initialize with fresh tables
    db_session = init_database(config)
    db_session.drop_tables()
    db_session.create_tables()
    
    print("✓ Database reset successfully")


def cmd_info(args):
    """Show database information"""
    config = DatabaseConfig(dir=args.db_dir, file=args.db_file)
    
    if not os.path.exists(config.path):
        print(f"Database does not exist: {config.path}")
        return
    
    print(f"Database: {config.path}")
    print(f"Size: {os.path.getsize(config.path)} bytes")
    
    try:
        with get_database_session(config) as session:
            stats = DatabaseCRUD.get_system_stats(session)
            
            print("\nTable counts:")
            for table, count in stats.items():
                print(f"  {table}: {count}")
                
    except Exception as e:
        print(f"Error reading database: {e}")


def cmd_stats(args):
    """Show detailed database statistics"""
    config = DatabaseConfig(dir=args.db_dir, file=args.db_file)
    
    if not os.path.exists(config.path):
        print(f"Database does not exist: {config.path}")
        return
    
    try:
        with get_database_session(config) as session:
            stats = DatabaseCRUD.get_system_stats(session)
            
            print("=== LeadVille Database Statistics ===")
            print(f"Database: {config.path}")
            print(f"Size: {os.path.getsize(config.path):,} bytes")
            
            print(f"\n📊 Entity Counts:")
            print(f"  Nodes: {stats['nodes']}")
            print(f"  Sensors: {stats['sensors']}")
            print(f"  Targets: {stats['targets']}")
            print(f"  Matches: {stats['matches']}")
            print(f"  Runs: {stats['runs']} ({stats['active_runs']} active)")
            print(f"  Timer Events: {stats['timer_events']:,}")
            print(f"  Sensor Events: {stats['sensor_events']:,}")
            
            total_events = stats['timer_events'] + stats['sensor_events']
            print(f"\n📈 Total Events: {total_events:,}")
            
    except Exception as e:
        print(f"Error reading database: {e}")


def cmd_migrate(args):
    """Run database migrations"""
    import subprocess
    
    # Try alembic command first, then python -m alembic
    alembic_commands = [
        ['alembic', 'upgrade', 'head'],
        ['python3', '-m', 'alembic', 'upgrade', 'head']
    ]
    
    for cmd in alembic_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Database migrations completed successfully")
                if result.stdout:
                    print(result.stdout)
                return
            elif 'alembic' in cmd[0]:
                # Try next command variant
                continue
            else:
                print("✗ Migration failed:")
                print(result.stderr)
                return
                
        except FileNotFoundError:
            # Try next command variant
            continue
    
    print("✗ Alembic not found. Install with: pip install alembic or apt install python3-alembic")


def main():
    parser = argparse.ArgumentParser(description="LeadVille Database Management")
    parser.add_argument('--db-dir', default='./db', help='Database directory')
    parser.add_argument('--db-file', default='bridge.db', help='Database filename')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database')
    
    # Reset command  
    reset_parser = subparsers.add_parser('reset', help='Reset database')
    reset_parser.add_argument('--force', action='store_true', 
                             help='Skip confirmation prompt')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show database info')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run database migrations')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'init':
        cmd_init(args)
    elif args.command == 'reset':
        cmd_reset(args)
    elif args.command == 'info':
        cmd_info(args)
    elif args.command == 'stats':
        cmd_stats(args)
    elif args.command == 'migrate':
        cmd_migrate(args)


if __name__ == '__main__':
    main()