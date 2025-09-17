"""
Database session management and initialization for LeadVille Impact Bridge

SQLite with WAL mode configuration for optimal concurrent access.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base
from ..config import DatabaseConfig


class DatabaseSession:
    """Database session factory with SQLite WAL mode optimization"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._init_engine()
    
    def _init_engine(self):
        """Initialize SQLAlchemy engine with SQLite WAL mode"""
        # Ensure database directory exists
        db_dir = os.path.dirname(self.config.path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Create engine with SQLite optimizations
        self.engine = create_engine(
            f"sqlite:///{self.config.path}",
            echo=self.config.echo,
            poolclass=StaticPool,
            pool_pre_ping=True,
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            }
        )
        
        # Configure SQLite for optimal performance
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Enable WAL mode for better concurrent access
            cursor.execute("PRAGMA journal_mode=WAL")
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            # Optimize for SSD storage
            cursor.execute("PRAGMA synchronous=NORMAL")
            # Increase cache size (10MB)
            cursor.execute("PRAGMA cache_size=10000")
            # Optimize page size
            cursor.execute("PRAGMA page_size=4096")
            # Set busy timeout
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()


# Global database session instance
_db_session: Optional[DatabaseSession] = None


def init_database(config: DatabaseConfig) -> DatabaseSession:
    """Initialize global database session"""
    global _db_session
    _db_session = DatabaseSession(config)
    _db_session.create_tables()
    return _db_session


@contextmanager
def get_database_session(config: Optional[DatabaseConfig] = None) -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup
    
    Usage:
        with get_database_session() as session:
            # Use session here
            pass
    """
    global _db_session
    
    # Initialize if needed
    if _db_session is None and config is not None:
        init_database(config)
    
    if _db_session is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session = _db_session.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_factory() -> Optional[sessionmaker]:
    """Get the session factory for advanced usage"""
    global _db_session
    return _db_session.SessionLocal if _db_session else None