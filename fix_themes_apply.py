#!/usr/bin/env python3
"""
Script to fix the apply_theme function in the running container
"""

import subprocess

# The fixed apply_theme function content
apply_theme_fix = '''@themes_bp.route("/apply", methods=["POST"])
@simple_auth_required
def apply_theme():
    """Apply a theme to the current user"""
    try:
        data = request.get_json()
        theme_name = data.get("theme_name")
        
        if not theme_name:
            return jsonify({"error": "Theme name is required"}), 400
        
        # Save theme preference using settings service
        try:
            from src.services.settings_service import SettingsService
            success = SettingsService.set("ui_theme", theme_name)
            if success:
                # Don't try to log with request.current_user.id as it causes SQLAlchemy session errors
                logger.info(f"Applied theme '{theme_name}' for user {getattr(request.current_user, 'username', 'unknown')}")
                return jsonify({"message": f"Theme '{theme_name}' applied successfully"})
            else:
                logger.error(f"Settings service failed to save theme preference for '{theme_name}'")
                return jsonify({"error": "Failed to save theme preference"}), 500
        except Exception as settings_error:
            # Check if it's the known SQLAlchemy session error but theme was actually saved
            error_str = str(settings_error)
            if "is not bound to a Session" in error_str:
                logger.warning(f"SQLAlchemy session error after successful theme save: {settings_error}")
                # Check if theme was actually saved despite the error
                try:
                    from src.services.settings_service import SettingsService
                    current_theme = SettingsService.get("ui_theme", "default")
                    if current_theme == theme_name:
                        logger.info(f"Theme '{theme_name}' was successfully saved despite session error")
                        return jsonify({"message": f"Theme '{theme_name}' applied successfully"})
                except Exception:
                    pass
            
            logger.error(f"Error saving theme preference: {settings_error}")
            return jsonify({"error": "Failed to save theme preference"}), 500
            
    except Exception as e:
        logger.error(f"Error applying theme: {e}")
        return jsonify({"error": "Failed to apply theme", "details": str(e)}), 500'''

def fix_container_theme_apply():
    """Fix the apply_theme function in the running container"""
    
    # Read the current themes.py file from the container
    result = subprocess.run([
        'docker', 'exec', 'mvidarr', 'cat', '/app/src/api/themes.py'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Failed to read themes.py: {result.stderr}")
        return False
    
    content = result.stdout
    
    # Find the apply_theme function and replace it
    lines = content.split('\n')
    new_lines = []
    i = 0
    in_apply_function = False
    function_indent = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for the start of apply_theme function
        if '@themes_bp.route("/apply", methods=["POST"])' in line:
            # Found the function, replace it entirely
            new_lines.extend(apply_theme_fix.split('\n'))
            
            # Skip ahead until we find the end of the current function
            i += 1
            while i < len(lines):
                line = lines[i]
                # Look for the next function definition or end of file
                if (line.strip().startswith('@') and 'route' in line) or (line.strip().startswith('def ') and line[0] not in [' ', '\t']):
                    # Found next function, don't skip this line
                    break
                elif line.strip().startswith('# Note:') and 'Built-in theme' in line:
                    # Found the comment section, don't skip this line
                    break
                i += 1
            continue
        else:
            new_lines.append(line)
        
        i += 1
    
    # Write the fixed content back to a temp file and copy to container
    fixed_content = '\n'.join(new_lines)
    
    with open('/tmp/themes_fixed.py', 'w') as f:
        f.write(fixed_content)
    
    # Copy the fixed file to the container
    result = subprocess.run([
        'docker', 'cp', '/tmp/themes_fixed.py', 'mvidarr:/app/src/api/themes.py'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Failed to copy fixed file: {result.stderr}")
        return False
    
    print("Successfully fixed the apply_theme function in the container")
    return True

if __name__ == "__main__":
    fix_container_theme_apply()