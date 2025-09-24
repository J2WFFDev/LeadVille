"""
Database session utilities for LeadVille FastAPI endpoints
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import DatabaseConfig
import os
from pathlib import Path

# Create a simple session factory without relying on the global variable
_session_factory = None

def get_db_session():
    """Get a database session for use in FastAPI endpoints"""
    global _session_factory
    
    if _session_factory is None:
        try:
            # Determine project root and use bridge.db (which has the correct schema)
            project_root = Path(__file__).parent.parent.parent.parent
            
            # Use leadville.db as the primary database with configuration data
            database_config = DatabaseConfig(
                dir=str(project_root / "db"),
                file="leadville.db",
                enable_ingest=True,
                echo=False
            )
            
            # Create engine directly
            db_url = f"sqlite:///{database_config.path}"
            print(f"Creating database connection to: {db_url}")
            
            engine = create_engine(db_url, echo=False)
            _session_factory = sessionmaker(bind=engine)
            
            print(f"Session factory created successfully")
            
        except Exception as e:
            print(f"Failed to create session factory: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    return _session_factory()