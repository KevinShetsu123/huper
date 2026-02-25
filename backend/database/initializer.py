"""Database Manager - Database and table initialization using Alembic."""

import logging
from typing import cast
from sqlalchemy.sql.expression import text
from sqlalchemy.engine.create import create_engine
from sqlalchemy.engine.base import Engine, Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool
from alembic.config import Config
from alembic import command
from backend.core.config import settings


logger = logging.getLogger(__name__)


class DBManager:
    """Database initialization manager using Alembic for table management."""

    def __init__(self):
        """Initialize DBManager with configuration from settings."""
        self.db_name = settings.DB_NAME
        self.master_engine: Engine | None = None
        self.target_engine: Engine | None = None

    def _get_engine(self, is_master: bool = False) -> Engine:
        """Get database engine.

        Args:
            is_master: If True, connect to 'master' database for admin
                    operations. If False, connect to target database.

        Returns:
            SQLAlchemy Engine instance
        """
        if is_master:
            if self.master_engine is None:
                self.master_engine = create_engine(
                    settings.get_db_url(is_master=True),
                    poolclass=NullPool,
                    isolation_level="AUTOCOMMIT",
                    echo=False,
                )
            return cast(Engine, self.master_engine)

        if self.target_engine is None:
            self.target_engine = create_engine(
                settings.get_db_url(is_master=False),
                poolclass=QueuePool,
                pool_pre_ping=True,
                echo=False,
                connect_args={"fast_executemany": True},
            )
        return cast(Engine, self.target_engine)

    def verify_conn(self) -> bool:
        """Check SQL Server connection to master database.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            conn: Connection
            with self._get_engine(is_master=True).connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("SQL Server connection successful")
            return True
        except SQLAlchemyError as exc:
            logger.error("SQL Server connection failed: %s", exc)
            return False

    def db_exists(self) -> bool:
        """Check if target database exists.

        Returns:
            bool: True if database exists, False otherwise
        """
        try:
            conn: Connection
            with self._get_engine(is_master=True).connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT 1 FROM sys.databases WHERE name = :db_name"
                    ),
                    {"db_name": self.db_name},
                )
                if not result:
                    logger.warning(
                        "No result returned when checking database existence"
                    )
                    return False

                exists = result.scalar() is not None

                if exists:
                    logger.info("Database '%s' exists", self.db_name)
                else:
                    logger.warning("Database '%s' not found", self.db_name)

                return exists
        except SQLAlchemyError as exc:
            logger.error("Database check failed: %s", exc)
            return False

    def create_db(self) -> bool:
        """Create target database if it doesn't exist.

        Returns:
            bool: True if database created or already exists, False otherwise
        """
        if self.db_exists():
            logger.info("Database '%s' already exists", self.db_name)
            return True

        try:
            logger.info("Creating database '%s'...", self.db_name)
            conn: Connection
            with self._get_engine(is_master=True).connect() as conn:
                # Create database
                conn.execute(
                    text(f"CREATE DATABASE [{self.db_name}]")
                )
                conn.commit()
            
            logger.info("✅ Database '%s' created successfully", self.db_name)
            return True
        except SQLAlchemyError as exc:
            logger.error(
                "Failed to create database '%s': %s", self.db_name, exc
            )
            return False

    def tables_exist(self) -> bool:
        """Check if all required tables exist in the database.

        Returns:
            bool: True if all required tables exist, False otherwise
        """
        required_tables = {
            "balance_sheet_items",
            "income_statement_items",
            "cash_flow_statement_items",
            "financial_reports",
        }

        if not self.db_exists():
            return False

        try:
            conn: Connection
            with self._get_engine(is_master=False).connect() as conn:
                result = conn.execute(
                    text(
                        """
                    SELECT TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    AND TABLE_SCHEMA = 'dbo'
                """
                    )
                )

                if not result:
                    logger.warning(
                        "No result returned when checking existing tables"
                    )
                    return False

                existing_tables = {row[0] for row in result.fetchall()}
                missing_tables = required_tables - existing_tables

                if missing_tables:
                    logger.warning(
                        "Missing tables: %s", ", ".join(missing_tables)
                    )
                    return False

                logger.info(
                    "All required tables exist: %s",
                    ", ".join(
                        sorted(existing_tables)
                    )
                )
                return True
        except SQLAlchemyError as exc:
            logger.error("Table check failed: %s", exc)
            return False

    def sync_tables(self) -> bool:
        """Synchronize database tables using Alembic migrations.

        This will:
        - Run all pending migrations to create/update tables
        - Ensure database schema matches the models

        Returns:
            bool: True if sync successful, False otherwise
        """
        if not self.db_exists():
            logger.error(
                "Cannot sync tables: Database '%s' does not exist",
                self.db_name
            )
            return False

        try:
            logger.info("Synchronizing tables using Alembic migrations...")
            alembic_cfg = Config(settings.ALEMBIC_INI_PATH)

            command.upgrade(alembic_cfg, "head")

            logger.info("Tables synchronized successfully via Alembic")
            return True
        except (SQLAlchemyError, RuntimeError, FileNotFoundError) as exc:
            logger.error("Table synchronization failed: %s", exc)
            return False

    def list_tables(self) -> list:
        """Read list of all existing tables in the database.

        Returns:
            list: List of table names, empty list if error or no tables
        """
        if not self.db_exists():
            return []

        try:
            conn: Connection
            with self._get_engine(is_master=False).connect() as conn:
                result = conn.execute(
                    text(
                        """
                    SELECT TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                """
                    )
                )

                if not result:
                    logger.warning(
                        "No result returned when reading table list"
                    )
                    return []

                tables = [row[0] for row in result.fetchall()]

                if tables:
                    logger.info(
                        "Tables in '%s': %s", self.db_name, ", ".join(tables)
                    )
                else:
                    logger.info("Database '%s' has no tables", self.db_name)

                return tables
        except SQLAlchemyError as exc:
            logger.error("Failed to read table list: %s", exc)
            return []

    def initialize(self) -> bool:
        """Initialize database: check database exists and sync tables with
        Alembic.

        Process:
        1. Check SQL Server connection
        2. Check if database exists (log error if not)
        3. If database exists, check and sync tables using Alembic

        Returns:
            bool: True if initialization successful, False otherwise
        """
        logger.info("Starting database initialization...")

        try:
            if not self.verify_conn():
                raise RuntimeError("Cannot connect to SQL Server")

            if not self.db_exists():
                logger.error(
                    "Database '%s' does not exist. "
                    "Create the database before running this application.",
                    self.db_name,
                )
                return False

            if not self.tables_exist():
                logger.info(
                    "Tables missing or incomplete, syncing with Alembic..."
                )
                if not self.sync_tables():
                    return False
            else:
                logger.info(
                    "All tables exist, checking if migrations are up-to-date."
                )

                if not self.sync_tables():
                    logger.warning("Tables exist but migration sync failed")

            if self.tables_exist():
                logger.info("Database initialization completed successfully")
                return True
            else:
                logger.error(
                    """
                    Database initialization failed:Tables not created properly
                    """
                )
                return False

        except (SQLAlchemyError, RuntimeError) as exc:
            logger.error("Database initialization failed: %s", exc)
            return False
        finally:
            self.cleanup()

    def cleanup(self):
        """Close all database connections and cleanup resources."""
        if self.target_engine:
            self.target_engine.dispose()
            logger.debug("Target database engine disposed")
        if self.master_engine:
            self.master_engine.dispose()
            logger.debug("Master database engine disposed")
