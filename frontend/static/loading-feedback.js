/**
 * MVidarr Unified Loading States & Feedback System
 * Comprehensive loading and user feedback management
 */

class LoadingManager {
    constructor() {
        this.activeLoadings = new Set();
        this.toastContainer = null;
        this.connectionStatus = null;
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        this.createToastContainer();
        // Set up connection monitoring
        this.setupConnectionMonitoring();
        // Set up global error handling
        this.setupGlobalErrorHandling();
    }

    createToastContainer() {
        if (!this.toastContainer) {
            this.toastContainer = document.createElement('div');
            this.toastContainer.className = 'toast-container';
            this.toastContainer.setAttribute('aria-live', 'polite');
            this.toastContainer.setAttribute('aria-label', 'Notifications');
            document.body.appendChild(this.toastContainer);
        }
    }

    /**
     * Show loading spinner on element
     * @param {string|Element} target - CSS selector or DOM element
     * @param {Object} options - Loading options
     */
    showLoading(target, options = {}) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        const {
            type = 'spinner', // 'spinner', 'skeleton', 'overlay', 'button'
            size = 'default', // 'small', 'default', 'large'
            message = 'Loading...',
            overlay = false
        } = options;

        const loadingId = `loading_${Date.now()}_${Math.random()}`;
        this.activeLoadings.add(loadingId);

        element.setAttribute('aria-busy', 'true');
        element.setAttribute('data-loading-id', loadingId);

        switch (type) {
            case 'spinner':
                this.showSpinner(element, size, message);
                break;
            case 'skeleton':
                this.showSkeleton(element);
                break;
            case 'overlay':
                this.showOverlay(element, message);
                break;
            case 'button':
                this.showButtonLoading(element);
                break;
            case 'progress':
                this.showProgress(element, message);
                break;
            default:
                this.showSpinner(element, size, message);
        }

        return loadingId;
    }

    /**
     * Hide loading state
     * @param {string|Element} target - CSS selector, DOM element, or loading ID
     */
    hideLoading(target) {
        let element;
        
        if (typeof target === 'string' && target.startsWith('loading_')) {
            // Target is a loading ID
            element = document.querySelector(`[data-loading-id="${target}"]`);
            this.activeLoadings.delete(target);
        } else {
            // Target is selector or element
            element = typeof target === 'string' ? document.querySelector(target) : target;
            if (element) {
                const loadingId = element.getAttribute('data-loading-id');
                if (loadingId) {
                    this.activeLoadings.delete(loadingId);
                }
            }
        }

        if (!element) return;

        element.removeAttribute('aria-busy');
        element.removeAttribute('data-loading-id');
        element.classList.remove('loading');

        // Remove loading elements
        const loadingElements = element.querySelectorAll('.loading-spinner, .loading-overlay, .skeleton, .progress-loading');
        loadingElements.forEach(el => el.remove());

        // Restore button text if it was a button
        if (element.hasAttribute('data-original-text')) {
            element.textContent = element.getAttribute('data-original-text');
            element.removeAttribute('data-original-text');
        }
    }

    showSpinner(element, size, message) {
        const spinner = document.createElement('div');
        spinner.className = `loading-spinner ${size}`;
        spinner.setAttribute('aria-label', message);

        if (element.tagName === 'BUTTON') {
            element.classList.add('loading');
            element.appendChild(spinner);
        } else {
            const container = document.createElement('div');
            container.className = 'loading-container';
            container.appendChild(spinner);
            
            if (message) {
                const text = document.createElement('span');
                text.textContent = message;
                text.className = 'loading-text';
                container.appendChild(text);
            }
            
            element.appendChild(container);
        }
    }

    showSkeleton(element) {
        const existingContent = element.innerHTML;
        element.setAttribute('data-original-content', existingContent);
        
        // Create skeleton based on content type
        let skeletonHTML = '';
        
        if (element.querySelector('.card')) {
            skeletonHTML = '<div class="skeleton skeleton-card"></div>';
        } else if (element.tagName === 'IMG') {
            skeletonHTML = '<div class="skeleton skeleton-thumbnail"></div>';
        } else {
            skeletonHTML = `
                <div class="skeleton skeleton-text large"></div>
                <div class="skeleton skeleton-text medium"></div>
                <div class="skeleton skeleton-text short"></div>
            `;
        }
        
        element.innerHTML = skeletonHTML;
    }

    showOverlay(element, message) {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay active';
        
        const content = document.createElement('div');
        content.style.textAlign = 'center';
        
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner large';
        
        const text = document.createElement('div');
        text.textContent = message;
        text.style.marginTop = '1rem';
        text.style.color = 'var(--text-secondary)';
        
        content.appendChild(spinner);
        content.appendChild(text);
        overlay.appendChild(content);
        
        element.style.position = 'relative';
        element.appendChild(overlay);
    }

    showButtonLoading(element) {
        if (element.hasAttribute('data-original-text')) return; // Already loading
        
        element.setAttribute('data-original-text', element.textContent);
        element.classList.add('loading');
        element.disabled = true;
        element.setAttribute('aria-disabled', 'true');
    }

    showProgress(element, message) {
        const container = document.createElement('div');
        container.className = 'loading-container';
        
        if (message) {
            const text = document.createElement('div');
            text.textContent = message;
            text.style.marginBottom = '1rem';
            container.appendChild(text);
        }
        
        const progress = document.createElement('div');
        progress.className = 'progress-loading';
        progress.setAttribute('role', 'progressbar');
        progress.setAttribute('aria-label', message || 'Loading');
        
        container.appendChild(progress);
        element.appendChild(container);
    }

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {Object} options - Toast options
     */
    showToast(message, options = {}) {
        const {
            type = 'info', // 'success', 'error', 'warning', 'info'
            title = null,
            duration = 5000,
            closable = true,
            persistent = false
        } = options;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.setAttribute('role', type === 'error' ? 'alert' : 'status');

        const header = document.createElement('div');
        header.className = 'toast-header';

        if (title) {
            const titleElement = document.createElement('div');
            titleElement.className = 'toast-title';
            titleElement.textContent = title;
            header.appendChild(titleElement);
        }

        if (closable) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'toast-close';
            closeBtn.innerHTML = '×';
            closeBtn.setAttribute('aria-label', 'Close notification');
            closeBtn.onclick = () => this.hideToast(toast);
            header.appendChild(closeBtn);
        }

        const body = document.createElement('div');
        body.className = 'toast-body';
        body.textContent = message;

        if (title || closable) {
            toast.appendChild(header);
        }
        toast.appendChild(body);

        this.toastContainer.appendChild(toast);

        // Trigger show animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto-hide after duration (unless persistent)
        if (!persistent && duration > 0) {
            setTimeout(() => {
                this.hideToast(toast);
            }, duration);
        }

        return toast;
    }

    hideToast(toast) {
        toast.classList.remove('show');
        toast.classList.add('hide');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    /**
     * Show different types of toast messages
     */
    showSuccess(message, options = {}) {
        return this.showToast(message, { ...options, type: 'success', title: options.title || 'Success' });
    }

    showError(message, options = {}) {
        return this.showToast(message, { ...options, type: 'error', title: options.title || 'Error', duration: 8000 });
    }

    showWarning(message, options = {}) {
        return this.showToast(message, { ...options, type: 'warning', title: options.title || 'Warning' });
    }

    showInfo(message, options = {}) {
        return this.showToast(message, { ...options, type: 'info', title: options.title || 'Info' });
    }

    /**
     * Show inline state messages
     */
    showStateMessage(target, message, type = 'info') {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        // Remove existing state messages
        const existingMessages = element.querySelectorAll('.state-message');
        existingMessages.forEach(msg => msg.remove());

        const stateMessage = document.createElement('div');
        stateMessage.className = `state-message ${type}`;
        stateMessage.textContent = message;
        stateMessage.setAttribute('role', type === 'error' ? 'alert' : 'status');

        element.appendChild(stateMessage);

        // Auto-hide after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                if (stateMessage.parentNode) {
                    stateMessage.remove();
                }
            }, 5000);
        }

        return stateMessage;
    }

    /**
     * Show empty state
     */
    showEmptyState(target, options = {}) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        const {
            icon = '📭',
            title = 'No items found',
            description = 'There are no items to display at the moment.',
            actionText = null,
            actionHandler = null
        } = options;

        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';

        const iconElement = document.createElement('div');
        iconElement.className = 'empty-state-icon';
        iconElement.textContent = icon;

        const titleElement = document.createElement('div');
        titleElement.className = 'empty-state-title';
        titleElement.textContent = title;

        const descElement = document.createElement('div');
        descElement.className = 'empty-state-description';
        descElement.textContent = description;

        emptyState.appendChild(iconElement);
        emptyState.appendChild(titleElement);
        emptyState.appendChild(descElement);

        if (actionText && actionHandler) {
            const actionBtn = document.createElement('button');
            actionBtn.className = 'btn btn-primary';
            actionBtn.textContent = actionText;
            actionBtn.onclick = actionHandler;
            emptyState.appendChild(actionBtn);
        }

        element.innerHTML = '';
        element.appendChild(emptyState);
    }

    /**
     * Connection status monitoring
     */
    setupConnectionMonitoring() {
        if (typeof navigator !== 'undefined' && 'onLine' in navigator) {
            this.updateConnectionStatus(navigator.onLine);

            window.addEventListener('online', () => {
                this.updateConnectionStatus(true);
                this.showSuccess('Connection restored');
            });

            window.addEventListener('offline', () => {
                this.updateConnectionStatus(false);
                this.showWarning('Connection lost', { persistent: true });
            });
        }
    }

    updateConnectionStatus(isOnline) {
        if (!this.connectionStatus) {
            this.connectionStatus = document.createElement('div');
            this.connectionStatus.className = 'connection-status';
            document.body.appendChild(this.connectionStatus);
        }

        this.connectionStatus.textContent = isOnline ? 'Online' : 'Offline';
        this.connectionStatus.className = `connection-status ${isOnline ? 'online' : 'offline'}`;
        
        // Show/hide based on connection status
        if (!isOnline) {
            this.connectionStatus.style.display = 'block';
        } else {
            setTimeout(() => {
                this.connectionStatus.style.display = 'none';
            }, 2000);
        }
    }

    /**
     * Global error handling
     */
    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('Global error caught:', event.error);
            this.showError('An unexpected error occurred. Please try again.');
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showError('A network or processing error occurred. Please check your connection.');
        });
    }

    /**
     * Form validation helpers
     */
    setFieldState(fieldElement, state, message) {
        const field = fieldElement.closest('.form-field') || fieldElement.parentElement;
        
        // Remove existing states
        field.classList.remove('success', 'error');
        const existingMessages = field.querySelectorAll('.form-error-message, .form-success-message');
        existingMessages.forEach(msg => msg.remove());

        if (state && message) {
            field.classList.add(state);
            
            const messageElement = document.createElement('div');
            messageElement.className = `form-${state}-message`;
            messageElement.textContent = message;
            messageElement.setAttribute('role', state === 'error' ? 'alert' : 'status');
            
            field.appendChild(messageElement);
        }
    }

    /**
     * Utility methods
     */
    hideAllLoadings() {
        this.activeLoadings.forEach(loadingId => {
            const element = document.querySelector(`[data-loading-id="${loadingId}"]`);
            if (element) {
                this.hideLoading(element);
            }
        });
        this.activeLoadings.clear();
    }

    hideAllToasts() {
        const toasts = this.toastContainer.querySelectorAll('.toast');
        toasts.forEach(toast => this.hideToast(toast));
    }

    isLoading(target) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        return element && element.getAttribute('aria-busy') === 'true';
    }
}

// Create global instance
window.LoadingManager = new LoadingManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingManager;
}