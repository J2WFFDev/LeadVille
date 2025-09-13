"""Database engine and session management for LeadVille Impact Bridge."""

import os
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, Engine, event, text
from sqlalchemy.engine import Engine as SQLAlchemyEngine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

from ..config import DatabaseConfig

logger = logging.getLogger(__name__)


def _setup_sqlite_wal_mode(dbapi_connection, connection_record):
    """Enable SQLite WAL mode for better concurrent access."""
    # Enable WAL mode
    dbapi_connection.execute("PRAGMA journal_mode=WAL")
    # Enable foreign keys
    dbapi_connection.execute("PRAGMA foreign_keys=ON")
    # Optimize for better performance
    dbapi_connection.execute("PRAGMA synchronous=NORMAL")
    dbapi_connection.execute("PRAGMA cache_size=10000")
    dbapi_connection.execute("PRAGMA temp_store=MEMORY")


def get_database_url(config: DatabaseConfig) -> str:
    """Generate database URL from configuration."""
    db_dir = Path(config.dir)
    db_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = db_dir / config.file
    return f"sqlite:///{db_path}"


def create_database_engine(config: DatabaseConfig) -> Engine:
    """Create and configure database engine with SQLite WAL mode."""
    database_url = get_database_url(config)
    
    # Create engine with connection pooling and WAL mode
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,  # Allow SQLite use across threads
            "timeout": 30,  # 30 second connection timeout
        },
        pool_pre_ping=True,  # Validate connections before use
        pool_recycle=3600,   # Recycle connections after 1 hour
    )
    
    # Set up WAL mode event listener
    event.listen(engine, "connect", _setup_sqlite_wal_mode)
    
    logger.info(f"Database engine created: {database_url}")
    return engine


# Global engine instance
_engine: Engine = None
_SessionLocal: sessionmaker = None


def get_database_engine(config: DatabaseConfig = None) -> Engine:
    """Get or create the global database engine."""
    global _engine
    
    if _engine is None:
        if config is None:
            # Use default config if none provided
            from ..config import DatabaseConfig
            config = DatabaseConfig()
        
        _engine = create_database_engine(config)
    
    return _engine


def get_session_factory(config: DatabaseConfig = None) -> sessionmaker:
    """Get or create the global session factory."""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_database_engine(config)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal


@contextmanager
def get_database_session(config: DatabaseConfig = None) -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    SessionLocal = get_session_factory(config)
    session = SessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def initialize_database(config: DatabaseConfig = None):
    """Initialize database schema and ensure tables exist."""
    from .models import Base
    
    engine = get_database_engine(config)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def reset_database(config: DatabaseConfig = None):
    """Reset database by dropping and recreating all tables."""
    from .models import Base
    
    engine = get_database_engine(config)
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    # Recreate all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset completed")


def get_database_info(config: DatabaseConfig = None) -> dict:
    """Get database information and statistics."""
    with get_database_session(config) as session:
        # Get SQLite version and configuration
        sqlite_version = session.execute(text("SELECT sqlite_version()")).scalar()
        
        # Get database file size
        db_url = get_database_url(config or DatabaseConfig())
        db_path = db_url.replace("sqlite:///", "")
        
        file_size = 0
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
        
        # Get table count and row counts
        tables_info = {}
        try:
            # Get all table names
            table_query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = session.execute(table_query).fetchall()
            
            for (table_name,) in tables:
                count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                row_count = session.execute(count_query).scalar()
                tables_info[table_name] = row_count
                
        except Exception as e:
            logger.warning(f"Could not get table info: {e}")
        
        return {
            "sqlite_version": sqlite_version,
            "database_path": db_path,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "tables": tables_info,
        }