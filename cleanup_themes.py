#!/usr/bin/env python3
"""
Script to remove old LCARS themes from themes.py
"""

import re

def cleanup_themes_file():
    """Remove old LCARS themes from the themes.py file"""
    
    # Read the original file
    with open('/home/mike/mvidarr/src/api/themes.py', 'r') as f:
        content = f.read()
    
    # Remove lcars_voy theme definition (in extract function)
    # This pattern matches the theme definition with all its CSS variables
    lcars_voy_pattern = r'"lcars_voy": {[^}]*(?:\n[^}]*)*},\s*'
    content = re.sub(lcars_voy_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove lcars_tng_e theme definition (in extract function)
    lcars_tng_e_pattern = r'"lcars_tng_e": {[^}]*(?:\n[^}]*)*},\s*'
    content = re.sub(lcars_tng_e_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove from edit function definitions (around line 1344)
    edit_lcars_voy_pattern = r'"lcars_voy": {\s*"display_name": "LCARS - Voy",\s*"description": "Star Trek: Voyager theme",\s*"variables": {[^}]*(?:\n[^}]*)*}\s*},\s*'
    content = re.sub(edit_lcars_voy_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    edit_lcars_tng_e_pattern = r'"lcars_tng_e": {\s*"display_name": "LCARS - TNG-E",\s*"description": "Star Trek: Enterprise theme",\s*"variables": {[^}]*(?:\n[^}]*)*}\s*},?\s*'
    content = re.sub(edit_lcars_tng_e_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove from duplicate function definitions (around line 1501)
    duplicate_pattern = r'"lcars_ds9": {"display_name": "LCARS - DS9", "description": "Star Trek: Deep Space Nine theme"},\s*"lcars_voy": {"display_name": "LCARS - Voy", "description": "Star Trek: Voyager theme"},\s*"lcars_tng_e": {"display_name": "LCARS - TNG-E", "description": "Star Trek: Enterprise theme"}'
    content = re.sub(duplicate_pattern, '', content, flags=re.MULTILINE)
    
    # Write the cleaned file
    with open('/home/mike/mvidarr/src/api/themes.py', 'w') as f:
        f.write(content)
    
    print("Cleaned up themes.py file - removed old LCARS themes")

if __name__ == "__main__":
    cleanup_themes_file()