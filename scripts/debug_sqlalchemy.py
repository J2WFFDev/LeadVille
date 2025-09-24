#!/usr/bin/env python3
"""
Debug script to test SQLAlchemy database connection and model mapping
"""
import sys
import os
sys.path.insert(0, '/home/jrwest/projects/LeadVille/src')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from impact_bridge.database.models import League, StageConfig, TargetConfig

# Create engine and session
engine = create_engine("sqlite:///leadville.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()

print("=== Testing SQLAlchemy Connection ===")

try:
    # Test raw SQL query
    print("\n1. Raw SQL query:")
    result = session.execute(text("SELECT COUNT(*) as count FROM leagues"))
    count = result.fetchone()
    print(f"Raw SQL leagues count: {count[0]}")
    
    # Test SQLAlchemy model query
    print("\n2. SQLAlchemy model query:")
    leagues = session.query(League).all()
    print(f"SQLAlchemy leagues count: {len(leagues)}")
    
    for league in leagues:
        print(f"  - {league.id}: {league.name} ({league.abbreviation})")
    
    # Test table existence
    print("\n3. Table inspection:")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Available tables: {tables}")
    
    if 'leagues' in tables:
        columns = inspector.get_columns('leagues')
        print("Leagues table columns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    session.close()

print("\n=== Test Complete ===")