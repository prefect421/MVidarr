"""
Administrative Web Interface for MVidarr
Provides web-based user management and system administration.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import os
import signal
import subprocess
import threading
import time
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.database.models import UserRole, User
from src.utils.auth_decorators import login_required, admin_required
from src.auth_integration import get_auth_status, get_protection_status
from src.utils.logger import get_logger

logger = get_logger('mvidarr.admin.interface')

# Create admin interface blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    try:
        # Get system status
        auth_status = get_auth_status()
        protection_status = get_protection_status()
        
        # Get user statistics
        users = AuthService.get_users(include_inactive=True)
        user_stats = {
            'total': len(users),
            'active': len([u for u in users if u.is_active]),
            'inactive': len([u for u in users if not u.is_active]),
            'by_role': {}
        }
        
        for role in UserRole:
            user_stats['by_role'][role.value] = len([u for u in users if u.role == role])
        
        return render_template('admin/dashboard.html',
                             auth_status=auth_status,
                             protection_status=protection_status,
                             user_stats=user_stats,
                             users=users[:10])  # Recent 10 users
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        flash(f"Error loading dashboard: {e}", 'error')
        return redirect(url_for('main.index'))

@admin_bp.route('/users')
@admin_required
def users_management():
    """User management interface"""
    try:
        users = AuthService.get_users(include_inactive=True)
        
        return render_template('admin/users.html', users=users)
        
    except Exception as e:
        logger.error(f"Users management error: {e}")
        flash(f"Error loading users: {e}", 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Create new user interface"""
    if request.method == 'GET':
        return render_template('admin/create_user.html', roles=UserRole)
    
    try:
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role_str = request.form.get('role', 'USER').upper()
        
        # Validate role
        try:
            role = UserRole[role_str]
        except KeyError:
            flash(f"Invalid role: {role_str}", 'error')
            return render_template('admin/create_user.html', roles=UserRole)
        
        # Create user
        success, message, user = AuthService.create_user(username, email, password, role)
        
        if success:
            # Log admin action
            AuditService.log_admin_action(
                "create_user",
                target_user=user,
                admin_user=request.current_user,
                additional_data={
                    "new_user_role": role.value,
                    "new_user_email": email
                }
            )
            
            flash(f"User '{username}' created successfully", 'success')
            return redirect(url_for('admin.users_management'))
        else:
            flash(f"Failed to create user: {message}", 'error')
            return render_template('admin/create_user.html', roles=UserRole)
        
    except Exception as e:
        logger.error(f"Create user error: {e}")
        flash(f"Error creating user: {e}", 'error')
        return render_template('admin/create_user.html', roles=UserRole)

@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_details(user_id):
    """User details interface"""
    try:
        from src.database.connection import get_db
        from src.database.models import UserSession, SessionStatus
        
        with get_db() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                flash("User not found", 'error')
                return redirect(url_for('admin.users_management'))
            
            # Get user sessions
            active_sessions = session.query(UserSession).filter_by(
                user_id=user_id,
                status=SessionStatus.ACTIVE
            ).order_by(UserSession.last_activity.desc()).all()
            
            return render_template('admin/user_details.html',
                                 user=user,
                                 active_sessions=active_sessions,
                                 roles=UserRole)
        
    except Exception as e:
        logger.error(f"User details error: {e}")
        flash(f"Error loading user details: {e}", 'error')
        return redirect(url_for('admin.users_management'))

@admin_bp.route('/system')
@admin_required
def system_status():
    """System status interface"""
    try:
        auth_status = get_auth_status()
        protection_status = get_protection_status()
        
        return render_template('admin/system.html',
                             auth_status=auth_status,
                             protection_status=protection_status)
        
    except Exception as e:
        logger.error(f"System status error: {e}")
        flash(f"Error loading system status: {e}", 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/audit')
@admin_required
def audit_log():
    """Audit log interface"""
    try:
        # For now, return a placeholder
        # In a full implementation, you'd query audit logs from database
        return render_template('admin/audit.html')
        
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        flash(f"Error loading audit log: {e}", 'error')
        return redirect(url_for('admin.dashboard'))

# API endpoints for admin interface
@admin_bp.route('/api/users/<int:user_id>/role', methods=['POST'])
@admin_required
def update_user_role_web(user_id):
    """Update user role via web interface"""
    try:
        new_role_str = request.form.get('role', '').upper()
        
        # Validate role
        try:
            new_role = UserRole[new_role_str]
        except KeyError:
            return jsonify({'error': f'Invalid role: {new_role_str}'}), 400
        
        # Update role
        success, message = AuthService.update_user_role(user_id, new_role, request.current_user.id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Update user role web error: {e}")
        return jsonify({'error': 'Failed to update user role'}), 500

@admin_bp.route('/api/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active_web(user_id):
    """Toggle user active status via web interface"""
    try:
        from src.database.connection import get_db
        
        with get_db() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Prevent admin from deactivating themselves
            if user_id == request.current_user.id:
                return jsonify({'error': 'Cannot deactivate your own account'}), 400
            
            if user.is_active:
                # Deactivate user
                success, message = AuthService.deactivate_user(user_id, request.current_user.id)
                action = 'deactivated'
            else:
                # Activate user
                user.is_active = True
                user.unlock_account()
                session.commit()
                
                AuditService.log_admin_action(
                    "activate_user",
                    target_user=user,
                    admin_user=request.current_user
                )
                
                success = True
                message = 'User activated successfully'
                action = 'activated'
            
            if success:
                return jsonify({
                    'success': True,
                    'message': message,
                    'action': action,
                    'new_status': not user.is_active if action == 'deactivated' else True
                })
            else:
                return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Toggle user active web error: {e}")
        return jsonify({'error': 'Failed to toggle user status'}), 500

@admin_bp.route('/system/restart', methods=['POST'])
@admin_required
def restart_application():
    """Restart the MVidarr application (Admin only)"""
    try:
        # Log the restart action for audit trail
        AuditService.log_admin_action(
            "restart_application",
            admin_user=request.current_user,
            additional_data={
                "timestamp": time.time(),
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get('User-Agent', 'Unknown')
            }
        )
        
        logger.warning(f"Application restart initiated by admin user: {request.current_user.username}")
        
        # Schedule restart in a separate thread to allow response to be sent
        def delayed_restart():
            try:
                # Wait 2 seconds to allow response to be sent
                time.sleep(2)
                
                # Get the current process ID
                current_pid = os.getpid()
                
                # Try to restart using systemctl if available (production environment)
                try:
                    result = subprocess.run(['systemctl', 'is-active', 'mvidarr'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        # Service is managed by systemd
                        logger.info("Restarting via systemctl...")
                        subprocess.run(['sudo', 'systemctl', 'restart', 'mvidarr'], 
                                     timeout=10)
                        return
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                    pass
                
                # Try using the manage_service.sh script if available
                script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         'scripts', 'manage_service.sh')
                if os.path.exists(script_path) and os.access(script_path, os.X_OK):
                    logger.info("Restarting via manage_service.sh...")
                    subprocess.run([script_path, 'restart'], timeout=10)
                    return
                
                # Fallback: Signal the current process to restart
                logger.info("Performing graceful process restart...")
                
                # Send SIGTERM to self (graceful shutdown)
                os.kill(current_pid, signal.SIGTERM)
                
            except Exception as e:
                logger.error(f"Failed to restart application: {e}")
        
        # Start the restart process in background
        restart_thread = threading.Thread(target=delayed_restart, daemon=True)
        restart_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Application restart initiated. The service will be back online shortly.',
            'estimated_downtime': '10-30 seconds'
        })
        
    except Exception as e:
        logger.error(f"Restart application error: {e}")
        return jsonify({'error': 'Failed to initiate application restart'}), 500

@admin_bp.route('/system/status/service')
@admin_required
def service_status():
    """Get service status information (Admin only)"""
    try:
        status_info = {
            'pid': os.getpid(),
            'uptime': None,
            'service_type': 'unknown',
            'restart_available': False
        }
        
        # Check if running under systemd
        try:
            result = subprocess.run(['systemctl', 'is-active', 'mvidarr'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                status_info['service_type'] = 'systemd'
                status_info['restart_available'] = True
                
                # Get service status details
                status_result = subprocess.run(['systemctl', 'status', 'mvidarr', '--no-pager'], 
                                             capture_output=True, text=True, timeout=5)
                if status_result.returncode == 0:
                    status_info['service_details'] = status_result.stdout
                    
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Check for manage_service.sh script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'scripts', 'manage_service.sh')
        if os.path.exists(script_path) and os.access(script_path, os.X_OK):
            if status_info['service_type'] == 'unknown':
                status_info['service_type'] = 'script'
            status_info['restart_available'] = True
        
        # If no service management found, still allow process restart
        if not status_info['restart_available']:
            status_info['restart_available'] = True
            status_info['service_type'] = 'process'
        
        return jsonify(status_info)
        
    except Exception as e:
        logger.error(f"Service status error: {e}")
        return jsonify({'error': 'Failed to get service status'}), 500

@admin_bp.route('/system/logs/recent')
@admin_required
def recent_logs():
    """Get recent application logs (Admin only)"""
    try:
        log_entries = []
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   'data', 'logs', 'mvidarr.log')
        
        if os.path.exists(log_file_path):
            try:
                # Read last 50 lines of log file
                with open(log_file_path, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                    
                    for line in recent_lines:
                        line = line.strip()
                        if line:
                            log_entries.append(line)
                            
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
                log_entries = [f"Error reading log file: {e}"]
        else:
            log_entries = ["Log file not found"]
        
        return jsonify({
            'log_entries': log_entries,
            'log_file': log_file_path,
            'entry_count': len(log_entries)
        })
        
    except Exception as e:
        logger.error(f"Recent logs error: {e}")
        return jsonify({'error': 'Failed to retrieve recent logs'}), 500

# Register the blueprint with the app
def register_admin_interface(app):
    """Register admin interface routes with Flask app"""
    app.register_blueprint(admin_bp)
    logger.info("Admin interface routes registered")