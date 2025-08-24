"""
Database migration system for MVidarr
Handles schema changes and database upgrades safely.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.database.connection import get_db
from src.utils.logger import get_logger

logger = get_logger("mvidarr.database.migrations")


class Migration:
    """Base class for database migrations"""

    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.timestamp = datetime.utcnow()

    def up(self, connection):
        """Apply the migration"""
        raise NotImplementedError("Migration must implement up() method")

    def down(self, connection):
        """Rollback the migration (optional)"""
        logger.warning(f"Rollback not implemented for migration {self.version}")

    def __str__(self):
        return f"Migration {self.version}: {self.description}"


class Migration_001_AddPlaylistThumbnailUrl(Migration):
    """Add thumbnail_url column to playlists table"""

    def __init__(self):
        super().__init__("001", "Add thumbnail_url column to playlists table")

    def up(self, connection):
        """Add thumbnail_url column"""
        try:
            # Check if column already exists
            result = connection.execute(
                text("SHOW COLUMNS FROM playlists LIKE 'thumbnail_url'")
            )
            if result.fetchone():
                logger.info("Column thumbnail_url already exists in playlists table")
                return

            # Add the column
            connection.execute(
                text(
                    "ALTER TABLE playlists ADD COLUMN thumbnail_url VARCHAR(500) NULL AFTER playlist_metadata"
                )
            )
            logger.info("Added thumbnail_url column to playlists table")

        except Exception as e:
            logger.error(f"Failed to add thumbnail_url column: {e}")
            raise

    def down(self, connection):
        """Remove thumbnail_url column"""
        try:
            connection.execute(text("ALTER TABLE playlists DROP COLUMN thumbnail_url"))
            logger.info("Removed thumbnail_url column from playlists table")
        except Exception as e:
            logger.error(f"Failed to remove thumbnail_url column: {e}")
            raise


class Migration_002_AddDynamicPlaylists(Migration):
    """Add dynamic playlist support to playlists table"""

    def __init__(self):
        super().__init__("002", "Add dynamic playlist support to playlists table")

    def up(self, connection):
        """Add dynamic playlist columns"""
        try:
            # Add playlist_type column
            try:
                connection.execute(
                    text(
                        "ALTER TABLE playlists ADD COLUMN playlist_type VARCHAR(10) DEFAULT 'STATIC' NOT NULL"
                    )
                )
                logger.info("Added playlist_type column to playlists table")
            except OperationalError as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    logger.info("Column playlist_type already exists")
                else:
                    raise

            # Add filter_criteria column
            try:
                connection.execute(
                    text("ALTER TABLE playlists ADD COLUMN filter_criteria JSON NULL")
                )
                logger.info("Added filter_criteria column to playlists table")
            except OperationalError as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    logger.info("Column filter_criteria already exists")
                else:
                    raise

            # Add auto_update column
            try:
                connection.execute(
                    text(
                        "ALTER TABLE playlists ADD COLUMN auto_update BOOLEAN DEFAULT 1 NOT NULL"
                    )
                )
                logger.info("Added auto_update column to playlists table")
            except OperationalError as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    logger.info("Column auto_update already exists")
                else:
                    raise

            # Add last_updated column
            try:
                connection.execute(
                    text("ALTER TABLE playlists ADD COLUMN last_updated DATETIME NULL")
                )
                logger.info("Added last_updated column to playlists table")
            except OperationalError as e:
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    logger.info("Column last_updated already exists")
                else:
                    raise

            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_playlist_type ON playlists (playlist_type)",
                "CREATE INDEX IF NOT EXISTS idx_playlist_auto_update ON playlists (auto_update)",
                "CREATE INDEX IF NOT EXISTS idx_playlist_last_updated ON playlists (last_updated)",
                "CREATE INDEX IF NOT EXISTS idx_playlist_type_auto ON playlists (playlist_type, auto_update)",
            ]

            for index_sql in indexes:
                try:
                    connection.execute(text(index_sql))
                except OperationalError:
                    # Index might already exist
                    pass

            logger.info("Dynamic playlist migration completed successfully")

        except Exception as e:
            logger.error(f"Failed to add dynamic playlist columns: {e}")
            raise

    def down(self, connection):
        """Remove dynamic playlist columns"""
        try:
            # Drop indexes
            indexes = [
                "DROP INDEX IF EXISTS idx_playlist_type_auto",
                "DROP INDEX IF EXISTS idx_playlist_last_updated",
                "DROP INDEX IF EXISTS idx_playlist_auto_update",
                "DROP INDEX IF EXISTS idx_playlist_type",
            ]

            for index_sql in indexes:
                try:
                    connection.execute(text(index_sql))
                except OperationalError:
                    pass

            # Drop columns
            columns = [
                "last_updated",
                "auto_update",
                "filter_criteria",
                "playlist_type",
            ]
            for column in columns:
                try:
                    connection.execute(
                        text(f"ALTER TABLE playlists DROP COLUMN {column}")
                    )
                except OperationalError:
                    pass

            logger.info("Dynamic playlist rollback completed")
        except Exception as e:
            logger.error(f"Failed to rollback dynamic playlist migration: {e}")
            raise


class MigrationManager:
    """Manages database migrations"""

    def __init__(self):
        self.migrations: List[Migration] = [
            Migration_001_AddPlaylistThumbnailUrl(),
            Migration_002_AddDynamicPlaylists(),
            # Add new migrations here
        ]

    def ensure_migrations_table(self, connection):
        """Create migrations table if it doesn't exist"""
        try:
            connection.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS database_migrations (
                    version VARCHAR(10) PRIMARY KEY,
                    description VARCHAR(255) NOT NULL,
                    applied_at DATETIME NOT NULL,
                    applied_by VARCHAR(100) DEFAULT 'system'
                )
                """
                )
            )
            logger.debug("Migrations table ensured")
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise

    def get_applied_migrations(self, connection) -> List[str]:
        """Get list of applied migration versions"""
        try:
            result = connection.execute(
                text("SELECT version FROM database_migrations ORDER BY version")
            )
            return [row[0] for row in result.fetchall()]
        except OperationalError:
            # Migrations table doesn't exist yet
            return []

    def get_pending_migrations(self, connection) -> List[Migration]:
        """Get list of migrations that need to be applied"""
        applied = self.get_applied_migrations(connection)
        return [m for m in self.migrations if m.version not in applied]

    def apply_migration(self, connection, migration: Migration):
        """Apply a single migration"""
        try:
            logger.info(f"Applying migration: {migration}")

            # Apply the migration
            migration.up(connection)

            # Record the migration as applied
            connection.execute(
                text(
                    """
                INSERT INTO database_migrations (version, description, applied_at)
                VALUES (:version, :description, :applied_at)
                """
                ),
                {
                    "version": migration.version,
                    "description": migration.description,
                    "applied_at": datetime.utcnow(),
                },
            )

            logger.info(f"Migration {migration.version} applied successfully")

        except Exception as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise

    def migrate(self) -> Dict[str, any]:
        """Apply all pending migrations"""
        applied_count = 0
        results = {"success": True, "applied_migrations": [], "errors": []}

        try:
            with get_db() as session:
                connection = session.connection()

                # Ensure migrations table exists
                self.ensure_migrations_table(connection)

                # Get pending migrations
                pending = self.get_pending_migrations(connection)

                if not pending:
                    logger.info("No pending migrations")
                    return results

                logger.info(f"Found {len(pending)} pending migrations")

                # Apply each migration
                for migration in pending:
                    try:
                        self.apply_migration(connection, migration)
                        results["applied_migrations"].append(
                            {
                                "version": migration.version,
                                "description": migration.description,
                            }
                        )
                        applied_count += 1
                    except Exception as e:
                        error_msg = f"Migration {migration.version} failed: {str(e)}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)
                        results["success"] = False
                        break  # Stop on first failure

                # Commit all changes
                session.commit()

                if results["success"]:
                    logger.info(f"Successfully applied {applied_count} migrations")
                else:
                    logger.error(
                        f"Migration process failed after {applied_count} migrations"
                    )

        except Exception as e:
            error_msg = f"Migration process failed: {str(e)}"
            logger.error(error_msg)
            results["success"] = False
            results["errors"].append(error_msg)

        return results

    def get_migration_status(self) -> Dict[str, any]:
        """Get current migration status"""
        try:
            with get_db() as session:
                connection = session.connection()

                self.ensure_migrations_table(connection)
                applied = self.get_applied_migrations(connection)
                pending = self.get_pending_migrations(connection)

                return {
                    "total_migrations": len(self.migrations),
                    "applied_count": len(applied),
                    "pending_count": len(pending),
                    "applied_migrations": [
                        {
                            "version": m.version,
                            "description": m.description,
                        }
                        for m in self.migrations
                        if m.version in applied
                    ],
                    "pending_migrations": [
                        {
                            "version": m.version,
                            "description": m.description,
                        }
                        for m in pending
                    ],
                }

        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {"error": str(e)}

    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration"""
        try:
            migration = next((m for m in self.migrations if m.version == version), None)
            if not migration:
                logger.error(f"Migration {version} not found")
                return False

            with get_db() as session:
                connection = session.connection()

                # Check if migration is applied
                applied = self.get_applied_migrations(connection)
                if version not in applied:
                    logger.warning(f"Migration {version} is not applied")
                    return False

                logger.info(f"Rolling back migration: {migration}")

                # Rollback the migration
                migration.down(connection)

                # Remove from migrations table
                connection.execute(
                    text("DELETE FROM database_migrations WHERE version = :version"),
                    {"version": version},
                )

                session.commit()
                logger.info(f"Migration {version} rolled back successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            return False


# Global migration manager instance
migration_manager = MigrationManager()


def run_migrations() -> Dict[str, any]:
    """Run all pending migrations"""
    return migration_manager.migrate()


def get_migration_status() -> Dict[str, any]:
    """Get current migration status"""
    return migration_manager.get_migration_status()


def rollback_migration(version: str) -> bool:
    """Rollback a specific migration"""
    return migration_manager.rollback_migration(version)
