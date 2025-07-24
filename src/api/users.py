"""
User management API endpoints for MVidarr Enhanced
Provides administrative user management functionality.
"""

from flask import Blueprint, request, jsonify, session as flask_session
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService, AuditEventType
from src.database.models import UserRole, User
from src.utils.auth_decorators import login_required, admin_required, role_required
from src.utils.logger import get_logger

logger = get_logger('mvidarr.users.api')

# Create users blueprint
users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/', methods=['GET'])
@login_required
def list_users():
    """List all users (admin only for full list, users can see basic info)"""
    try:
        current_user = request.current_user
        
        # Admin can see all users with sensitive info
        if current_user.can_manage_users():
            users = AuthService.get_users(include_inactive=True)
            users_data = [user.to_dict(include_sensitive=True) for user in users]
            
            AuditService.log_admin_action(
                "list_all_users",
                admin_user=current_user,
                additional_data={"user_count": len(users)}
            )
            
            return jsonify({
                'users': users_data,
                'total': len(users_data),
                'can_manage': True
            })
        else:
            # Regular users can only see basic user info (for UI purposes)
            users = AuthService.get_users(include_inactive=False)
            users_data = [
                {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role.value,
                    'is_active': user.is_active
                } 
                for user in users
            ]
            
            return jsonify({
                'users': users_data,
                'total': len(users_data),
                'can_manage': False
            })
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({'error': 'Failed to list users'}), 500

@users_bp.route('/', methods=['POST'])
@admin_required
def create_user():
    """Create a new user (admin only)"""
    try:
        admin_user = request.current_user
        data = request.get_json()
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role_str = data.get('role', 'USER').upper()
        
        # Validate input
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Validate role
        try:
            role = UserRole[role_str]
        except KeyError:
            return jsonify({'error': f'Invalid role: {role_str}'}), 400
        
        # Create user
        success, message, user = AuthService.create_user(username, email, password, role)
        
        if success:
            AuditService.log_admin_action(
                "create_user",
                target_user=user,
                admin_user=admin_user,
                additional_data={
                    "new_user_role": role.value,
                    "new_user_email": email
                }
            )
            
            return jsonify({
                'success': True,
                'message': message,
                'user': user.to_dict()
            }), 201
        else:
            return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return jsonify({'error': 'Failed to create user'}), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Get user details"""
    try:
        current_user = request.current_user
        
        # Users can only see their own details unless they're admin
        if user_id != current_user.id and not current_user.can_manage_users():
            AuditService.log_authorization_event(
                AuditEventType.ACCESS_DENIED,
                f"Attempted to access user details for user {user_id}",
                user=current_user,
                resource="user_details",
                action="view",
                granted=False
            )
            return jsonify({'error': 'Access denied'}), 403
        
        # Get user from database
        from src.database.connection import get_db
        
        with get_db() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Return appropriate level of detail
            include_sensitive = current_user.can_manage_users() or user_id == current_user.id
            return jsonify({
                'user': user.to_dict(include_sensitive=include_sensitive)
            })
        
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({'error': 'Failed to get user'}), 500

@users_bp.route('/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    """Update user role (admin only)"""
    try:
        admin_user = request.current_user
        data = request.get_json()
        
        new_role_str = data.get('role', '').upper()
        
        # Validate role
        try:
            new_role = UserRole[new_role_str]
        except KeyError:
            return jsonify({'error': f'Invalid role: {new_role_str}'}), 400
        
        # Update role
        success, message = AuthService.update_user_role(user_id, new_role, admin_user.id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Update user role error: {e}")
        return jsonify({'error': 'Failed to update user role'}), 500

@users_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    """Deactivate user account (admin only)"""
    try:
        admin_user = request.current_user
        
        # Deactivate user
        success, message = AuthService.deactivate_user(user_id, admin_user.id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Deactivate user error: {e}")
        return jsonify({'error': 'Failed to deactivate user'}), 500

@users_bp.route('/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    """Activate user account (admin only)"""
    try:
        admin_user = request.current_user
        
        from src.database.connection import get_db
        
        with get_db() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.is_active:
                return jsonify({'error': 'User is already active'}), 400
            
            # Activate user
            user.is_active = True
            user.unlock_account()  # Also unlock if locked
            session.commit()
            
            AuditService.log_admin_action(
                "activate_user",
                target_user=user,
                admin_user=admin_user
            )
            
            return jsonify({'success': True, 'message': 'User activated successfully'})
        
    except Exception as e:
        logger.error(f"Activate user error: {e}")
        return jsonify({'error': 'Failed to activate user'}), 500

@users_bp.route('/<int:user_id>/unlock', methods=['POST'])
@admin_required
def unlock_user(user_id):
    """Unlock user account (admin only)"""
    try:
        admin_user = request.current_user
        
        from src.database.connection import get_db
        
        with get_db() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.is_locked():
                return jsonify({'error': 'User account is not locked'}), 400
            
            # Unlock user
            user.unlock_account()
            session.commit()
            
            AuditService.log_admin_action(
                "unlock_user",
                target_user=user,
                admin_user=admin_user
            )
            
            return jsonify({'success': True, 'message': 'User account unlocked successfully'})
        
    except Exception as e:
        logger.error(f"Unlock user error: {e}")
        return jsonify({'error': 'Failed to unlock user'}), 500

@users_bp.route('/<int:user_id>/sessions', methods=['GET'])
@login_required
def get_user_sessions(user_id):
    """Get user sessions"""
    try:
        current_user = request.current_user
        
        # Users can only see their own sessions unless they're admin
        if user_id != current_user.id and not current_user.can_manage_users():
            return jsonify({'error': 'Access denied'}), 403
        
        from src.database.connection import get_db
        from src.database.models import UserSession, SessionStatus
        
        with get_db() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get active sessions
            sessions = session.query(UserSession).filter_by(
                user_id=user_id,
                status=SessionStatus.ACTIVE
            ).order_by(UserSession.last_activity.desc()).all()
            
            current_session_token = flask_session.get('session_token')
            
            sessions_data = []
            for user_session in sessions:
                session_data = user_session.to_dict()
                session_data['is_current'] = user_session.session_token == current_session_token
                sessions_data.append(session_data)
            
            return jsonify({
                'sessions': sessions_data,
                'total': len(sessions_data)
            })
        
    except Exception as e:
        logger.error(f"Get user sessions error: {e}")
        return jsonify({'error': 'Failed to get user sessions'}), 500

@users_bp.route('/<int:user_id>/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def revoke_user_session(user_id, session_id):
    """Revoke a user session"""
    try:
        current_user = request.current_user
        
        # Users can only revoke their own sessions unless they're admin
        if user_id != current_user.id and not current_user.can_manage_users():
            return jsonify({'error': 'Access denied'}), 403
        
        from src.database.connection import get_db
        from src.database.models import UserSession
        
        with get_db() as session:
            # Find the session
            user_session = session.query(UserSession).filter_by(
                id=session_id,
                user_id=user_id
            ).first()
            
            if not user_session:
                return jsonify({'error': 'Session not found'}), 404
            
            # Check if trying to revoke current session
            current_session_token = flask_session.get('session_token')
            is_current_session = user_session.session_token == current_session_token
            
            # Revoke the session
            user_session.revoke()
            session.commit()
            
            # Log the action
            if current_user.can_manage_users() and user_id != current_user.id:
                AuditService.log_admin_action(
                    "revoke_user_session",
                    target_user=user_session.user,
                    admin_user=current_user,
                    additional_data={'session_id': session_id}
                )
            else:
                AuditService.log_event(
                    "session_revoked",
                    f"User revoked {'current' if is_current_session else 'other'} session",
                    user_id=current_user.id,
                    username=current_user.username,
                    additional_data={'session_id': session_id, 'is_current': is_current_session}
                )
            
            response_data = {
                'success': True,
                'message': 'Session revoked',
                'current_session_revoked': is_current_session
            }
            
            # If current session was revoked, clear Flask session
            if is_current_session:
                flask_session.clear()
                response_data['redirect_to_login'] = True
            
            return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Revoke user session error: {e}")
        return jsonify({'error': 'Failed to revoke session'}), 500

@users_bp.route('/<int:user_id>/sessions', methods=['DELETE'])
@login_required
def revoke_all_user_sessions(user_id):
    """Revoke all sessions for a user"""
    try:
        current_user = request.current_user
        
        # Users can revoke all their own sessions, admins can revoke any user's sessions
        if user_id != current_user.id and not current_user.can_manage_users():
            return jsonify({'error': 'Access denied'}), 403
        
        # Revoke all sessions
        success = AuthService.logout_all_sessions(user_id)
        
        if success:
            # Log the action
            if current_user.can_manage_users() and user_id != current_user.id:
                from src.database.connection import get_db
                with get_db() as session:
                    target_user = session.query(User).filter_by(id=user_id).first()
                    if target_user:
                        AuditService.log_admin_action(
                            "revoke_all_user_sessions",
                            target_user=target_user,
                            admin_user=current_user
                        )
            else:
                AuditService.log_event(
                    "all_sessions_revoked",
                    "User revoked all sessions",
                    user_id=current_user.id,
                    username=current_user.username
                )
            
            response_data = {
                'success': True,
                'message': 'All sessions revoked'
            }
            
            # If user revoked their own sessions, clear Flask session
            if user_id == current_user.id:
                flask_session.clear()
                response_data['redirect_to_login'] = True
            
            return jsonify(response_data)
        else:
            return jsonify({'error': 'Failed to revoke sessions'}), 500
        
    except Exception as e:
        logger.error(f"Revoke all user sessions error: {e}")
        return jsonify({'error': 'Failed to revoke all sessions'}), 500

@users_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user's information"""
    try:
        user = request.current_user
        
        return jsonify({
            'user': user.to_dict(include_sensitive=True),
            'permissions': {
                'can_admin': user.can_access_admin(),
                'can_modify': user.can_modify_content(),
                'can_delete': user.can_delete_content(),
                'can_manage_users': user.can_manage_users()
            }
        })
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({'error': 'Failed to get user info'}), 500

@users_bp.route('/me/preferences', methods=['PUT'])
@login_required
def update_user_preferences():
    """Update current user's preferences"""
    try:
        user = request.current_user
        data = request.get_json()
        
        preferences = data.get('preferences', {})
        
        # Validate preferences (basic validation)
        if not isinstance(preferences, dict):
            return jsonify({'error': 'Preferences must be a JSON object'}), 400
        
        from src.database.connection import get_db
        
        with get_db() as session:
            # Get fresh user object
            fresh_user = session.query(User).filter_by(id=user.id).first()
            
            if not fresh_user:
                return jsonify({'error': 'User not found'}), 404
            
            # Update preferences
            if not fresh_user.preferences:
                fresh_user.preferences = {}
            
            fresh_user.preferences.update(preferences)
            session.commit()
            
            AuditService.log_event(
                "user_preferences_updated",
                "User updated preferences",
                user_id=user.id,
                username=user.username,
                additional_data={"updated_keys": list(preferences.keys())}
            )
            
            return jsonify({
                'success': True,
                'message': 'Preferences updated',
                'preferences': fresh_user.preferences
            })
        
    except Exception as e:
        logger.error(f"Update user preferences error: {e}")
        return jsonify({'error': 'Failed to update preferences'}), 500

# Register the blueprint with the app
def register_users_routes(app):
    """Register user management routes with Flask app"""
    app.register_blueprint(users_bp)
    logger.info("User management routes registered")