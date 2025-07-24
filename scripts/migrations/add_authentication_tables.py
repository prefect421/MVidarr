#!/usr/bin/env python3
"""
Database migration script to add authentication tables for MVidarr Enhanced
This script adds the User and UserSession tables along with required enums.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db, engine, Base
from src.database.models import User, UserSession, UserRole, SessionStatus
from src.services.auth_service import AuthService
from src.utils.logger import get_logger

logger = get_logger('mvidarr.migration.auth')

def create_authentication_tables():
    """Create authentication tables and initial admin user"""
    try:
        logger.info("Starting authentication tables migration...")
        
        # Create all tables (this will only create tables that don't exist)
        Base.metadata.create_all(engine)
        logger.info("Authentication tables created successfully")
        
        # Check if we need to create a default admin user
        with get_db() as session:
            admin_count = session.query(User).filter_by(role=UserRole.ADMIN).count()
            
            if admin_count == 0:
                # Create default admin user
                logger.info("No admin users found, creating default admin...")
                
                success, message, admin_user = AuthService.create_user(
                    username="admin",
                    email="admin@mvidarr.local",
                    password="MVidarr@dmin123",  # Strong default password
                    role=UserRole.ADMIN
                )
                
                if success:
                    logger.info("✅ Default admin user created successfully")
                    logger.info("   Username: admin")
                    logger.info("   Password: MVidarr@dmin123")
                    logger.info("   ⚠️  IMPORTANT: Change the default password immediately after first login!")
                    print("\n" + "="*70)
                    print("🔐 DEFAULT ADMIN USER CREATED")
                    print("="*70)
                    print(f"Username: admin")
                    print(f"Password: MVidarr@dmin123")
                    print(f"Email: admin@mvidarr.local")
                    print("\n⚠️  SECURITY WARNING:")
                    print("   Please change the default password immediately after first login!")
                    print("   The default password is intentionally complex but should be changed.")
                    print("="*70 + "\n")
                else:
                    logger.error(f"❌ Failed to create default admin user: {message}")
                    return False
            else:
                logger.info(f"✅ Found {admin_count} existing admin user(s), skipping default admin creation")
        
        # Verify tables were created correctly
        with get_db() as session:
            # Test User table
            user_count = session.query(User).count()
            session_count = session.query(UserSession).count()
            
            logger.info(f"✅ Migration completed successfully")
            logger.info(f"   - Users in database: {user_count}")
            logger.info(f"   - Sessions in database: {session_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def verify_authentication_tables():
    """Verify that authentication tables exist and are accessible"""
    try:
        logger.info("Verifying authentication tables...")
        
        with get_db() as session:
            # Test table accessibility
            users = session.query(User).limit(5).all()
            sessions = session.query(UserSession).limit(5).all()
            
            logger.info(f"✅ Authentication tables verified")
            logger.info(f"   - User table accessible: {len(users)} users found")
            logger.info(f"   - UserSession table accessible: {len(sessions)} sessions found")
            
            # Check for admin users
            admin_count = session.query(User).filter_by(role=UserRole.ADMIN).count()
            if admin_count > 0:
                logger.info(f"   - Admin users available: {admin_count}")
            else:
                logger.warning("   - ⚠️  No admin users found!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def rollback_authentication_tables():
    """Rollback authentication tables (for testing purposes)"""
    try:
        logger.warning("⚠️  ROLLBACK: Dropping authentication tables...")
        
        # Drop tables in reverse order due to foreign key constraints
        UserSession.__table__.drop(engine, checkfirst=True)
        User.__table__.drop(engine, checkfirst=True)
        
        logger.info("✅ Authentication tables dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🔐 MVidarr Enhanced - Authentication Tables Migration")
    print("="*60)
    print(f"Migration started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    import argparse
    parser = argparse.ArgumentParser(description='Authentication tables migration')
    parser.add_argument('--action', choices=['migrate', 'verify', 'rollback'], 
                       default='migrate', help='Action to perform')
    parser.add_argument('--force', action='store_true', 
                       help='Force rollback without confirmation')
    
    args = parser.parse_args()
    
    if args.action == 'migrate':
        print("📊 Creating authentication tables...")
        success = create_authentication_tables()
        
        if success:
            print("\n✅ Migration completed successfully!")
            print("🔍 Verifying tables...")
            verify_authentication_tables()
            print("\n🎉 Authentication system is ready!")
        else:
            print("\n❌ Migration failed! Check logs for details.")
            sys.exit(1)
    
    elif args.action == 'verify':
        print("🔍 Verifying authentication tables...")
        success = verify_authentication_tables()
        
        if success:
            print("\n✅ Verification completed successfully!")
        else:
            print("\n❌ Verification failed! Check logs for details.")
            sys.exit(1)
    
    elif args.action == 'rollback':
        if not args.force:
            print("⚠️  WARNING: This will delete all authentication data!")
            response = input("Are you sure you want to rollback? (type 'yes' to confirm): ")
            if response.lower() != 'yes':
                print("Rollback cancelled.")
                sys.exit(0)
        
        print("🗑️  Rolling back authentication tables...")
        success = rollback_authentication_tables()
        
        if success:
            print("\n✅ Rollback completed successfully!")
        else:
            print("\n❌ Rollback failed! Check logs for details.")
            sys.exit(1)
    
    print(f"\nMigration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()