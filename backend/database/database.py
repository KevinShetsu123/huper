"""
Database core configuration: Base, Engine, Session and Naming Convention.

This module consolidates all database core components including:
- Naming convention for constraints (helps avoid migration errors)
- Declarative base
- Engine configuration and management
- Session factory and dependency injection
"""

from typing import Generator, cast
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.create import create_engine
from sqlalchemy.sql.schema import MetaData
from sqlalchemy.orm.session import sessionmaker, Session
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.pool import QueuePool
from backend.core import settings


# Naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=NAMING_CONVENTION)

# Create declarative base with custom metadata
Base = declarative_base(metadata=metadata)

# Create database engine
DATABASE_URL = settings.get_db_url()

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    isolation_level="READ COMMITTED",
    implicit_returning=False,
    connect_args={
        "fast_executemany": True,
    },
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_engine() -> Engine:
    """Get the database engine.

    Returns:
        Engine: SQLAlchemy engine instance
    """
    return cast(Engine, engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency function to get database session.

    This function is used as a FastAPI dependency to provide
    database sessions to route handlers.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_session)):
            # Use db session here
            pass

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def close_engine():
    """Close the database engine and cleanup connections.

    This should be called during application shutdown.
    """
    engine.dispose()
