"""
Async Database Connection for FastAPI
Provides async SQLAlchemy engine and session management
"""

import asyncio
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine, 
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text

from src.utils.logger import get_logger

logger = get_logger("mvidarr.async_database")

class AsyncDatabaseManager:
    """Manages async database connections and sessions"""
    
    def __init__(self):
        self.engine: AsyncEngine = None
        self.async_session_factory: async_sessionmaker = None
        self._initialized = False

    async def initialize(self, database_url: str):
        """Initialize async database engine and session factory"""
        if self._initialized:
            logger.debug("Async database already initialized")
            return

        try:
            # Convert MySQL URL to async format
            if database_url.startswith("mysql+pymysql://"):
                async_database_url = database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
            elif database_url.startswith("mysql://"):
                async_database_url = database_url.replace("mysql://", "mysql+aiomysql://") 
            else:
                async_database_url = database_url

            logger.info(f"Initializing async database connection")

            # Create async engine with optimized settings
            self.engine = create_async_engine(
                async_database_url,
                # Connection pool settings optimized for async operations
                poolclass=QueuePool,
                pool_size=10,  # Number of connections to maintain
                max_overflow=20,  # Additional connections on demand
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,  # Recycle connections after 1 hour
                # Async-specific settings
                echo=False,  # Set to True for SQL debugging
                future=True,  # Use SQLAlchemy 2.0 style
            )

            # Create async session factory
            self.async_session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Important for async operations
                autoflush=False,  # Manual control over flushing
                autocommit=False,  # Explicit transaction management
            )

            # Test the connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self._initialized = True
            logger.info("✅ Async database initialized successfully")
            logger.info(f"Connection pool size: {self.engine.pool.size()}")

        except Exception as e:
            logger.error(f"Failed to initialize async database: {e}")
            raise

    async def get_session(self) -> AsyncSession:
        """Get an async database session"""
        if not self._initialized:
            raise RuntimeError("Async database not initialized. Call initialize() first.")
        
        return self.async_session_factory()

    @asynccontextmanager
    async def session_scope(self):
        """
        Async context manager for database sessions with automatic cleanup
        Usage:
            async with db_manager.session_scope() as session:
                # Use session here
                result = await session.execute(select(User))
        """
        session = await self.get_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def close(self):
        """Close the database engine and all connections"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Async database connections closed")

# Global async database manager instance
async_db_manager = AsyncDatabaseManager()

async def get_async_database_url():
    """Get the async database URL from environment/config"""
    # Import here to avoid circular imports
    try:
        from src.config.config import Config
        config = Config()
        
        # Build the async database URL using the same pattern as sync
        sync_url = (
            f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}"
            f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
            f"?charset=utf8mb4"
        )
        
        # Convert to async URL
        if sync_url.startswith("mysql+pymysql://"):
            return sync_url.replace("mysql+pymysql://", "mysql+aiomysql://")
        elif sync_url.startswith("mysql://"):
            return sync_url.replace("mysql://", "mysql+aiomysql://")
        else:
            return sync_url
    except Exception as e:
        logger.error(f"Error getting database URL from config: {e}")
        # Fallback to environment variables
        import os
        from urllib.parse import quote_plus
        
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '3306')
        username = os.getenv('DB_USER', 'mvidarr')
        password = os.getenv('DB_PASSWORD', 'change_me_to_your_password')
        database = os.getenv('DB_NAME', 'mvidarr')
        
        # URL encode the password to handle special characters
        encoded_password = quote_plus(password)
        
        return f"mysql+aiomysql://{username}:{encoded_password}@{host}:{port}/{database}?charset=utf8mb4"

async def initialize_async_database():
    """Initialize the global async database manager"""
    database_url = await get_async_database_url()
    await async_db_manager.initialize(database_url)

# FastAPI dependency for getting async database sessions
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting async database sessions
    Usage in FastAPI routes:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    if not async_db_manager._initialized:
        await initialize_async_database()
    
    async with async_db_manager.session_scope() as session:
        yield session

# Utility function for manual session management
async def get_async_session() -> AsyncSession:
    """Get an async session for manual management (remember to close!)"""
    if not async_db_manager._initialized:
        await initialize_async_database()
    
    return await async_db_manager.get_session()

# Health check function
async def check_async_database_health():
    """Check if async database connection is healthy"""
    try:
        if not async_db_manager._initialized:
            await initialize_async_database()
        
        async with async_db_manager.session_scope() as session:
            await session.execute(text("SELECT 1"))
        
        return {"status": "healthy", "database": "async_connection_ok"}
    except Exception as e:
        logger.error(f"Async database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "database": "async_connection_failed"}