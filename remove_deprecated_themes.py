#!/usr/bin/env python3
"""
Remove deprecated themes from MVidarr database.
Removes: LCARS (New), TARDIS, MTV themes from custom_themes table.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.connection import get_db
from database.models import CustomTheme

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def remove_deprecated_themes():
    """Remove deprecated themes from the database."""
    
    # Themes to remove
    deprecated_themes = [
        "lcars_new",    # "LCARS (New)"
        "tardis",       # "TARDIS" 
        "mtv"           # "MTV"
    ]
    
    logger.info("Starting removal of deprecated themes...")
    
    try:
        with get_db() as session:
            themes_removed = 0
            
            for theme_name in deprecated_themes:
                # Find the theme by name
                theme = session.query(CustomTheme).filter_by(name=theme_name).first()
                
                if theme:
                    logger.info(f"Removing theme: {theme.display_name} ({theme.name})")
                    
                    # Check if anyone is using this theme as their preference
                    # Note: We should check user preferences, but for now we'll just delete
                    
                    session.delete(theme)
                    themes_removed += 1
                else:
                    logger.info(f"Theme '{theme_name}' not found in database (may already be removed)")
            
            # Commit the changes
            if themes_removed > 0:
                session.commit()
                logger.info(f"Successfully removed {themes_removed} deprecated themes from database")
            else:
                logger.info("No deprecated themes found to remove")
                
    except Exception as e:
        logger.error(f"Error removing deprecated themes: {e}")
        return False
    
    return True

def main():
    """Main function."""
    logger.info("MVidarr Deprecated Theme Removal Tool")
    logger.info("=====================================")
    
    # Initialize database connection
    try:
        init_database()
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1
    
    # Remove deprecated themes
    if remove_deprecated_themes():
        logger.info("Theme removal completed successfully")
        return 0
    else:
        logger.error("Theme removal failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())