#!/usr/bin/env python3
"""Database management CLI for LeadVille Impact Bridge."""

import argparse
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from impact_bridge.config import DatabaseConfig
from impact_bridge.database import (
    initialize_database,
    reset_database,
    get_database_info,
)


def cmd_init(args):
    """Initialize database schema."""
    config = DatabaseConfig(
        dir=args.db_dir,
        file=args.db_file,
        echo_sql=args.verbose
    )
    
    print(f"Initializing database: {config.dir}/{config.file}")
    initialize_database(config)
    
    info = get_database_info(config)
    print(f"✅ Database initialized successfully")
    print(f"   SQLite version: {info['sqlite_version']}")
    print(f"   Tables created: {len(info['tables'])}")
    print(f"   Database path: {info['database_path']}")


def cmd_reset(args):
    """Reset database (drop and recreate all tables)."""
    config = DatabaseConfig(
        dir=args.db_dir,
        file=args.db_file,
        echo_sql=args.verbose
    )
    
    if not args.force:
        response = input(f"⚠️  This will delete all data in {config.dir}/{config.file}. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Reset cancelled.")
            return
    
    print(f"Resetting database: {config.dir}/{config.file}")
    reset_database(config)
    print("✅ Database reset successfully")


def cmd_info(args):
    """Show database information."""
    config = DatabaseConfig(
        dir=args.db_dir,
        file=args.db_file
    )
    
    try:
        info = get_database_info(config)
        
        print(f"📊 Database Information")
        print(f"=" * 40)
        print(f"Path: {info['database_path']}")
        print(f"SQLite version: {info['sqlite_version']}")
        print(f"File size: {info['file_size_mb']} MB ({info['file_size_bytes']} bytes)")
        print(f"\n📊 Tables:")
        
        if info['tables']:
            for table, count in info['tables'].items():
                print(f"   {table}: {count} records")
        else:
            print("   No tables found (database may not be initialized)")
            
    except Exception as e:
        print(f"❌ Error getting database info: {e}")
        print("   Database may not exist. Run 'init' command first.")


def cmd_export_schema(args):
    """Export database schema as JSON."""
    # This would require additional SQLAlchemy introspection
    # For now, just export the table info
    config = DatabaseConfig(
        dir=args.db_dir,
        file=args.db_file
    )
    
    try:
        info = get_database_info(config)
        schema_info = {
            "database_info": {
                "sqlite_version": info['sqlite_version'],
                "tables": info['tables']
            },
            "generated_at": str(info.get('generated_at', 'unknown'))
        }
        
        output_file = args.output or f"{config.dir}/schema.json"
        with open(output_file, 'w') as f:
            json.dump(schema_info, f, indent=2)
        
        print(f"✅ Schema exported to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error exporting schema: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LeadVille Impact Bridge Database Management",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument(
        "--db-dir", 
        default="./db",
        help="Database directory (default: ./db)"
    )
    parser.add_argument(
        "--db-file",
        default="bridge.db", 
        help="Database filename (default: bridge.db)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (show SQL queries)"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize database schema")
    init_parser.set_defaults(func=cmd_init)
    
    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset database (drop and recreate tables)")
    reset_parser.add_argument(
        "--force", 
        action="store_true",
        help="Skip confirmation prompt"
    )
    reset_parser.set_defaults(func=cmd_reset)
    
    # Info command  
    info_parser = subparsers.add_parser("info", help="Show database information")
    info_parser.set_defaults(func=cmd_info)
    
    # Export schema command
    export_parser = subparsers.add_parser("export-schema", help="Export database schema")
    export_parser.add_argument(
        "-o", "--output",
        help="Output file (default: <db_dir>/schema.json)"
    )
    export_parser.set_defaults(func=cmd_export_schema)
    
    # Parse arguments and run command
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()