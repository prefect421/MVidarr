"""
Database connection management for MVidarr
"""

import logging
from contextlib import contextmanager
from threading import Lock

import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

from src.config.config import Config
from src.utils.logger import get_logger

# Global database objects
engine = None
SessionLocal = None
Base = declarative_base()

logger = get_logger("mvidarr.database")


class DatabaseManager:
    """Database connection and session management"""

    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.session_factory = None
        self._lock = Lock()

    def get_connection_url(self):
        """Build database connection URL"""
        return (
            f"mysql+pymysql://{self.config.DB_USER}:{self.config.DB_PASSWORD}"
            f"@{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}"
            f"?charset=utf8mb4"
        )

    def create_engine(self):
        """Create SQLAlchemy engine with connection pooling"""
        if self.engine is None:
            with self._lock:
                if self.engine is None:
                    connection_url = self.get_connection_url()

                    self.engine = create_engine(
                        connection_url,
                        poolclass=QueuePool,
                        pool_size=self.config.DB_POOL_SIZE,
                        max_overflow=self.config.DB_MAX_OVERFLOW,
                        pool_timeout=self.config.DB_POOL_TIMEOUT,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        echo=self.config.DEBUG,
                    )

                    logger.info(
                        f"Database engine created: {self.config.DB_HOST}:{self.config.DB_PORT}"
                    )

        return self.engine

    def create_session_factory(self):
        """Create session factory"""
        if self.session_factory is None:
            with self._lock:
                if self.session_factory is None:
                    engine = self.create_engine()
                    session_local = sessionmaker(
                        autocommit=False, autoflush=False, bind=engine
                    )
                    self.session_factory = scoped_session(session_local)

                    logger.info("Database session factory created")

        return self.session_factory

    def test_connection(self):
        """Test database connection"""
        try:
            engine = self.create_engine()
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def create_database_if_not_exists(self):
        """Create database if it doesn't exist"""
        try:
            # Connect without specifying database
            temp_url = (
                f"mysql+pymysql://{self.config.DB_USER}:{self.config.DB_PASSWORD}"
                f"@{self.config.DB_HOST}:{self.config.DB_PORT}/?charset=utf8mb4"
            )

            temp_engine = create_engine(temp_url)
            with temp_engine.connect() as connection:
                # Check if database exists
                result = connection.execute(
                    text(
                        f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{self.config.DB_NAME}'"
                    )
                )

                if not result.fetchone():
                    # Create database
                    connection.execute(
                        text(
                            f"CREATE DATABASE {self.config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                        )
                    )
                    logger.info(f"Created database: {self.config.DB_NAME}")
                else:
                    logger.info(f"Database already exists: {self.config.DB_NAME}")

            temp_engine.dispose()
            return True

        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False

    @contextmanager
    def get_session(self):
        """Get database session with proper cleanup"""
        session_factory = self.create_session_factory()
        session = session_factory()

        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def close_connections(self):
        """Close all database connections"""
        if self.session_factory:
            self.session_factory.remove()

        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = None


def init_db(app):
    """Initialize database for Flask application"""
    global db_manager, engine, SessionLocal

    config = Config()
    db_manager = DatabaseManager(config)

    # Create database if it doesn't exist
    if not db_manager.create_database_if_not_exists():
        logger.error("Failed to create database")
        raise RuntimeError("Database initialization failed")

    # Test connection
    if not db_manager.test_connection():
        logger.error("Database connection test failed")
        raise RuntimeError("Database connection failed")

    # Create engine and session factory
    engine = db_manager.create_engine()
    SessionLocal = db_manager.create_session_factory()

    # Store in app context for cleanup
    app.db_manager = db_manager

    # Create database tables if they don't exist
    try:
        from src.database.init_db import initialize_database

        logger.info("Creating database tables...")
        if not initialize_database():
            logger.error("Failed to initialize database tables")
            raise RuntimeError("Database table initialization failed")
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Database table initialization failed: {e}")
        raise RuntimeError(f"Database table initialization failed: {e}")

    # Register cleanup on app teardown
    @app.teardown_appcontext
    def cleanup_db(error):
        if error:
            logger.error(f"Request failed: {error}")

        # Clean up any leftover sessions
        if SessionLocal:
            SessionLocal.remove()

    logger.info("Database initialization completed")


def get_db():
    """Get database session (for use in Flask routes)"""
    if db_manager:
        return db_manager.get_session()
    else:
        raise RuntimeError("Database not initialized")


def get_engine():
    """Get database engine"""
    return engine


def get_session_factory():
    """Get session factory"""
    return SessionLocal
