#!/usr/bin/env python3
"""
Migration: Add Advanced Search Tables for MVidarr 0.9.7 - Issue #73
Version: 008
Date: 2025-08-16
Description: Creates tables for saved search presets, search analytics, 
search result caching, and search suggestions.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db
from src.utils.logger import get_logger
from sqlalchemy import text

logger = get_logger('mvidarr.migration_008')

def upgrade():
    """Create advanced search tables"""
    try:
        with get_db() as session:
            logger.info("Starting migration 008: Adding advanced search tables")
            
            # Create search_presets table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS search_presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    search_criteria JSON NOT NULL,
                    preset_type VARCHAR(20) NOT NULL DEFAULT 'USER_DEFINED',
                    is_public BOOLEAN DEFAULT 0,
                    is_favorite BOOLEAN DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for search_presets
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_preset_user_id ON search_presets(user_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_preset_type ON search_presets(preset_type)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_preset_public ON search_presets(is_public)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_preset_favorite ON search_presets(is_favorite)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_preset_usage ON search_presets(usage_count)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_preset_last_used ON search_presets(last_used_at)"))
            
            logger.info("Created search_presets table with indexes")
            
            # Create search_analytics table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS search_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    session_id VARCHAR(255),
                    event_type VARCHAR(50) NOT NULL,
                    search_query TEXT,
                    search_criteria JSON,
                    preset_id INTEGER REFERENCES search_presets(id),
                    response_time_ms INTEGER,
                    result_count INTEGER,
                    user_agent TEXT,
                    ip_address VARCHAR(45),
                    referrer VARCHAR(500),
                    event_metadata JSON,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for search_analytics
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_analytics_user_id ON search_analytics(user_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_analytics_event_type ON search_analytics(event_type)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_analytics_preset_id ON search_analytics(preset_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_analytics_timestamp ON search_analytics(timestamp)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_analytics_response_time ON search_analytics(response_time_ms)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_analytics_session ON search_analytics(session_id)"))
            
            logger.info("Created search_analytics table with indexes")
            
            # Create search_result_cache table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS search_result_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key VARCHAR(64) UNIQUE NOT NULL,
                    search_criteria JSON NOT NULL,
                    result_data JSON NOT NULL,
                    result_count INTEGER NOT NULL,
                    response_time_ms INTEGER,
                    hit_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for search_result_cache
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_cache_key ON search_result_cache(cache_key)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_cache_expires ON search_result_cache(expires_at)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_cache_created ON search_result_cache(created_at)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_cache_hit_count ON search_result_cache(hit_count)"))
            
            logger.info("Created search_result_cache table with indexes")
            
            # Create search_suggestions table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS search_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suggestion_text VARCHAR(500) NOT NULL,
                    suggestion_type VARCHAR(50) NOT NULL,
                    category VARCHAR(50),
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    relevance_score REAL DEFAULT 1.0,
                    source_type VARCHAR(50),
                    language VARCHAR(10) DEFAULT 'en',
                    suggestion_metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME
                )
            """))
            
            # Create indexes for search_suggestions
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_suggestion_text ON search_suggestions(suggestion_text)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_suggestion_type ON search_suggestions(suggestion_type)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_suggestion_usage ON search_suggestions(usage_count)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_suggestion_relevance ON search_suggestions(relevance_score)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_suggestion_category ON search_suggestions(category)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_search_suggestion_composite ON search_suggestions(suggestion_type, usage_count, relevance_score)"))
            
            logger.info("Created search_suggestions table with indexes")
            
            # Add enhanced search indexes to existing video and artist tables
            try:
                # Full-text search indexes for videos
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_video_title_fts ON videos(title)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_video_description_fts ON videos(description)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_video_search_keywords ON videos(search_keywords)"))
                
                # Composite indexes for common search patterns
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_video_search_composite ON videos(status, title, artist_id)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_video_quality_year ON videos(quality, year)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_video_duration_status ON videos(duration, status)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_video_genres_status ON videos(status) WHERE genres IS NOT NULL"))
                
                # Artist search indexes
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_artist_name_fts ON artists(name)"))
                session.execute(text("CREATE INDEX IF NOT EXISTS idx_artist_search_composite ON artists(monitored, name, source)"))
                
                logger.info("Created enhanced search indexes on existing tables")
                
            except Exception as e:
                logger.warning(f"Some indexes may already exist: {e}")
            
            # Insert default system search presets
            system_presets = [
                {
                    'name': 'Recently Added',
                    'description': 'Videos added in the last 7 days',
                    'criteria': '{"created_after": "", "sort_by": "created_at", "sort_order": "desc"}'
                },
                {
                    'name': 'High Quality Videos',
                    'description': 'Videos in 1080p or higher quality',
                    'criteria': '{"quality": ["1080p", "1440p", "2160p", "4K"], "sort_by": "quality", "sort_order": "desc"}'
                },
                {
                    'name': 'Downloaded Videos',
                    'description': 'All downloaded videos',
                    'criteria': '{"status": ["DOWNLOADED"], "sort_by": "created_at", "sort_order": "desc"}'
                },
                {
                    'name': 'Wanted Videos',
                    'description': 'Videos marked as wanted but not yet downloaded',
                    'criteria': '{"status": ["WANTED"], "sort_by": "created_at", "sort_order": "desc"}'
                },
                {
                    'name': 'Videos with Thumbnails',
                    'description': 'Videos that have thumbnail images',
                    'criteria': '{"has_thumbnail": true, "sort_by": "created_at", "sort_order": "desc"}'
                },
                {
                    'name': 'Long Format Videos',
                    'description': 'Videos longer than 5 minutes',
                    'criteria': '{"duration_range": {"min": 300}, "sort_by": "duration", "sort_order": "desc"}'
                }
            ]
            
            for preset in system_presets:
                # Check if preset already exists
                existing = session.execute(text("""
                    SELECT id FROM search_presets 
                    WHERE name = :name AND preset_type = 'SYSTEM'
                """), {'name': preset['name']}).fetchone()
                
                if not existing:
                    session.execute(text("""
                        INSERT INTO search_presets (
                            user_id, name, description, search_criteria, 
                            preset_type, is_public
                        ) VALUES (
                            NULL, :name, :description, :criteria, 
                            'SYSTEM', 1
                        )
                    """), {
                        'name': preset['name'],
                        'description': preset['description'],
                        'criteria': preset['criteria']
                    })
            
            logger.info("Created system search presets")
            
            # Populate search suggestions from existing data
            try:
                # Add artist names as suggestions
                session.execute(text("""
                    INSERT OR IGNORE INTO search_suggestions (
                        suggestion_text, suggestion_type, category, 
                        source_type, relevance_score
                    )
                    SELECT DISTINCT 
                        name, 'artist', 'Artist Name',
                        'existing_data', 2.0
                    FROM artists 
                    WHERE name IS NOT NULL AND trim(name) != ''
                """))
                
                # Add video titles as suggestions (limit to avoid too many)
                session.execute(text("""
                    INSERT OR IGNORE INTO search_suggestions (
                        suggestion_text, suggestion_type, category,
                        source_type, relevance_score
                    )
                    SELECT DISTINCT 
                        title, 'title', 'Video Title',
                        'existing_data', 1.5
                    FROM videos 
                    WHERE title IS NOT NULL AND trim(title) != ''
                    AND length(title) > 3
                    LIMIT 1000
                """))
                
                logger.info("Populated initial search suggestions from existing data")
                
            except Exception as e:
                logger.warning(f"Error populating search suggestions: {e}")
            
            session.commit()
            logger.info("Migration 008 completed successfully: Advanced search tables created")
            
    except Exception as e:
        logger.error(f"Migration 008 failed: {e}")
        raise

def downgrade():
    """Remove advanced search tables"""
    try:
        with get_db() as session:
            logger.info("Starting downgrade of migration 008")
            
            # Drop tables in reverse order of dependencies
            session.execute(text("DROP TABLE IF EXISTS search_suggestions"))
            session.execute(text("DROP TABLE IF EXISTS search_result_cache"))
            session.execute(text("DROP TABLE IF EXISTS search_analytics"))
            session.execute(text("DROP TABLE IF EXISTS search_presets"))
            
            # Remove enhanced indexes
            session.execute(text("DROP INDEX IF EXISTS idx_video_title_fts"))
            session.execute(text("DROP INDEX IF EXISTS idx_video_description_fts"))
            session.execute(text("DROP INDEX IF EXISTS idx_video_search_keywords"))
            session.execute(text("DROP INDEX IF EXISTS idx_video_search_composite"))
            session.execute(text("DROP INDEX IF EXISTS idx_video_quality_year"))
            session.execute(text("DROP INDEX IF EXISTS idx_video_duration_status"))
            session.execute(text("DROP INDEX IF EXISTS idx_video_genres_status"))
            session.execute(text("DROP INDEX IF EXISTS idx_artist_name_fts"))
            session.execute(text("DROP INDEX IF EXISTS idx_artist_search_composite"))
            
            session.commit()
            logger.info("Migration 008 downgrade completed successfully")
            
    except Exception as e:
        logger.error(f"Migration 008 downgrade failed: {e}")
        raise

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Search Tables Migration')
    parser.add_argument('--downgrade', action='store_true', 
                       help='Run downgrade instead of upgrade')
    
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade()
    else:
        upgrade()