"""
Migration 014: Add video quality check fields
Add fields to track available YouTube qualities and last check date
"""

from datetime import datetime
from sqlalchemy import JSON, Column, DateTime, String, text


def upgrade(connection, metadata):
    """Add quality check fields to videos table"""
    print("Adding quality check fields to videos table...")
    
    # Add available_qualities JSON field
    connection.execute(text("""
        ALTER TABLE videos ADD COLUMN available_qualities JSON DEFAULT NULL
    """))
    
    # Add quality_check_date field
    connection.execute(text("""
        ALTER TABLE videos ADD COLUMN quality_check_date DATETIME DEFAULT NULL
    """))
    
    # Add max_available_quality field  
    connection.execute(text("""
        ALTER TABLE videos ADD COLUMN max_available_quality VARCHAR(50) DEFAULT NULL
    """))
    
    # Add quality_check_status field to track check results
    connection.execute(text("""
        ALTER TABLE videos ADD COLUMN quality_check_status VARCHAR(50) DEFAULT NULL
    """))
    
    print("✅ Added quality check fields to videos table")


def downgrade(connection, metadata):
    """Remove quality check fields from videos table"""
    print("Removing quality check fields from videos table...")
    
    connection.execute(text("ALTER TABLE videos DROP COLUMN available_qualities"))
    connection.execute(text("ALTER TABLE videos DROP COLUMN quality_check_date")) 
    connection.execute(text("ALTER TABLE videos DROP COLUMN max_available_quality"))
    connection.execute(text("ALTER TABLE videos DROP COLUMN quality_check_status"))
    
    print("✅ Removed quality check fields from videos table")