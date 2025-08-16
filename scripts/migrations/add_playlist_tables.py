#!/usr/bin/env python3
"""
Database migration script to add playlist tables for MVidarr
This script adds the Playlist and PlaylistEntry tables.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config.config import Config
from src.database.connection import DatabaseManager, Base
from src.database.models import Playlist, PlaylistEntry, User, Video, UserRole
from src.utils.logger import get_logger

logger = get_logger('mvidarr.migration.playlists')

def create_playlist_tables():
    """Create playlist tables"""
    try:
        logger.info("Starting playlist tables migration...")
        
        # Initialize database manager
        config = Config()
        db_manager = DatabaseManager(config)
        
        # Create database if it doesn't exist
        if not db_manager.create_database_if_not_exists():
            logger.error("Failed to create database")
            return False
        
        # Create engine
        engine = db_manager.create_engine()
        
        # Create all tables (this will only create tables that don't exist)
        Base.metadata.create_all(engine)
        logger.info("Playlist tables created successfully")
        
        # Verify tables were created correctly
        with db_manager.get_session() as session:
            # Test Playlist table
            playlist_count = session.query(Playlist).count()
            entry_count = session.query(PlaylistEntry).count()
            
            logger.info(f"✅ Migration completed successfully")
            logger.info(f"   - Playlists in database: {playlist_count}")
            logger.info(f"   - Playlist entries in database: {entry_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def verify_playlist_tables():
    """Verify that playlist tables exist and are accessible"""
    try:
        logger.info("Verifying playlist tables...")
        
        # Initialize database manager
        config = Config()
        db_manager = DatabaseManager(config)
        
        with db_manager.get_session() as session:
            # Test table accessibility
            playlists = session.query(Playlist).limit(5).all()
            entries = session.query(PlaylistEntry).limit(5).all()
            
            logger.info(f"✅ Playlist tables verified")
            logger.info(f"   - Playlist table accessible: {len(playlists)} playlists found")
            logger.info(f"   - PlaylistEntry table accessible: {len(entries)} entries found")
            
            # Test relationships
            user_count = session.query(User).count()
            video_count = session.query(Video).count()
            logger.info(f"   - Related tables: {user_count} users, {video_count} videos available")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def create_sample_playlist():
    """Create a sample playlist for testing"""
    try:
        logger.info("Creating sample playlist...")
        
        # Initialize database manager
        config = Config()
        db_manager = DatabaseManager(config)
        
        with db_manager.get_session() as session:
            # Find first admin user
            admin_user = session.query(User).filter_by(role=UserRole.ADMIN).first()
            if not admin_user:
                logger.warning("No admin user found, skipping sample playlist creation")
                return True
            
            # Check if sample playlist already exists
            existing_playlist = session.query(Playlist).filter_by(
                name="Sample Playlist",
                user_id=admin_user.id
            ).first()
            
            if existing_playlist:
                logger.info("Sample playlist already exists, skipping creation")
                return True
            
            # Create sample playlist
            sample_playlist = Playlist(
                name="Sample Playlist",
                description="A sample playlist created during migration",
                user_id=admin_user.id,
                is_public=True,
                is_featured=False
            )
            
            session.add(sample_playlist)
            session.commit()
            
            # Update stats
            sample_playlist.update_stats()
            session.commit()
            
            logger.info(f"✅ Sample playlist created successfully (ID: {sample_playlist.id})")
            return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create sample playlist: {e}")
        return False

def rollback_playlist_tables():
    """Rollback playlist tables (for testing purposes)"""
    try:
        logger.warning("⚠️  ROLLBACK: Dropping playlist tables...")
        
        # Initialize database manager
        config = Config()
        db_manager = DatabaseManager(config)
        engine = db_manager.create_engine()
        
        # Drop tables in reverse order due to foreign key constraints
        PlaylistEntry.__table__.drop(engine, checkfirst=True)
        Playlist.__table__.drop(engine, checkfirst=True)
        
        logger.info("✅ Playlist tables dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🎵 MVidarr - Playlist Tables Migration")
    print("="*60)
    print(f"Migration started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    import argparse
    parser = argparse.ArgumentParser(description='Playlist tables migration')
    parser.add_argument('--action', choices=['migrate', 'verify', 'rollback', 'sample'], 
                       default='migrate', help='Action to perform')
    parser.add_argument('--force', action='store_true', 
                       help='Force rollback without confirmation')
    
    args = parser.parse_args()
    
    if args.action == 'migrate':
        print("📊 Creating playlist tables...")
        success = create_playlist_tables()
        
        if success:
            print("\n✅ Migration completed successfully!")
            print("🔍 Verifying tables...")
            verify_success = verify_playlist_tables()
            if verify_success:
                print("\n🎉 Playlist system is ready!")
            else:
                print("\n⚠️  Migration completed but verification failed.")
        else:
            print("\n❌ Migration failed! Check logs for details.")
            sys.exit(1)
    
    elif args.action == 'verify':
        print("🔍 Verifying playlist tables...")
        success = verify_playlist_tables()
        
        if success:
            print("\n✅ Verification completed successfully!")
        else:
            print("\n❌ Verification failed! Check logs for details.")
            sys.exit(1)
    
    elif args.action == 'sample':
        print("🎵 Creating sample playlist...")
        success = create_sample_playlist()
        
        if success:
            print("\n✅ Sample playlist created successfully!")
        else:
            print("\n❌ Failed to create sample playlist! Check logs for details.")
            sys.exit(1)
    
    elif args.action == 'rollback':
        if not args.force:
            print("⚠️  WARNING: This will delete all playlist data!")
            response = input("Are you sure you want to rollback? (type 'yes' to confirm): ")
            if response.lower() != 'yes':
                print("Rollback cancelled.")
                sys.exit(0)
        
        print("🗑️  Rolling back playlist tables...")
        success = rollback_playlist_tables()
        
        if success:
            print("\n✅ Rollback completed successfully!")
        else:
            print("\n❌ Rollback failed! Check logs for details.")
            sys.exit(1)
    
    print(f"\nMigration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()