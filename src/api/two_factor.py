"""
Two-Factor Authentication API for MVidarr Enhanced
Provides TOTP setup, verification, and management endpoints.
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from datetime import datetime, timezone

from src.services.two_factor_service import TwoFactorService
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.database.models import User, UserRole
from src.utils.auth_decorators import login_required, admin_required
from src.database.connection import get_db
from src.utils.logger import get_logger

logger = get_logger('mvidarr.two_factor')

# Create 2FA blueprint
two_factor_bp = Blueprint('two_factor', __name__, url_prefix='/2fa')

@two_factor_bp.route('/setup')
@login_required
def setup_page():
    """2FA setup page"""
    try:
        user = request.current_user
        
        # Check if 2FA is already enabled
        if user.two_factor_enabled:
            flash("Two-factor authentication is already enabled for your account.", 'info')
            return redirect(url_for('profile.profile_page'))
        
        return render_template('auth/2fa_setup.html', user=user)
        
    except Exception as e:
        logger.error(f"2FA setup page error: {e}")
        flash(f"Error loading 2FA setup: {e}", 'error')
        return redirect(url_for('profile.profile_page'))

@two_factor_bp.route('/api/setup', methods=['POST'])
@login_required
def initiate_setup():
    """Initiate 2FA setup"""
    try:
        user = request.current_user
        
        if user.two_factor_enabled:
            return jsonify({'error': 'Two-factor authentication is already enabled'}), 400
        
        success, message, setup_data = TwoFactorService.setup_two_factor(user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'setup_data': {
                    'qr_code': setup_data['qr_code'],
                    'manual_entry_key': setup_data['manual_entry_key'],
                    'backup_codes': setup_data['backup_codes']
                }
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"2FA setup initiation error: {e}")
        return jsonify({'error': 'Failed to initiate 2FA setup'}), 500

@two_factor_bp.route('/api/verify-setup', methods=['POST'])
@login_required
def verify_setup():
    """Verify and confirm 2FA setup"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({'error': 'Verification token is required'}), 400
        
        token = data['token'].strip()
        
        success, message = TwoFactorService.confirm_two_factor_setup(user.id, token)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"2FA setup verification error: {e}")
        return jsonify({'error': 'Failed to verify 2FA setup'}), 500

@two_factor_bp.route('/api/disable', methods=['POST'])
@login_required
def disable_two_factor():
    """Disable 2FA for current user"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data or 'password' not in data:
            return jsonify({'error': 'Password is required to disable 2FA'}), 400
        
        password = data['password']
        
        success, message = TwoFactorService.disable_two_factor(user.id, password)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"2FA disable error: {e}")
        return jsonify({'error': 'Failed to disable 2FA'}), 500

@two_factor_bp.route('/api/regenerate-codes', methods=['POST'])
@login_required
def regenerate_backup_codes():
    """Regenerate backup codes"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data or 'password' not in data:
            return jsonify({'error': 'Password is required to regenerate backup codes'}), 400
        
        password = data['password']
        
        success, message, new_codes = TwoFactorService.regenerate_backup_codes(user.id, password)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'backup_codes': new_codes
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"Backup codes regeneration error: {e}")
        return jsonify({'error': 'Failed to regenerate backup codes'}), 500

@two_factor_bp.route('/api/status')
@login_required
def get_status():
    """Get 2FA status for current user"""
    try:
        user = request.current_user
        status = TwoFactorService.get_two_factor_status(user.id)
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"2FA status error: {e}")
        return jsonify({'error': 'Failed to get 2FA status'}), 500

@two_factor_bp.route('/verify')
def verify_page():
    """2FA verification page for login"""
    # This would be called during login flow
    # Check if user is in 2FA pending state
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login_page'))
    
    return render_template('auth/2fa_verify.html', user_id=user_id)

@two_factor_bp.route('/api/verify-login', methods=['POST'])
def verify_login():
    """Verify 2FA token during login process"""
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'token' not in data:
            return jsonify({'error': 'User ID and verification token are required'}), 400
        
        user_id = data['user_id']
        token = data['token'].strip()
        
        success, message = TwoFactorService.verify_two_factor_login(user_id, token)
        
        if success:
            # Complete the login process
            with get_db() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    # Create session (this would integrate with AuthService)
                    session_token = AuthService.create_user_session(
                        user,
                        request.remote_addr,
                        request.headers.get('User-Agent', 'Unknown')
                    )
                    
                    return jsonify({
                        'success': True,
                        'message': 'Login successful',
                        'session_token': session_token,
                        'redirect_url': '/'
                    })
                else:
                    return jsonify({'error': 'User not found'}), 404
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"2FA login verification error: {e}")
        return jsonify({'error': 'Failed to verify 2FA token'}), 500

# Admin endpoints for 2FA management
@two_factor_bp.route('/admin/users/<int:user_id>/disable', methods=['POST'])
@admin_required
def admin_disable_two_factor(user_id):
    """Admin disable 2FA for user"""
    try:
        admin_user = request.current_user
        
        success, message = TwoFactorService.disable_two_factor(
            user_id, 
            password=None, 
            admin_user_id=admin_user.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"Admin 2FA disable error: {e}")
        return jsonify({'error': 'Failed to disable 2FA'}), 500

@two_factor_bp.route('/admin/users/<int:user_id>/regenerate-codes', methods=['POST'])
@admin_required
def admin_regenerate_backup_codes(user_id):
    """Admin regenerate backup codes for user"""
    try:
        admin_user = request.current_user
        
        success, message, new_codes = TwoFactorService.regenerate_backup_codes(
            user_id, 
            password=None, 
            admin_user_id=admin_user.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'backup_codes': new_codes
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"Admin backup codes regeneration error: {e}")
        return jsonify({'error': 'Failed to regenerate backup codes'}), 500

@two_factor_bp.route('/admin/users/<int:user_id>/status')
@admin_required
def admin_get_user_status(user_id):
    """Admin get 2FA status for specific user"""
    try:
        status = TwoFactorService.get_two_factor_status(user_id)
        
        # Get user info
        with get_db() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            user_info = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.value
            }
        
        return jsonify({
            'success': True,
            'user': user_info,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Admin 2FA status error: {e}")
        return jsonify({'error': 'Failed to get 2FA status'}), 500

@two_factor_bp.route('/admin/overview')
@admin_required
def admin_overview():
    """Admin 2FA overview page"""
    try:
        # Get 2FA statistics
        with get_db() as session:
            total_users = session.query(User).count()
            enabled_users = session.query(User).filter_by(two_factor_enabled=True).count()
            pending_setup = session.query(User).filter(
                User.two_factor_secret.isnot(None),
                User.two_factor_enabled == False
            ).count()
            
            users_with_2fa = session.query(User).filter_by(two_factor_enabled=True).all()
        
        stats = {
            'total_users': total_users,
            'enabled_users': enabled_users,
            'pending_setup': pending_setup,
            'enabled_percentage': round((enabled_users / total_users * 100) if total_users > 0 else 0, 1)
        }
        
        return render_template('admin/2fa_overview.html', 
                             stats=stats, 
                             users_with_2fa=users_with_2fa)
        
    except Exception as e:
        logger.error(f"Admin 2FA overview error: {e}")
        flash(f"Error loading 2FA overview: {e}", 'error')
        return redirect(url_for('admin.dashboard'))

# Integration with existing auth flow
def integrate_2fa_with_login():
    """
    Integration point for 2FA with existing login flow.
    This should be called from the main auth service during login.
    """
    pass

# Register the blueprint
def register_two_factor_routes(app):
    """Register 2FA routes with Flask app"""
    app.register_blueprint(two_factor_bp)
    logger.info("Two-factor authentication routes registered")