"""
Database configuration and connection management.

Handles database URL construction, engine creation, and session management.
"""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine as sa_create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..models.base import Base


def get_database_url(test_mode: bool = False) -> str:
    """
    Get database URL from environment variables.
    
    Args:
        test_mode: Whether to use test database configuration
        
    Returns:
        Database URL string
        
    Raises:
        ValueError: If required environment variables are not set
    """
    if test_mode:
        # Use in-memory SQLite for testing
        return "sqlite:///:memory:"
    
    # Check for full database URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Construct URL from individual components
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "aihelpers")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    
    if not db_password:
        raise ValueError("Database password must be set in DB_PASSWORD environment variable")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def create_engine(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    Create SQLAlchemy engine with appropriate configuration.
    
    Args:
        database_url: Database URL (if not provided, will be fetched from env)
        echo: Whether to echo SQL statements
        
    Returns:
        SQLAlchemy engine instance
    """
    if database_url is None:
        database_url = get_database_url()
    
    engine_kwargs = {
        "echo": echo,
        "future": True,  # Use SQLAlchemy 2.0 style
    }
    
    # Special handling for SQLite (mainly for testing)
    if database_url.startswith("sqlite"):
        engine_kwargs.update({
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False}
        })
    else:
        # PostgreSQL connection pool settings
        engine_kwargs.update({
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_pre_ping": True,
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        })
    
    return sa_create_engine(database_url, **engine_kwargs)


# Create the global engine instance (only if not in test mode)
try:
    engine = create_engine(echo=os.getenv("DB_ECHO", "false").lower() == "true")
    
    # Create session factory
    SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        future=True  # Use SQLAlchemy 2.0 style
    )
except ValueError:
    # Handle case where database is not configured (e.g., during testing)
    engine = None
    SessionLocal = None


def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session for dependency injection.
    
    Yields:
        Database session
        
    Usage:
        @app.get("/")
        def read_root(db: Session = Depends(get_db_session)):
            return db.query(User).all()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tables(engine_instance: Optional[Engine] = None) -> None:
    """
    Create all database tables.
    
    Args:
        engine_instance: SQLAlchemy engine (uses global engine if not provided)
    """
    if engine_instance is None:
        engine_instance = engine
    
    Base.metadata.create_all(bind=engine_instance)


def drop_tables(engine_instance: Optional[Engine] = None) -> None:
    """
    Drop all database tables.
    
    Args:
        engine_instance: SQLAlchemy engine (uses global engine if not provided)
    """
    if engine_instance is None:
        engine_instance = engine
    
    Base.metadata.drop_all(bind=engine_instance)


def get_test_engine() -> Engine:
    """
    Get a test engine with in-memory SQLite database.
    
    Returns:
        Test engine instance
    """
    return create_engine("sqlite:///:memory:", echo=False)


def get_test_session() -> Session:
    """
    Get a test database session.
    
    Returns:
        Test database session
    """
    test_engine = get_test_engine()
    create_tables(test_engine)
    
    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        future=True
    )
    
    return TestSessionLocal()