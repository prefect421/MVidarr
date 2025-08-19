"""
Migration 011: Add thumbnail_url field to playlists table
"""

from sqlalchemy import text

def upgrade(session):
    """Add thumbnail_url field to playlists table"""
    
    # Add thumbnail_url column to playlists table
    session.execute(text("ALTER TABLE playlists ADD COLUMN thumbnail_url VARCHAR(500)"))
    session.commit()
    
    print("✅ Migration 011: Added thumbnail_url field to playlists table")

def downgrade(session):
    """Remove thumbnail_url field from playlists table"""
    
    # Remove thumbnail_url column from playlists table
    session.execute(text("ALTER TABLE playlists DROP COLUMN thumbnail_url"))
    session.commit()
    
    print("✅ Migration 011 Downgrade: Removed thumbnail_url field from playlists table")