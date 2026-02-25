"""
Database Package - Centralized database management.

This package provides a comprehensive database layer including:
- Core: Base, Engine, Session, and metadata configuration
- Models: SQLAlchemy ORM models for financial data
- Repositories: Data access layer with CRUD operations
- Migrations: Alembic migrations for schema management
- Manager: Database administration and initialization tools

Usage:
    # Get database session
    from backend.database import get_session

    # Access models
    from backend.database import models

    # Use repositories
    from backend.database import repositories

    # Database management
    from backend.database import Manager
"""

from backend.database.database import (
    Base,
    engine,
    SessionLocal,
    metadata,
    NAMING_CONVENTION,
    get_engine,
    get_session,
    close_engine,
)

from backend.database.initializer import DBManager
from backend.database import models
from backend.database import repositories

# Convenience alias
Manager = DBManager

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "metadata",
    "NAMING_CONVENTION",
    "get_engine",
    "get_session",
    "close_engine",
    "DBManager",
    "Manager",
    "models",
    "repositories",
]
