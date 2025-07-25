// MVidarr Enhanced - Main JavaScript

// Utility functions - Updated to use toast notifications
function showMessage(message, type = 'info') {
    // Use the global toast manager if available, fallback to console
    if (window.toastManager) {
        return window.toastManager.show(message, type);
    } else if (window.showToast) {
        return window.showToast(message, type);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
        return null;
    }
}

// Note: showSuccess, showError, showWarning, showInfo are defined in toast.js
// This provides the showLoading function that toast.js doesn't have
function showLoading(message) {
    if (window.toastManager) {
        return window.toastManager.loading(message);
    } else {
        console.log(`LOADING: ${message}`);
        return null;
    }
}

// Toast notification system is loaded from toast.js

// API helper functions
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // Non-JSON response, likely an error page
            const text = await response.text();
            throw new Error(`Server returned non-JSON response (${response.status}): ${text.substring(0, 100)}...`);
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Settings management
class SettingsManager {
    static async get(key) {
        try {
            const data = await apiRequest(`/api/settings/${key}`);
            return data.value;
        } catch (error) {
            console.error(`Failed to get setting ${key}:`, error);
            return null;
        }
    }
    
    static async set(key, value) {
        try {
            await apiRequest(`/api/settings/${key}`, {
                method: 'PUT',
                body: JSON.stringify({ value })
            });
            return true;
        } catch (error) {
            console.error(`Failed to set setting ${key}:`, error);
            return false;
        }
    }
    
    static async getAll() {
        try {
            const data = await apiRequest('/api/settings/');
            return data.settings;
        } catch (error) {
            console.error('Failed to get all settings:', error);
            return {};
        }
    }
    
    static async updateMultiple(settings) {
        try {
            await apiRequest('/api/settings/bulk', {
                method: 'PUT',
                body: JSON.stringify({ settings })
            });
            return true;
        } catch (error) {
            console.error('Failed to update multiple settings:', error);
            return false;
        }
    }
}

// System health monitoring
class HealthMonitor {
    static async getStatus() {
        try {
            const data = await apiRequest('/api/health/status');
            return data;
        } catch (error) {
            console.error('Failed to get health status:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }
    
    static async checkDatabase() {
        try {
            const data = await apiRequest('/api/health/database');
            return data;
        } catch (error) {
            console.error('Failed to check database:', error);
            return { status: 'unhealthy', error: error.message };
        }
    }
}

// Loading indicator - Enhanced for toast integration
function showElementLoading(element, message = 'Loading...') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (!element) {
        // Fallback to toast loading if element not found
        return showLoading(message);
    }
    
    const originalContent = element.innerHTML;
    element.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>${message}</p>
        </div>
    `;
    
    return () => {
        element.innerHTML = originalContent;
    };
}

// Global loading indicator using toast
function showGlobalLoading(message = 'Loading...') {
    return showLoading(message);
}

// Add spinner CSS
const spinnerStyle = document.createElement('style');
spinnerStyle.textContent = `
    .loading-spinner {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    }
    
    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #444;
        border-top: 4px solid #00d4ff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(spinnerStyle);

// Form validation
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#ff0000';
            isValid = false;
        } else {
            field.style.borderColor = '#444';
        }
    });
    
    return isValid;
}

// Format utilities
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Global error handler with toast notifications
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    showError('An unexpected error occurred. Please check the console for details.');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    showError('An unexpected error occurred during an operation.');
});

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers for navigation
    const navLinks = document.querySelectorAll('.nav-menu a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked link
            this.classList.add('active');
        });
    });
    
    // Set active navigation item based on current path
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// Thumbnail management functions
class ThumbnailManager {
    static async populateArtistThumbnails(element, limit = 10) {
        const loadingToast = showLoading('Populating artist thumbnails...');
        const hideLoading = element ? showElementLoading(element, 'Processing...') : null;
        
        try {
            const result = await apiRequest('/api/artists/populate-thumbnails', {
                method: 'POST',
                body: JSON.stringify({ limit })
            });
            
            if (loadingToast && window.toastManager) {
                window.toastManager.update(loadingToast, `Updated ${result.updated_count} of ${result.processed_count} artist thumbnails`, 'success');
                setTimeout(() => window.toastManager.removeToast(loadingToast), 3000);
            } else {
                showSuccess(`Updated ${result.updated_count} of ${result.processed_count} artist thumbnails`);
            }
            return result;
        } catch (error) {
            if (loadingToast && window.toastManager) {
                window.toastManager.update(loadingToast, `Failed to populate thumbnails: ${error.message}`, 'error');
            } else {
                showError(`Failed to populate thumbnails: ${error.message}`);
            }
            throw error;
        } finally {
            if (hideLoading) hideLoading();
        }
    }
    
    static async downloadVideoThumbnail(videoId, element) {
        const loadingToast = showLoading('Downloading video thumbnail...');
        const hideLoading = element ? showElementLoading(element, 'Downloading...') : null;
        
        try {
            const result = await apiRequest('/api/video-indexing/thumbnails/download', {
                method: 'POST',
                body: JSON.stringify({ video_id: videoId })
            });
            
            if (loadingToast && window.toastManager) {
                window.toastManager.update(loadingToast, 'Video thumbnail downloaded successfully', 'success');
                setTimeout(() => window.toastManager.removeToast(loadingToast), 3000);
            } else {
                showSuccess('Video thumbnail downloaded successfully');
            }
            return result;
        } catch (error) {
            if (loadingToast && window.toastManager) {
                window.toastManager.update(loadingToast, `Failed to download thumbnail: ${error.message}`, 'error');
            } else {
                showError(`Failed to download thumbnail: ${error.message}`);
            }
            throw error;
        } finally {
            if (hideLoading) hideLoading();
        }
    }
    
    static async getThumbnailStats() {
        try {
            const stats = await apiRequest('/api/video-indexing/thumbnails/stats');
            return stats;
        } catch (error) {
            console.error('Failed to get thumbnail stats:', error);
            return { total_size: 0, total_count: 0, artist_count: 0, video_count: 0 };
        }
    }
    
    static loadThumbnailWithFallback(imgElement, thumbnailUrl, fallbackUrl) {
        if (thumbnailUrl) {
            imgElement.src = thumbnailUrl;
            imgElement.onerror = () => {
                imgElement.src = fallbackUrl;
                imgElement.onerror = null;
            };
        } else {
            imgElement.src = fallbackUrl;
        }
    }
    
    static setupLazyLoading(container) {
        const images = container.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const thumbnailUrl = img.dataset.src;
                    const fallbackUrl = img.dataset.fallback || '/static/placeholder-video.png';
                    
                    this.loadThumbnailWithFallback(img, thumbnailUrl, fallbackUrl);
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
    
    static refreshThumbnailDisplay(containerId, type = 'video') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const images = container.querySelectorAll('img');
        const placeholderUrl = type === 'artist' ? '/static/placeholder-artist.png' : '/static/placeholder-video.png';
        
        images.forEach(img => {
            const originalSrc = img.dataset.originalSrc || img.src;
            if (originalSrc && !originalSrc.includes('placeholder')) {
                this.loadThumbnailWithFallback(img, originalSrc, placeholderUrl);
            }
        });
    }
    
    static async bulkDownloadThumbnails(videoIds, progressCallback) {
        const results = [];
        const total = videoIds.length;
        
        for (let i = 0; i < total; i++) {
            const videoId = videoIds[i];
            try {
                const result = await this.downloadVideoThumbnail(videoId);
                results.push({ videoId, success: true, result });
                
                if (progressCallback) {
                    progressCallback(i + 1, total, videoId, true);
                }
            } catch (error) {
                results.push({ videoId, success: false, error: error.message });
                
                if (progressCallback) {
                    progressCallback(i + 1, total, videoId, false, error.message);
                }
            }
            
            // Small delay to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        const successCount = results.filter(r => r.success).length;
        const messageType = successCount === total ? 'success' : 'warning';
        showMessage(`Downloaded ${successCount} of ${total} thumbnails`, messageType);
        
        return results;
    }
}

// Authentication Management
class AuthManager {
    static async checkAuthStatus() {
        try {
            // Check if authentication is required
            const settings = await apiRequest('/api/settings/');
            const requireAuth = settings.require_authentication?.value === 'true';
            
            if (requireAuth) {
                // Show user menu and get user info
                const userMenu = document.getElementById('userMenu');
                const usernameSpan = document.getElementById('username');
                
                if (userMenu) {
                    userMenu.style.display = 'block';
                    if (usernameSpan) {
                        usernameSpan.textContent = 'admin'; // For now, hardcoded
                    }
                }
            } else {
                // Hide user menu when auth is disabled
                const userMenu = document.getElementById('userMenu');
                if (userMenu) {
                    userMenu.style.display = 'none';
                }
            }
            
            return requireAuth;
        } catch (error) {
            console.error('Failed to check auth status:', error);
            return false;
        }
    }
    
    static async logout() {
        try {
            const response = await fetch('/auth/logout', { method: 'POST' });
            if (response.ok) {
                showSuccess('Logged out successfully');
                // Reload page to trigger redirect to login if auth is still required
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showError('Logout failed');
            }
        } catch (error) {
            console.error('Logout error:', error);
            showError('Logout failed');
        }
    }
}

// User Management Functions
function logout() {
    if (confirm('Are you sure you want to log out?')) {
        AuthManager.logout();
    }
}

function showUserProfile() {
    // Create user profile modal
    const modalHtml = `
        <div class="modal" id="userProfileModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>👤 User Profile</h2>
                    <button class="modal-close" onclick="closeModal('userProfileModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="profile-section">
                        <h3>Account Information</h3>
                        <div class="form-group">
                            <label>Username:</label>
                            <p><strong>admin</strong></p>
                        </div>
                        <div class="form-group">
                            <label>Role:</label>
                            <p><strong>Administrator</strong></p>
                        </div>
                        <div class="form-group">
                            <label>Last Login:</label>
                            <p id="lastLogin">Just now</p>
                        </div>
                    </div>
                    <div class="profile-actions">
                        <button class="btn btn-primary" onclick="showChangePassword()">Change Password</button>
                        <button class="btn btn-secondary" onclick="closeModal('userProfileModal')">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existing = document.getElementById('userProfileModal');
    if (existing) existing.remove();
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    document.getElementById('userProfileModal').style.display = 'block';
}

function showChangePassword() {
    // Create change password modal
    const modalHtml = `
        <div class="modal" id="changePasswordModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>🔑 Change Password</h2>
                    <button class="modal-close" onclick="closeModal('changePasswordModal')">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="changePasswordForm" onsubmit="handleChangePassword(event)">
                        <div class="form-group">
                            <label for="currentPassword">Current Password:</label>
                            <input type="password" id="currentPassword" name="currentPassword" required>
                        </div>
                        <div class="form-group">
                            <label for="newPassword">New Password:</label>
                            <input type="password" id="newPassword" name="newPassword" required minlength="8">
                            <small class="help-text">Password must be at least 8 characters long</small>
                        </div>
                        <div class="form-group">
                            <label for="confirmPassword">Confirm New Password:</label>
                            <input type="password" id="confirmPassword" name="confirmPassword" required>
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">Change Password</button>
                            <button type="button" class="btn btn-secondary" onclick="closeModal('changePasswordModal')">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existing = document.getElementById('changePasswordModal');
    if (existing) existing.remove();
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    document.getElementById('changePasswordModal').style.display = 'block';
}

async function handleChangePassword(event) {
    event.preventDefault();
    
    const form = event.target;
    const currentPassword = form.currentPassword.value;
    const newPassword = form.newPassword.value;
    const confirmPassword = form.confirmPassword.value;
    
    // Validate passwords match
    if (newPassword !== confirmPassword) {
        showError('New passwords do not match');
        return;
    }
    
    // Validate password strength
    if (newPassword.length < 8) {
        showError('Password must be at least 8 characters long');
        return;
    }
    
    try {
        const response = await apiRequest('/auth/change-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        if (response.success) {
            showSuccess('Password changed successfully');
            closeModal('changePasswordModal');
        } else {
            showWarning(response.message || 'Password change functionality is not yet fully implemented');
            closeModal('changePasswordModal');
        }
    } catch (error) {
        console.error('Password change error:', error);
        const errorMessage = error.message || 'Failed to change password';
        showError(errorMessage);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        setTimeout(() => modal.remove(), 300);
    }
}

// User Management Functions for Settings Page
function resetFailedAttempts() {
    showWarning('Failed attempt reset functionality will be implemented in the next update');
    // TODO: Implement actual API call to reset failed attempts
}

function forceLogoutAllSessions() {
    if (confirm('Are you sure you want to force logout all active sessions? This will require all users to log in again.')) {
        showWarning('Force logout functionality will be implemented in the next update');
        // TODO: Implement actual API call to invalidate all sessions
    }
}

// Settings page authentication management (simplified - no complex user management)
function updateUserManagementSection() {
    // This function is kept for compatibility but does nothing since we removed complex user management
    // The user credentials section is handled by updateUserCredentialsSection()
}

// User credentials section management
function updateUserCredentialsSection() {
    const userCredentialsSection = document.getElementById('userCredentialsSection');
    if (!userCredentialsSection) return;
    
    // Check if authentication is enabled
    const requireAuthElement = document.getElementById('require_authentication');
    if (requireAuthElement && requireAuthElement.value === 'true') {
        userCredentialsSection.style.display = 'block';
        loadCurrentCredentials();
    } else {
        userCredentialsSection.style.display = 'none';
    }
}

// Load current credentials for display
async function loadCurrentCredentials() {
    try {
        const response = await apiRequest('/auth/credentials');
        const usernameField = document.getElementById('auth_username');
        if (usernameField && response.username) {
            usernameField.value = response.username;
        }
    } catch (error) {
        console.log('Could not load current credentials:', error);
    }
}

// Update user credentials
async function updateCredentials() {
    const username = document.getElementById('auth_username').value.trim();
    const password = document.getElementById('auth_password').value;
    const confirmPassword = document.getElementById('auth_password_confirm').value;
    
    // Validation
    if (!username) {
        showError('Username is required');
        return;
    }
    
    if (username.length < 3) {
        showError('Username must be at least 3 characters long');
        return;
    }
    
    if (!password) {
        showError('Password is required');
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters long');
        return;
    }
    
    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }
    
    try {
        showLoading('Updating credentials...');
        
        await apiRequest('/auth/credentials', {
            method: 'POST',
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        showSuccess('Credentials updated successfully');
        
        // Clear password fields
        document.getElementById('auth_password').value = '';
        document.getElementById('auth_password_confirm').value = '';
        
    } catch (error) {
        showError('Failed to update credentials: ' + error.message);
    }
}

// Reset credentials to default
async function resetCredentials() {
    if (!confirm('Are you sure you want to reset credentials to default values?')) {
        return;
    }
    
    try {
        showLoading('Resetting credentials...');
        
        await apiRequest('/auth/credentials/reset', {
            method: 'POST'
        });
        
        showSuccess('Credentials reset to default (admin/mvidarr)');
        loadCurrentCredentials();
        
        // Clear password fields
        document.getElementById('auth_password').value = '';
        document.getElementById('auth_password_confirm').value = '';
        
    } catch (error) {
        showError('Failed to reset credentials: ' + error.message);
    }
}

// Initialize authentication status on page load
document.addEventListener('DOMContentLoaded', function() {
    AuthManager.checkAuthStatus();
    
    // Update user management section visibility on settings page
    if (window.location.pathname.includes('/settings')) {
        // Watch for authentication setting changes
        const requireAuthElement = document.getElementById('require_authentication');
        if (requireAuthElement) {
            requireAuthElement.addEventListener('change', function() {
                updateUserManagementSection();
                updateUserCredentialsSection();
            });
            updateUserManagementSection(); // Initial check
            updateUserCredentialsSection(); // Initial check for credentials section
        }
    }
});

// Export for use in other scripts
window.MVidarr = {
    showMessage,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading,
    showElementLoading,
    showGlobalLoading,
    apiRequest,
    SettingsManager,
    HealthMonitor,
    validateForm,
    formatFileSize,
    formatDuration,
    formatDate,
    ThumbnailManager,
    AuthManager
};