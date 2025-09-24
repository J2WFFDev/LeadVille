#!/usr/bin/env python3
"""
Debug script to test what database the FastAPI session is actually using
"""
import sys
import os
sys.path.insert(0, '/home/jrwest/projects/LeadVille/src')

# Test the exact same import path that FastAPI uses
from impact_bridge.database.session import get_db_session
from impact_bridge.database.models import League

print("=== Testing FastAPI Database Session ===")

try:
    print(f"Current working directory: {os.getcwd()}")
    
    # Use the same session method as FastAPI
    session = get_db_session()
    print(f"Session created successfully")
    
    # Test the query
    leagues = session.query(League).all()
    print(f"Found {len(leagues)} leagues:")
    
    for league in leagues:
        print(f"  - {league.id}: {league.name} ({league.abbreviation})")
    
    session.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")