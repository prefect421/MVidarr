/**
 * Enhanced Video Management Workflows
 * Improved user experience for video operations
 */

class VideoManagementUI {
    constructor() {
        this.selectedVideos = new Set();
        this.bulkActionsVisible = false;
        this.currentFilters = {};
        this.sortOrder = { field: 'created_at', direction: 'desc' };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.enhanceVideoGrid();
        this.setupBulkActions();
        this.setupSmartFilters();
        this.setupQuickActions();
    }
    
    // ========================================
    // VIDEO GRID ENHANCEMENTS
    // ========================================
    
    enhanceVideoGrid() {
        const videoGrid = document.querySelector('.video-grid, .videos-grid');
        if (!videoGrid) return;
        
        // Add keyboard navigation
        videoGrid.setAttribute('role', 'grid');
        videoGrid.setAttribute('aria-label', 'Video library');
        
        // Enhance video cards
        this.enhanceVideoCards();
        
        // Add infinite scroll
        this.setupInfiniteScroll();
        
        // Add drag and drop for reordering
        this.setupDragAndDrop();
    }
    
    enhanceVideoCards() {
        document.querySelectorAll('.video-card:not(.enhanced)').forEach(card => {
            card.classList.add('enhanced');
            card.setAttribute('role', 'gridcell');
            card.setAttribute('tabindex', '0');
            
            // Add hover effects
            this.addHoverEffects(card);
            
            // Add quick action overlay
            this.addQuickActionOverlay(card);
            
            // Add contextual information
            this.addContextualInfo(card);
            
            // Add keyboard support
            this.addCardKeyboardSupport(card);
        });
    }
    
    addHoverEffects(card) {
        const overlay = document.createElement('div');
        overlay.className = 'video-card-overlay';
        
        Object.assign(overlay.style, {
            position: 'absolute',
            top: '0',
            left: '0',
            right: '0',
            bottom: '0',
            background: 'linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.8) 100%)',
            opacity: '0',
            transition: 'opacity 0.3s ease',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            padding: 'var(--space-4)',
            pointerEvents: 'none'
        });
        
        card.style.position = 'relative';
        card.appendChild(overlay);
        
        card.addEventListener('mouseenter', () => {
            overlay.style.opacity = '1';
            overlay.style.pointerEvents = 'auto';
        });
        
        card.addEventListener('mouseleave', () => {
            overlay.style.opacity = '0';
            overlay.style.pointerEvents = 'none';
        });
    }
    
    addQuickActionOverlay(card) {
        const overlay = card.querySelector('.video-card-overlay');
        if (!overlay) return;
        
        const videoId = this.getVideoIdFromCard(card);
        const videoStatus = this.getVideoStatusFromCard(card);
        
        const quickActions = document.createElement('div');
        quickActions.className = 'quick-actions';
        quickActions.style.display = 'flex';
        quickActions.style.gap = 'var(--space-2)';
        quickActions.style.marginTop = 'var(--space-3)';
        
        // Status-based actions
        const actions = this.getQuickActionsForStatus(videoStatus);
        
        actions.forEach(action => {
            const button = document.createElement('button');
            button.className = `btn btn-sm ${action.type}`;
            button.innerHTML = `<iconify-icon icon="${action.icon}"></iconify-icon> ${action.label}`;
            button.setAttribute('aria-label', action.ariaLabel || action.label);
            button.onclick = () => this.executeQuickAction(action.handler, videoId, card);
            quickActions.appendChild(button);
        });
        
        overlay.appendChild(quickActions);
    }
    
    getQuickActionsForStatus(status) {
        const baseActions = [
            {
                icon: 'tabler:eye',
                label: 'View',
                type: 'btn-ghost',
                handler: 'viewVideo'
            },
            {
                icon: 'tabler:edit',
                label: 'Edit',
                type: 'btn-ghost',
                handler: 'editVideo'
            }
        ];
        
        const statusActions = {
            WANTED: [
                {
                    icon: 'tabler:download',
                    label: 'Download',
                    type: 'btn-primary',
                    handler: 'downloadVideo'
                },
                {
                    icon: 'tabler:eye-off',
                    label: 'Ignore',
                    type: 'btn-secondary',
                    handler: 'ignoreVideo'
                }
            ],
            DOWNLOADED: [
                {
                    icon: 'tabler:play',
                    label: 'Play',
                    type: 'btn-success',
                    handler: 'playVideo'
                },
                {
                    icon: 'tabler:download',
                    label: 'Re-download',
                    type: 'btn-secondary',
                    handler: 'redownloadVideo'
                }
            ],
            FAILED: [
                {
                    icon: 'tabler:refresh',
                    label: 'Retry',
                    type: 'btn-warning',
                    handler: 'retryDownload'
                },
                {
                    icon: 'tabler:eye-off',
                    label: 'Ignore',
                    type: 'btn-secondary',
                    handler: 'ignoreVideo'
                }
            ],
            IGNORED: [
                {
                    icon: 'tabler:heart',
                    label: 'Want',
                    type: 'btn-primary',
                    handler: 'wantVideo'
                }
            ]
        };
        
        return [...baseActions, ...(statusActions[status] || [])];
    }
    
    addContextualInfo(card) {
        const videoId = this.getVideoIdFromCard(card);
        const info = document.createElement('div');
        info.className = 'video-contextual-info';
        
        Object.assign(info.style, {
            position: 'absolute',
            top: 'var(--space-2)',
            right: 'var(--space-2)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-1)',
            alignItems: 'flex-end'
        });
        
        // Add quality badge
        const quality = this.getVideoQuality(card);
        if (quality) {
            const qualityBadge = this.createBadge(quality, 'quality');
            info.appendChild(qualityBadge);
        }
        
        // Add duration badge
        const duration = this.getVideoDuration(card);
        if (duration) {
            const durationBadge = this.createBadge(this.formatDuration(duration), 'duration');
            info.appendChild(durationBadge);
        }
        
        // Add status badge
        const status = this.getVideoStatusFromCard(card);
        const statusBadge = this.createBadge(status, 'status');
        info.appendChild(statusBadge);
        
        card.appendChild(info);
    }
    
    createBadge(text, type) {
        const badge = document.createElement('span');
        badge.className = `badge badge-${type}`;
        badge.textContent = text;
        
        const typeStyles = {
            quality: { background: 'var(--status-info)', color: 'white' },
            duration: { background: 'var(--bg-secondary)', color: 'var(--text-secondary)' },
            status: { 
                background: this.getStatusColor(text),
                color: 'white'
            }
        };
        
        Object.assign(badge.style, {
            padding: 'var(--space-1) var(--space-2)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            ...typeStyles[type]
        });
        
        return badge;
    }
    
    getStatusColor(status) {
        const colors = {
            WANTED: 'var(--status-info)',
            DOWNLOADING: 'var(--status-warning)',
            DOWNLOADED: 'var(--status-success)',
            FAILED: 'var(--status-error)',
            IGNORED: 'var(--status-neutral)'
        };
        
        return colors[status] || 'var(--status-neutral)';
    }
    
    addCardKeyboardSupport(card) {
        card.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    this.selectVideo(this.getVideoIdFromCard(card), !card.classList.contains('selected'));
                    break;
                case 'Delete':
                    e.preventDefault();
                    this.deleteVideo(this.getVideoIdFromCard(card));
                    break;
                case 'd':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.downloadVideo(this.getVideoIdFromCard(card));
                    }
                    break;
            }
        });
    }
    
    // ========================================
    // BULK ACTIONS ENHANCEMENT
    // ========================================
    
    setupBulkActions() {
        const bulkPanel = this.createEnhancedBulkPanel();
        this.insertBulkPanel(bulkPanel);
        
        // Update bulk actions when selection changes
        document.addEventListener('videoSelectionChanged', () => {
            this.updateBulkActions();
        });
    }
    
    createEnhancedBulkPanel() {
        const panel = document.createElement('div');
        panel.id = 'enhanced-bulk-panel';
        panel.className = 'enhanced-bulk-panel';
        
        Object.assign(panel.style, {
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-4)',
            marginBottom: 'var(--space-4)',
            display: 'none',
            opacity: '0',
            transform: 'translateY(-10px)',
            transition: 'all 0.3s ease'
        });
        
        panel.innerHTML = `
            <div class="bulk-header">
                <h3>Bulk Actions</h3>
                <span class="selected-count">0 videos selected</span>
                <button class="btn btn-ghost btn-sm" onclick="videoManagementUI.closeBulkPanel()">
                    <iconify-icon icon="tabler:x"></iconify-icon>
                </button>
            </div>
            <div class="bulk-content">
                <div class="action-grid">
                    <button class="action-card" data-action="download" onclick="videoManagementUI.bulkDownload()">
                        <iconify-icon icon="tabler:download"></iconify-icon>
                        <span>Download Selected</span>
                    </button>
                    <button class="action-card" data-action="mark-wanted" onclick="videoManagementUI.bulkMarkWanted()">
                        <iconify-icon icon="tabler:heart"></iconify-icon>
                        <span>Mark as Wanted</span>
                    </button>
                    <button class="action-card" data-action="mark-ignored" onclick="videoManagementUI.bulkMarkIgnored()">
                        <iconify-icon icon="tabler:eye-off"></iconify-icon>
                        <span>Mark as Ignored</span>
                    </button>
                    <button class="action-card danger" data-action="delete" onclick="videoManagementUI.bulkDelete()">
                        <iconify-icon icon="tabler:trash"></iconify-icon>
                        <span>Delete Selected</span>
                    </button>
                </div>
                <div class="bulk-metadata">
                    <h4>Bulk Edit Metadata</h4>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Artist</label>
                            <input type="text" id="bulkArtist" placeholder="Change artist for all selected">
                        </div>
                        <div class="form-group">
                            <label>Year</label>
                            <input type="number" id="bulkYear" placeholder="Change year for all selected">
                        </div>
                    </div>
                    <button class="btn btn-primary" onclick="videoManagementUI.applyBulkMetadata()">
                        Apply Changes
                    </button>
                </div>
            </div>
        `;
        
        // Add CSS for the panel
        this.addBulkPanelStyles();
        
        return panel;
    }
    
    addBulkPanelStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            .enhanced-bulk-panel.visible {
                display: block !important;
                opacity: 1 !important;
                transform: translateY(0) !important;
            }
            
            .bulk-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: var(--space-4);
                padding-bottom: var(--space-3);
                border-bottom: 1px solid var(--border-primary);
            }
            
            .bulk-header h3 {
                margin: 0;
                color: var(--text-primary);
            }
            
            .selected-count {
                color: var(--text-muted);
                font-size: var(--font-size-sm);
            }
            
            .action-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: var(--space-3);
                margin-bottom: var(--space-6);
            }
            
            .action-card {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: var(--space-2);
                padding: var(--space-4);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-lg);
                background: var(--bg-primary);
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .action-card:hover {
                transform: translateY(-2px);
                border-color: var(--status-info);
                box-shadow: var(--shadow-md);
            }
            
            .action-card.danger:hover {
                border-color: var(--status-error);
            }
            
            .action-card iconify-icon {
                font-size: 1.5rem;
                color: var(--text-primary);
            }
            
            .action-card span {
                font-size: var(--font-size-sm);
                font-weight: 500;
                text-align: center;
            }
            
            .bulk-metadata {
                padding-top: var(--space-4);
                border-top: 1px solid var(--border-primary);
            }
            
            .bulk-metadata h4 {
                margin: 0 0 var(--space-3) 0;
                color: var(--text-primary);
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: var(--space-4);
                margin-bottom: var(--space-4);
            }
            
            @media (max-width: 640px) {
                .action-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .form-row {
                    grid-template-columns: 1fr;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }
    
    insertBulkPanel(panel) {
        const videosActions = document.querySelector('.videos-actions');
        if (videosActions && videosActions.parentNode) {
            videosActions.parentNode.insertBefore(panel, videosActions.nextSibling);
        }
    }
    
    toggleBulkPanel() {
        const panel = document.getElementById('enhanced-bulk-panel');
        if (!panel) return;
        
        if (this.bulkActionsVisible) {
            this.closeBulkPanel();
        } else {
            this.openBulkPanel();
        }
    }
    
    openBulkPanel() {
        const panel = document.getElementById('enhanced-bulk-panel');
        if (!panel) return;
        
        panel.style.display = 'block';
        // Force reflow
        panel.offsetHeight;
        panel.classList.add('visible');
        
        this.bulkActionsVisible = true;
        this.updateBulkActions();
    }
    
    closeBulkPanel() {
        const panel = document.getElementById('enhanced-bulk-panel');
        if (!panel) return;
        
        panel.classList.remove('visible');
        
        setTimeout(() => {
            panel.style.display = 'none';
        }, 300);
        
        this.bulkActionsVisible = false;
    }
    
    updateBulkActions() {
        const panel = document.getElementById('enhanced-bulk-panel');
        if (!panel) return;
        
        const selectedCount = this.selectedVideos.size;
        const countElement = panel.querySelector('.selected-count');
        
        if (countElement) {
            countElement.textContent = `${selectedCount} video${selectedCount !== 1 ? 's' : ''} selected`;
        }
        
        // Enable/disable actions based on selection
        const actionCards = panel.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            card.disabled = selectedCount === 0;
            card.style.opacity = selectedCount === 0 ? '0.5' : '1';
            card.style.pointerEvents = selectedCount === 0 ? 'none' : 'auto';
        });
        
        // Auto-open panel when videos are selected
        if (selectedCount > 0 && !this.bulkActionsVisible) {
            this.openBulkPanel();
        } else if (selectedCount === 0 && this.bulkActionsVisible) {
            this.closeBulkPanel();
        }
    }
    
    // ========================================
    // BULK ACTIONS HANDLERS
    // ========================================
    
    async bulkDownload() {
        const videoIds = Array.from(this.selectedVideos);
        
        try {
            window.uiEnhancements.info('Download Started', `Downloading ${videoIds.length} videos...`);
            
            const response = await fetch('/api/videos/bulk/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_ids: videoIds })
            });
            
            const result = await response.json();
            
            if (result.success) {
                window.uiEnhancements.success('Download Initiated', `${result.queued_count} videos queued for download`);
                this.clearSelection();
            } else {
                throw new Error(result.error || 'Download failed');
            }
        } catch (error) {
            window.uiEnhancements.error('Download Failed', error.message);
        }
    }
    
    async bulkMarkWanted() {
        await this.bulkUpdateStatus('WANTED', 'wanted');
    }
    
    async bulkMarkIgnored() {
        await this.bulkUpdateStatus('IGNORED', 'ignored');
    }
    
    async bulkUpdateStatus(status, statusLabel) {
        const videoIds = Array.from(this.selectedVideos);
        
        try {
            const response = await fetch('/api/videos/bulk/status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_ids: videoIds, status })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                window.uiEnhancements.success('Status Updated', `${videoIds.length} videos marked as ${statusLabel}`);
                this.clearSelection();
                this.refreshVideoGrid();
            } else {
                throw new Error(result.error || 'Status update failed');
            }
        } catch (error) {
            window.uiEnhancements.error('Status Update Failed', error.message);
        }
    }
    
    async applyBulkMetadata() {
        const videoIds = Array.from(this.selectedVideos);
        const artist = document.getElementById('bulkArtist')?.value.trim();
        const year = document.getElementById('bulkYear')?.value;
        
        const updates = {};
        if (artist) updates.artist_name = artist;
        if (year) updates.year = parseInt(year);
        
        if (Object.keys(updates).length === 0) {
            window.uiEnhancements.warning('No Changes', 'Please specify at least one field to update');
            return;
        }
        
        try {
            const response = await fetch('/api/videos/bulk/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_ids: videoIds, updates })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                window.uiEnhancements.success('Metadata Updated', `Updated ${result.updated_count} videos`);
                this.clearSelection();
                this.refreshVideoGrid();
                
                // Clear form
                if (document.getElementById('bulkArtist')) document.getElementById('bulkArtist').value = '';
                if (document.getElementById('bulkYear')) document.getElementById('bulkYear').value = '';
            } else {
                throw new Error(result.error || 'Metadata update failed');
            }
        } catch (error) {
            window.uiEnhancements.error('Metadata Update Failed', error.message);
        }
    }
    
    bulkDelete() {
        const videoIds = Array.from(this.selectedVideos);
        
        window.uiEnhancements.confirm(
            'Confirm Deletion',
            `Are you sure you want to delete ${videoIds.length} videos? This action cannot be undone.`,
            () => this.executeBulkDelete(videoIds)
        );
    }
    
    async executeBulkDelete(videoIds) {
        try {
            const response = await fetch('/api/videos/bulk/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_ids: videoIds })
            });
            
            const result = await response.json();
            
            if (result.success) {
                window.uiEnhancements.success('Videos Deleted', `${result.deleted_count} videos deleted successfully`);
                this.clearSelection();
                this.refreshVideoGrid();
            } else {
                throw new Error(result.error || 'Deletion failed');
            }
        } catch (error) {
            window.uiEnhancements.error('Deletion Failed', error.message);
        }
    }
    
    // ========================================
    // SELECTION MANAGEMENT
    // ========================================
    
    selectVideo(videoId, selected = true) {
        const card = document.querySelector(`[data-video-id="${videoId}"]`);
        if (!card) return;
        
        if (selected) {
            this.selectedVideos.add(videoId);
            card.classList.add('selected');
        } else {
            this.selectedVideos.delete(videoId);
            card.classList.remove('selected');
        }
        
        this.updateSelectionUI();
        document.dispatchEvent(new CustomEvent('videoSelectionChanged', { 
            detail: { selectedVideos: Array.from(this.selectedVideos) }
        }));
    }
    
    selectAll() {
        const videoCards = document.querySelectorAll('.video-card[data-video-id]');
        videoCards.forEach(card => {
            const videoId = this.getVideoIdFromCard(card);
            this.selectVideo(videoId, true);
        });
    }
    
    clearSelection() {
        const selectedCards = document.querySelectorAll('.video-card.selected');
        selectedCards.forEach(card => {
            card.classList.remove('selected');
        });
        
        this.selectedVideos.clear();
        this.updateSelectionUI();
        document.dispatchEvent(new CustomEvent('videoSelectionChanged', { 
            detail: { selectedVideos: [] }
        }));
    }
    
    updateSelectionUI() {
        const selectAllCheckbox = document.getElementById('selectAllVideos');
        if (selectAllCheckbox) {
            const totalVideos = document.querySelectorAll('.video-card[data-video-id]').length;
            const selectedCount = this.selectedVideos.size;
            
            selectAllCheckbox.checked = selectedCount > 0;
            selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < totalVideos;
        }
        
        const selectedCountElement = document.getElementById('selectedCount');
        if (selectedCountElement) {
            selectedCountElement.textContent = this.selectedVideos.size;
        }
    }
    
    // ========================================
    // QUICK ACTIONS
    // ========================================
    
    async executeQuickAction(action, videoId, card) {
        const loadingOverlay = window.uiEnhancements.showLoadingOverlay(card);
        
        try {
            switch (action) {
                case 'downloadVideo':
                    await this.downloadSingleVideo(videoId);
                    break;
                case 'retryDownload':
                    await this.retryVideoDownload(videoId);
                    break;
                case 'playVideo':
                    await this.playVideo(videoId);
                    break;
                case 'editVideo':
                    this.openVideoEditModal(videoId);
                    break;
                case 'viewVideo':
                    this.viewVideoDetails(videoId);
                    break;
                case 'ignoreVideo':
                    await this.setVideoStatus(videoId, 'IGNORED');
                    break;
                case 'wantVideo':
                    await this.setVideoStatus(videoId, 'WANTED');
                    break;
                case 'deleteVideo':
                    this.confirmDeleteVideo(videoId);
                    break;
                default:
                    console.warn(`Unknown action: ${action}`);
            }
        } catch (error) {
            window.uiEnhancements.error('Action Failed', error.message);
        } finally {
            window.uiEnhancements.hideLoadingOverlay(card);
        }
    }
    
    async downloadSingleVideo(videoId) {
        const response = await fetch('/api/videos/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: videoId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.uiEnhancements.success('Download Started', 'Video queued for download');
            this.updateVideoCardStatus(videoId, 'DOWNLOADING');
        } else {
            throw new Error(result.error || 'Download failed');
        }
    }
    
    async setVideoStatus(videoId, status) {
        const response = await fetch(`/api/videos/${videoId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.uiEnhancements.success('Status Updated', `Video marked as ${status.toLowerCase()}`);
            this.updateVideoCardStatus(videoId, status);
        } else {
            throw new Error(result.error || 'Status update failed');
        }
    }
    
    // ========================================
    // UTILITY METHODS
    // ========================================
    
    setupEventListeners() {
        // Enhanced select all checkbox
        const selectAllCheckbox = document.getElementById('selectAllVideos');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectAll();
                } else {
                    this.clearSelection();
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+A to select all videos
            if ((e.ctrlKey || e.metaKey) && e.key === 'a' && this.isVideoPageActive()) {
                e.preventDefault();
                this.selectAll();
            }
            
            // Escape to clear selection
            if (e.key === 'Escape') {
                this.clearSelection();
            }
            
            // Delete to delete selected videos
            if (e.key === 'Delete' && this.selectedVideos.size > 0) {
                e.preventDefault();
                this.bulkDelete();
            }
        });
    }
    
    getVideoIdFromCard(card) {
        return card.dataset.videoId || card.getAttribute('data-video-id');
    }
    
    getVideoStatusFromCard(card) {
        return card.dataset.status || card.querySelector('.status')?.textContent?.trim();
    }
    
    getVideoQuality(card) {
        return card.dataset.quality || card.querySelector('.quality')?.textContent?.trim();
    }
    
    getVideoDuration(card) {
        return card.dataset.duration || card.querySelector('.duration')?.textContent?.trim();
    }
    
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    updateVideoCardStatus(videoId, newStatus) {
        const card = document.querySelector(`[data-video-id="${videoId}"]`);
        if (card) {
            card.dataset.status = newStatus;
            
            // Update status badge
            const statusBadge = card.querySelector('.badge-status');
            if (statusBadge) {
                statusBadge.textContent = newStatus;
                statusBadge.style.background = this.getStatusColor(newStatus);
            }
            
            // Update quick actions
            const overlay = card.querySelector('.video-card-overlay');
            if (overlay) {
                const quickActions = overlay.querySelector('.quick-actions');
                if (quickActions) {
                    quickActions.remove();
                    this.addQuickActionOverlay(card);
                }
            }
        }
    }
    
    refreshVideoGrid() {
        // Trigger video grid refresh if function exists
        if (typeof loadVideos === 'function') {
            loadVideos();
        } else if (typeof refreshVideos === 'function') {
            refreshVideos();
        }
    }
    
    isVideoPageActive() {
        return window.location.pathname.includes('/videos') || 
               document.querySelector('.video-grid, .videos-grid') !== null;
    }
    
    setupInfiniteScroll() {
        // TODO: Implement infinite scroll for large video collections
        // This would reduce initial load times and improve performance
    }
    
    setupDragAndDrop() {
        // TODO: Implement drag and drop for video reordering/organization
        // This would allow users to organize videos more intuitively
    }
    
    setupSmartFilters() {
        // TODO: Implement smart filters based on user behavior
        // Recent, Frequently Accessed, etc.
    }
    
    setupQuickActions() {
        // TODO: Add floating action button for common actions
        // Download All Wanted, Refresh All, etc.
    }
}

// Initialize enhanced video management
const videoManagementUI = new VideoManagementUI();

// Export for global access
window.videoManagementUI = videoManagementUI;

// Backward compatibility
window.toggleBulkActionsPanel = () => videoManagementUI.toggleBulkPanel();
window.toggleSelectAll = () => {
    const selectAllCheckbox = document.getElementById('selectAllVideos');
    if (selectAllCheckbox.checked) {
        videoManagementUI.selectAll();
    } else {
        videoManagementUI.clearSelection();
    }
};