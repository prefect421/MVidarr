"""
Simple authentication API endpoints for single-user system
"""

from flask import Blueprint, request, jsonify, session as flask_session, redirect, render_template
from src.services.simple_auth_service import SimpleAuthService
from src.utils.logger import get_logger

logger = get_logger('mvidarr.simple_auth.api')

# Create simple authentication blueprint
simple_auth_bp = Blueprint('simple_auth', __name__, url_prefix='/auth')

@simple_auth_bp.route('/login', methods=['GET'])
def login_page():
    """Show simple login page"""
    try:
        # Check if user is already authenticated
        if SimpleAuthService.is_authenticated():
            return redirect('/')
        
        # Check if credentials are still defaults
        username, has_credentials = SimpleAuthService.get_credentials()
        
        # Show default credentials if:
        # 1. No credentials are configured, OR
        # 2. Username is 'admin' AND password is still the default 'mvidarr'
        show_default_creds = False
        try:
            if not has_credentials:
                show_default_creds = True
            elif username == 'admin' and SimpleAuthService._is_default_password():
                show_default_creds = True
        except Exception:
            # On any error, assume we should show defaults (safer for new installs)
            show_default_creds = True
        
        # Show login page
        error = request.args.get('error')
        return render_template('auth/simple_login.html', 
                             show_default_credentials=show_default_creds,
                             error=error)
        
    except Exception as e:
        logger.error(f"Login page error: {e}")
        return render_template('auth/simple_login.html', error="Failed to load login page")

@simple_auth_bp.route('/login', methods=['POST'])
def login():
    """Simple user login endpoint"""
    try:
        # Get login credentials
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Authenticate user
        success, message = SimpleAuthService.authenticate(username, password)
        
        if success:
            # Log user in
            SimpleAuthService.login_user(username)
            
            # Handle different response types
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'username': username,
                        'authenticated': True
                    }
                })
            else:
                # Redirect for form submissions
                next_url = request.args.get('next', '/')
                return redirect(next_url)
        else:
            # Login failed
            if request.is_json:
                return jsonify({'error': message}), 401
            else:
                return redirect('/auth/login?error=' + message)
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed due to internal error'}), 500

@simple_auth_bp.route('/logout', methods=['POST'])
def logout():
    """Simple user logout endpoint"""
    try:
        username = SimpleAuthService.get_current_username()
        SimpleAuthService.logout_user()
        
        return jsonify({'success': True, 'message': 'Logged out successfully'})
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@simple_auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check simple authentication status"""
    try:
        is_authenticated = SimpleAuthService.is_authenticated()
        username = SimpleAuthService.get_current_username()
        
        if is_authenticated and username:
            return jsonify({
                'authenticated': True,
                'user': {
                    'username': username,
                    'authenticated': True
                }
            })
        else:
            return jsonify({'authenticated': False})
        
    except Exception as e:
        logger.error(f"Auth check error: {e}")
        return jsonify({'authenticated': False, 'error': 'Check failed'}), 500

@simple_auth_bp.route('/credentials', methods=['GET'])
def get_credentials():
    """Get current stored username (password not returned)"""
    try:
        username, has_credentials = SimpleAuthService.get_credentials()
        
        return jsonify({
            'username': username,
            'has_credentials': has_credentials
        })
        
    except Exception as e:
        logger.error(f"Get credentials error: {e}")
        return jsonify({'error': 'Failed to get credentials'}), 500

@simple_auth_bp.route('/credentials', methods=['POST'])
def update_credentials():
    """Update username and password"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        success, message = SimpleAuthService.set_credentials(username, password)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"Update credentials error: {e}")
        return jsonify({'error': 'Failed to update credentials'}), 500

@simple_auth_bp.route('/credentials/reset', methods=['POST'])
def reset_credentials():
    """Reset credentials to default values"""
    try:
        created, username, password, message = SimpleAuthService.initialize_default_credentials()
        
        if created or username:  # Success if created new or already exists
            return jsonify({
                'success': True, 
                'message': message,
                'username': username,
                'default_password': password if created else 'mvidarr'
            })
        else:
            return jsonify({'error': message}), 500
            
    except Exception as e:
        logger.error(f"Reset credentials error: {e}")
        return jsonify({'error': 'Failed to reset credentials'}), 500

# Register the blueprint with the app
def register_simple_auth_routes(app):
    """Register simple authentication routes with Flask app"""
    app.register_blueprint(simple_auth_bp)
    logger.info("Simple authentication routes registered")