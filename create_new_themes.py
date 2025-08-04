#!/usr/bin/env python3
"""
Script to create new color themes in the MVidarr database
"""

import json
import sys
import os
from datetime import datetime

# Add the src directory to the path so we can import the models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db
from database.models import CustomTheme, User

def create_themes():
    """Create the four new themes"""
    
    # Initialize database manager first
    from config.config import Config
    from database.connection import DatabaseManager
    import database.connection as db_conn
    
    if db_conn.db_manager is None:
        config = Config()
        db_conn.db_manager = DatabaseManager(config)
    
    with get_db() as session:
        # Get or create a system user for built-in themes
        system_user = session.query(User).filter_by(username='admin').first()
        if not system_user:
            # Create admin user if it doesn't exist
            system_user = User(
                username='admin',
                email='admin@mvidarr.local',
                password='admin_password_placeholder'
            )
            session.add(system_user)
            session.commit()
        
        # Check if themes already exist to avoid duplicates
        existing_themes = session.query(CustomTheme).filter(
            CustomTheme.name.in_(['lcars_new', 'punk77', 'tardis', 'mtv'])
        ).all()
        
        if existing_themes:
            print(f"Found {len(existing_themes)} existing themes, skipping duplicates:")
            for theme in existing_themes:
                print(f"  - {theme.name} ({theme.display_name})")
        
        existing_names = {theme.name for theme in existing_themes}
        
        # Theme 1: LCARS (New) - Based on Star Trek TNG with goldenrod sidebar/topbar
        if 'lcars_new' not in existing_names:
            lcars_theme_data = {
                # Background colors - LCARS characteristic blacks and grays
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a", 
                "--bg-tertiary": "#2a2a2a",
                "--bg-modal": "#111111",
                "--bg-card": "#1e1e1e",
                "--bg-hover": "#333333",
                
                # Sidebar and topbar - Goldenrod as requested
                "--sidebar-bg": "#DAA520",
                "--topbar-bg": "#DAA520",
                
                # Text colors - High contrast for LCARS readability
                "--text-primary": "#ffffff",
                "--text-secondary": "#e0e0e0",
                "--text-muted": "#999999",
                "--text-accent": "#ff9900",  # LCARS orange accent
                "--text-inverse": "#000000",
                
                # LCARS signature colors
                "--btn-primary-bg": "#ff9900",  # LCARS orange
                "--btn-primary-text": "#000000",
                "--btn-secondary-bg": "#99ccff",  # LCARS light blue
                "--btn-secondary-text": "#000000",
                "--btn-danger-bg": "#ff6666",  # LCARS red
                "--btn-danger-text": "#000000",
                
                # Borders and accents
                "--border-primary": "#ff9900",
                "--border-focus": "#99ccff",
                "--border-secondary": "#666666",
                
                # Status colors in LCARS style
                "--success": "#99ff99",  # LCARS green
                "--warning": "#ffcc00",  # LCARS yellow
                "--error": "#ff6666",   # LCARS red
                "--info": "#99ccff",    # LCARS blue
                
                # Additional LCARS elements
                "--accent-color": "#ff9900",
                "--highlight-color": "#99ccff",
                "--muted-color": "#666666"
            }
            
            lcars_theme = CustomTheme(
                name='lcars_new',
                display_name='LCARS (New)',
                description='Star Trek TNG LCARS interface with goldenrod command sections',
                created_by=system_user.id,
                is_public=True,
                is_built_in=True,
                theme_data=lcars_theme_data
            )
            session.add(lcars_theme)
            print("Created LCARS (New) theme")
        
        # Theme 2: Punk'77 - Based on The Clash and Sex Pistols aesthetics
        if 'punk77' not in existing_names:
            punk77_theme_data = {
                # Background - Dark, gritty punk aesthetic
                "--bg-primary": "#0d0d0d",     # Almost black
                "--bg-secondary": "#1a1a1a",   # Dark gray
                "--bg-tertiary": "#262626",    # Medium gray
                "--bg-modal": "#1f1f1f",
                "--bg-card": "#1e1e1e",
                "--bg-hover": "#333333",
                
                # Sidebar and topbar - Punk black with red accents
                "--sidebar-bg": "#000000",
                "--topbar-bg": "#1a0000",      # Very dark red
                
                # Text colors - High contrast punk style
                "--text-primary": "#ffffff",
                "--text-secondary": "#e0e0e0",
                "--text-muted": "#999999",
                "--text-accent": "#ff0040",    # Hot pink/red - Sex Pistols inspired
                "--text-inverse": "#000000",
                
                # Buttons - Punk rock colors
                "--btn-primary-bg": "#ff0040",  # Hot pink
                "--btn-primary-text": "#ffffff",
                "--btn-secondary-bg": "#ffff00", # Yellow - London Calling inspired
                "--btn-secondary-text": "#000000",
                "--btn-danger-bg": "#cc0000",   # Blood red
                "--btn-danger-text": "#ffffff",
                
                # Borders - Sharp punk edges
                "--border-primary": "#ff0040",
                "--border-focus": "#ffff00",
                "--border-secondary": "#666666",
                
                # Status colors - Aggressive punk palette
                "--success": "#00ff00",   # Electric green
                "--warning": "#ffff00",   # Bright yellow
                "--error": "#ff0000",     # Pure red
                "--info": "#ff0080",      # Magenta
                
                # Punk accent colors
                "--accent-color": "#ff0040",
                "--highlight-color": "#ffff00",  
                "--muted-color": "#666666"
            }
            
            punk77_theme = CustomTheme(
                name='punk77',
                display_name="Punk '77",
                description='Raw punk rock aesthetic inspired by The Clash and Sex Pistols',
                created_by=system_user.id,
                is_public=True,
                is_built_in=True,
                theme_data=punk77_theme_data
            )
            session.add(punk77_theme)
            print("Created Punk '77 theme")
        
        # Theme 3: TARDIS - Doctor Who Tennant era with Oxford Blue
        if 'tardis' not in existing_names:
            tardis_theme_data = {
                # Background - TARDIS interior inspired
                "--bg-primary": "#0f1419",     # Very dark blue-black
                "--bg-secondary": "#1a2332",   # Dark blue-gray
                "--bg-tertiary": "#253447",    # Medium blue-gray
                "--bg-modal": "#1e2a3a",
                "--bg-card": "#1c2633",
                "--bg-hover": "#2d3e52",
                
                # Sidebar and topbar - Oxford Blue as requested
                "--sidebar-bg": "#002147",     # Oxford Blue
                "--topbar-bg": "#002147",      # Oxford Blue
                
                # TARDIS console room colors
                "--text-primary": "#ffffff",
                "--text-secondary": "#b8d4f0",  # Light blue
                "--text-muted": "#7a9cc6",     # Muted blue
                "--text-accent": "#4db8ff",    # TARDIS blue
                "--text-inverse": "#000000",
                
                # Buttons - TARDIS control inspired
                "--btn-primary-bg": "#4db8ff",  # TARDIS blue
                "--btn-primary-text": "#ffffff",
                "--btn-secondary-bg": "#ff8c42", # Warm orange (console accent)
                "--btn-secondary-text": "#000000",
                "--btn-danger-bg": "#ff4757",   # Warning red
                "--btn-danger-text": "#ffffff",
                
                # Borders - TARDIS panel lines
                "--border-primary": "#4db8ff",
                "--border-focus": "#70c1ff",
                "--border-secondary": "#4a6b8a",
                
                # Status colors - Time Lord technology
                "--success": "#26d0ce",   # Cyan (time energy)
                "--warning": "#ff8c42",   # Orange (console warning)
                "--error": "#ff4757",     # Red (danger)
                "--info": "#4db8ff",      # TARDIS blue
                
                # TARDIS specific accents
                "--accent-color": "#4db8ff",
                "--highlight-color": "#70c1ff",
                "--muted-color": "#4a6b8a"
            }
            
            tardis_theme = CustomTheme(
                name='tardis',
                display_name='TARDIS',
                description='Doctor Who TARDIS interior inspired by the Tennant era console room',
                created_by=system_user.id,
                is_public=True,
                is_built_in=True,
                theme_data=tardis_theme_data
            )
            session.add(tardis_theme)
            print("Created TARDIS theme")
        
        # Theme 4: MTV - Early 80s neon MTV logo colors
        if 'mtv' not in existing_names:
            mtv_theme_data = {
                # Background - Dark to make neon colors pop
                "--bg-primary": "#0a0a0a",     # Almost black
                "--bg-secondary": "#1a1a1a",   # Dark gray
                "--bg-tertiary": "#2a2a2a",    # Medium dark
                "--bg-modal": "#1f1f1f",
                "--bg-card": "#1e1e1e",
                "--bg-hover": "#333333",
                
                # Sidebar and topbar - MTV neon pink/magenta
                "--sidebar-bg": "#ff1493",     # Deep pink (MTV signature)
                "--topbar-bg": "#ff1493",      # Deep pink
                
                # Text colors - High contrast for neon readability
                "--text-primary": "#ffffff",
                "--text-secondary": "#f0f0f0",
                "--text-muted": "#cccccc",
                "--text-accent": "#00ffff",    # Cyan accent
                "--text-inverse": "#000000",
                
                # Buttons - MTV neon palette
                "--btn-primary-bg": "#00ffff",  # Electric cyan
                "--btn-primary-text": "#000000",
                "--btn-secondary-bg": "#ffff00", # Electric yellow
                "--btn-secondary-text": "#000000",
                "--btn-danger-bg": "#ff0080",   # Hot pink
                "--btn-danger-text": "#ffffff",
                
                # Borders - Neon outlines
                "--border-primary": "#00ffff",
                "--border-focus": "#ffff00",
                "--border-secondary": "#666666",
                
                # Status colors - MTV neon style
                "--success": "#00ff00",   # Electric green
                "--warning": "#ffff00",   # Electric yellow  
                "--error": "#ff0080",     # Hot pink
                "--info": "#00ffff",      # Electric cyan
                
                # MTV neon accents
                "--accent-color": "#ff1493",   # MTV pink
                "--highlight-color": "#00ffff", # Cyan
                "--secondary-accent": "#ffff00", # Yellow
                "--muted-color": "#666666"
            }
            
            mtv_theme = CustomTheme(
                name='mtv',
                display_name='MTV',
                description='Early 80s MTV neon aesthetic with electric colors and bold contrasts',
                created_by=system_user.id,
                is_public=True,
                is_built_in=True,
                theme_data=mtv_theme_data
            )
            session.add(mtv_theme)
            print("Created MTV theme")
        
        # Commit all changes
        session.commit()
        print("\nAll themes created successfully!")
        
        # Display summary
        all_themes = session.query(CustomTheme).all()
        print(f"\nTotal themes in database: {len(all_themes)}")
        for theme in all_themes:
            print(f"  - {theme.name}: {theme.display_name}")

if __name__ == "__main__":
    create_themes()