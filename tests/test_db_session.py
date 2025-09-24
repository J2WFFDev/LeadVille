#!/usr/bin/env python3
"""Test database session usage patterns"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.impact_bridge.database import init_database, get_database_session
from src.impact_bridge.config import DatabaseConfig

db_config = DatabaseConfig()
db = init_database(db_config)
print('init_database returned:', type(db))
print('has get_session:', hasattr(db, 'get_session'))

session_gen = get_database_session(db_config)
print('get_database_session returned:', type(session_gen))

# Test the correct pattern
print("Testing session access...")
try:
    with get_database_session(db_config) as session:
        print('Session type:', type(session))
        from src.impact_bridge.database.models import User
        users = session.query(User).all()
        print('Query successful, user count:', len(users))
except Exception as e:
    print('Session test failed:', e)

# Test old pattern that's failing
print("Testing old pattern...")
try:
    db_session = get_database_session(db_config)
    print('db_session type:', type(db_session))
    session = db_session.get_session()  # This is what's failing
    print('This should not print')
except Exception as e:
    print('Old pattern failed as expected:', e)