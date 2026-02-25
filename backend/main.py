"""
FastAPI application entry point.

This module initializes and configures the FastAPI application with:
- Database initialization
- API routers
- CORS middleware
- Logging configuration
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.database import Manager, close_engine
from backend.api.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================================
# 1. CONNECT - Lifecycle Management
# ============================================================================
@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application lifecycle: startup and shutdown.

    Startup:
        - Initialize database manager
        - Verify SQL Server connection
        - Create database if not exists
        - Run Alembic migrations to create/update tables

    Shutdown:
        - Close database engine connections
        - Clean up resources
    """
    logger.info("🚀 Starting application...")

    # Initialize database manager
    db_manager = Manager()

    try:
        logger.info("📡 Verifying SQL Server connection...")
        if not db_manager.verify_conn():
            logger.error("Failed to connect to SQL Server")
            raise ConnectionError("Cannot connect to SQL Server")
        logger.info("SQL Server connection successful")

        logger.info("Checking database existence...")
        if not db_manager.db_exists():
            logger.info("Database not found, creating...")
            if not db_manager.create_db():
                logger.error("Failed to create database")
                raise RuntimeError("Cannot create database")
            logger.info("Database created successfully")
        else:
            logger.info("Database already exists")

        # Step 3: Run migrations to create/update tables
        # Temporarily disabled - no migration files exist yet
        logger.info("Skipping database migrations (no migrations yet)")
        logger.info("Running database migrations...")
        try:
            if not db_manager.sync_tables():
                logger.warning("Migration completed with warnings")
            else:
                logger.info("Migrations completed successfully")
        except (RuntimeError, ConnectionError, OSError) as migration_error:
            logger.error("Migration failed: %s", migration_error)
            logger.warning(
                "Continuing without migrations."
            )

        logger.info("Application started successfully")

        # Application is ready - yield control
        yield

    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise

    finally:
        logger.info("Shutting down application...")
        close_engine()
        logger.info("Database connections closed")


# ============================================================================
# 2. CREATE APP - Application Factory
# ============================================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VER,
    description="Hyper Data Lab - Financial Data API",
    lifespan=lifespan,
)


# ============================================================================
# 3. CORS - Security Configuration
# ============================================================================
# Configure CORS to allow requests from Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1234",
        "http://127.0.0.1:1234",
        "https://*.vercel.app",
        "https://*.vercel.com",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

logger.info("CORS middleware configured")


# ============================================================================
# 4. CONTROLLER - Routing
# ============================================================================
# Include API routers - delegates requests to specific route handlers
app.include_router(
    api_router,
    prefix="/api/v1",
)

logger.info("API routes registered")


# ============================================================================
# 5. CHECK - Health Check
# ============================================================================
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint.

    Returns:
        dict: Status indicating the service is online

    Usage:
        This endpoint is used to verify:
        - The application is running
        - Ngrok tunnel is working
        - Server is accessible from external sources
    """
    return {
        "status": "online",
        "message": "Hyper Data Lab API is running",
        "version": settings.APP_VER,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint.

    Returns:
        dict: Detailed status information
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VER,
    }


# ============================================================================
# 6. ENTRY POINT - Development Server
# ============================================================================
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VER)
    logger.info("Server will run on http://localhost:%s", settings.APP_PORT)

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=True,
        log_level="info",
    )
