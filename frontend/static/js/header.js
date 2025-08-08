/**
 * Header Management - Optimized Performance
 * Handles dynamic header positioning and user interactions
 */

class HeaderManager {
    constructor() {
        this.header = document.getElementById('appHeader');
        this.sidebar = document.getElementById('sidebar');
        this.resizeTimeout = null;
        
        this.init();
    }
    
    init() {
        if (!this.header || !this.sidebar) return;
        
        // Initialize header positioning
        this.updateHeaderWidth();
        
        // Efficient event listeners
        this.setupEventListeners();
        this.setupSidebarObserver();
        
        // Update header user section
        this.updateHeaderUserSection();
    }
    
    setupEventListeners() {
        // Debounced resize handler
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => this.updateHeaderWidth(), 100);
        });
        
        // Sidebar toggle listener
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                // Small delay to allow animation to start
                requestAnimationFrame(() => {
                    setTimeout(() => this.updateHeaderWidth(), 50);
                });
            });
        }
    }
    
    setupSidebarObserver() {
        // Use MutationObserver for sidebar class changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    this.updateHeaderWidth();
                }
            });
        });
        
        observer.observe(this.sidebar, { 
            attributes: true, 
            attributeFilter: ['class']
        });
    }
    
    updateHeaderWidth() {
        if (!this.sidebar || !this.header) return;
        
        const isCollapsed = this.sidebar.classList.contains('collapsed');
        const sidebarWidth = isCollapsed ? '60px' : '250px';
        
        // Update CSS custom property for smooth transitions
        document.documentElement.style.setProperty('--sidebar-width', sidebarWidth);
        
        // Apply immediate positioning for desktop
        if (window.innerWidth > 1024) {
            this.header.style.left = sidebarWidth;
        } else {
            this.header.style.left = '0';
        }
    }
    
    updateHeaderUserSection() {
        const headerUserSection = document.getElementById('headerUserSection');
        const headerUsername = document.getElementById('headerUsername');
        const sidebarUserMenu = document.getElementById('userMenu');
        const sidebarUsername = document.getElementById('username');
        
        if (!headerUserSection) return;
        
        // Sync with sidebar user menu
        if (sidebarUserMenu && sidebarUsername) {
            const isVisible = sidebarUserMenu.style.display !== 'none';
            headerUserSection.style.display = isVisible ? 'flex' : 'none';
            
            if (headerUsername && isVisible) {
                headerUsername.textContent = sidebarUsername.textContent || 'User';
            }
        }
    }
    
    // Public methods for external integration
    syncUserSection() {
        this.updateHeaderUserSection();
    }
    
    refresh() {
        this.updateHeaderWidth();
        this.updateHeaderUserSection();
    }
}

// Initialize header manager
let headerManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        headerManager = new HeaderManager();
        window.headerManager = headerManager;
    });
} else {
    headerManager = new HeaderManager();
    window.headerManager = headerManager;
}

// Expose methods for backward compatibility
window.updateHeaderUserSection = () => headerManager?.syncUserSection();
window.updateHeaderWidth = () => headerManager?.refresh();