document.addEventListener('DOMContentLoaded', function() {
    loadVideos();
    loadVideoGenreOptions(); // Load genre filter options
});

// Pagination state
let currentPage = 1;
let pageSize = 50;
let totalVideos = 0;
let totalPages = 1;

function loadVideos(page = 1, size = pageSize, resetPage = false) {
    if (resetPage) {
        currentPage = 1;
        page = 1;
    }
    
    const offset = (page - 1) * size;
    fetch(`/api/videos/?sort=title&order=asc&offset=${offset}&limit=${size}`)
        .then(response => response.json())
        .then(data => {
            const grid = document.getElementById('videos-grid');
            
            // Update pagination state
            currentPage = page;
            pageSize = size;
            totalVideos = data.total || 0;
            totalPages = Math.ceil(totalVideos / pageSize);
            
            if (data.videos && data.videos.length > 0) {
                grid.innerHTML = data.videos.map(video => `
                    <div class="video-card">
                        <div class="video-select">
                            <input type="checkbox" class="video-checkbox" value="${video.id}" onchange="updateSelectedCount()">
                        </div>
                        <div class="video-thumbnail" data-video-id="${video.id}" data-action="play">
                            <img src="/api/videos/${video.id}/thumbnail" 
                                 alt="${video.title}" onerror="this.src='/static/placeholder-video.png'">
                            <div class="play-overlay">
                                <div class="play-button">▶</div>
                            </div>
                        </div>
                        <div class="video-info">
                            <h3>${video.title}</h3>
                            <p>Artist: ${video.artist_name || 'Unknown'}</p>
                            <p>Status: ${video.status}</p>
                            ${video.year ? `<p>Year: ${video.year}</p>` : ''}
                        </div>
                        <div class="video-actions">
                            <button data-video-id="${video.id}" data-action="view" class="btn-icon" title="View Details">
                                <i class="icon-eye"></i>
                            </button>
                            <button data-video-id="${video.id}" data-action="edit" class="btn-icon" title="Edit Video">
                                <i class="icon-edit"></i>
                            </button>
                            <button data-video-id="${video.id}" data-action="refresh-metadata" class="btn-icon" title="Refresh Metadata">
                                <i class="icon-refresh"></i>
                            </button>
                            ${video.status === 'WANTED' ? 
                                `<button data-video-id="${video.id}" data-action="download" class="btn-icon" title="Download Video">
                                    <i class="icon-download"></i>
                                </button>` : 
                                ''}
                            <button data-video-id="${video.id}" data-action="delete" class="btn-icon btn-danger" title="Delete Video">
                                <i class="icon-trash"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
            } else {
                grid.innerHTML = '<p>No videos found. Add some artists to discover videos!</p>';
            }
            
            // Update pagination controls
            updatePaginationControls();
        })
        .catch(error => {
            console.error('Error loading videos:', error);
            document.getElementById('videos-grid').innerHTML = '<p>Error loading videos.</p>';
            // Hide pagination on error
            document.getElementById('topPagination').style.display = 'none';
            document.getElementById('bottomPagination').style.display = 'none';
        });
}

// Add event delegation for video actions
document.addEventListener('click', function(e) {
    // Check if the clicked element or any of its parents have the data attributes
    let element = e.target;
    let videoId = null;
    let action = null;
    
    // Walk up the DOM tree to find data attributes
    while (element && element !== document) {
        videoId = element.getAttribute('data-video-id');
        action = element.getAttribute('data-action');
        
        if (videoId && action) break;
        element = element.parentElement;
    }
    
    if (!videoId || !action) return;
    
    console.log(`Video action triggered: ${action} for video ${videoId}`);
    
    // Find the video data from the most recent loadVideos call
    const videoCards = document.querySelectorAll('.video-card');
    let videoData = null;
    
    // Find the video card containing this element
    let videoCard = e.target.closest('.video-card');
    if (videoCard) {
        const titleElement = videoCard.querySelector('h3');
        const title = titleElement ? titleElement.textContent : '';
        
        // For play action, we need to get video data from API
        if (action === 'play') {
            fetch(`/api/videos/${videoId}`)
                .then(response => response.json())
                .then(video => {
                    playVideo(video.id, video.title, video.local_path, video.video_url);
                })
                .catch(error => {
                    console.error('Error getting video data:', error);
                    // Fallback to basic data
                    playVideo(parseInt(videoId), title, null, null);
                });
        } else if (action === 'view') {
            viewVideo(parseInt(videoId));
        } else if (action === 'edit') {
            editVideo(parseInt(videoId));
        } else if (action === 'refresh-metadata') {
            refreshVideoMetadata(parseInt(videoId));
        } else if (action === 'download') {
            downloadVideo(parseInt(videoId));
        } else if (action === 'delete') {
            deleteVideo(parseInt(videoId));
        }
    }
});

function refreshVideos() {
    loadVideos();
}

// Search functionality
let searchActive = false;

function toggleSearchPanel() {
    const panel = document.getElementById('searchPanel');
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
    } else {
        panel.style.display = 'none';
        if (searchActive) {
            clearSearch();
        }
    }
}

function handleSearchKeyup(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
}

function performSearch() {
    const query = document.getElementById('searchQuery').value.trim();
    const artist = document.getElementById('searchArtist').value.trim();
    const status = document.getElementById('searchStatus').value;
    const year = document.getElementById('searchYear').value;
    const sortBy = document.getElementById('sortBy').value || 'title';
    const sortOrder = document.getElementById('sortOrder').value || 'asc';
    
    // Build search parameters
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (artist) params.append('artist', artist);
    if (status) params.append('status', status);
    if (year) params.append('year', year);
    params.append('sort', sortBy);
    params.append('order', sortOrder);
    
    // Show loading state
    const resultsInfo = document.getElementById('searchResults');
    resultsInfo.textContent = 'Searching...';
    
    // Perform search
    fetch(`/api/videos/search?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError('Search error: ' + data.error);
                return;
            }
            
            searchActive = true;
            displaySearchResults(data);
            updateSearchResultsInfo(data);
        })
        .catch(error => {
            console.error('Search error:', error);
            showError('Error performing search');
            resultsInfo.textContent = '';
        });
}

function displaySearchResults(data) {
    const grid = document.getElementById('videos-grid');
    
    if (data.videos && data.videos.length > 0) {
        grid.innerHTML = data.videos.map(video => `
            <div class="video-card">
                <div class="video-select">
                    <input type="checkbox" class="video-checkbox" value="${video.id}" onchange="updateSelectedCount()">
                </div>
                <div class="video-thumbnail" data-video-id="${video.id}" data-action="play">
                    <img src="/api/videos/${video.id}/thumbnail" 
                         alt="${video.title}" onerror="this.src='/static/placeholder-video.png'">
                    <div class="play-overlay">
                        <div class="play-button">▶</div>
                    </div>
                </div>
                <div class="video-info">
                    <h3>${video.title}</h3>
                    <p>Artist: ${video.artist_name || 'Unknown'}</p>
                    <p>Status: ${video.status}</p>
                    ${video.year ? `<p>Year: ${video.year}</p>` : ''}
                </div>
                <div class="video-actions">
                    <button data-video-id="${video.id}" data-action="view" class="btn-icon" title="View Details">
                        <i class="icon-eye"></i>
                    </button>
                    <button data-video-id="${video.id}" data-action="edit" class="btn-icon" title="Edit Video">
                        <i class="icon-edit"></i>
                    </button>
                    <button data-video-id="${video.id}" data-action="refresh-metadata" class="btn-icon" title="Refresh Metadata">
                        <i class="icon-refresh"></i>
                    </button>
                    ${video.status === 'WANTED' ? 
                        `<button data-video-id="${video.id}" data-action="download" class="btn-icon" title="Download Video">
                            <i class="icon-download"></i>
                        </button>` : 
                        ''}
                    <button data-video-id="${video.id}" data-action="delete" class="btn-icon btn-danger" title="Delete Video">
                        <i class="icon-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    } else {
        grid.innerHTML = '<p>No videos found matching your search criteria.</p>';
    }
}

function updateSearchResultsInfo(data) {
    const resultsInfo = document.getElementById('searchResults');
    resultsInfo.textContent = `Found ${data.count} of ${data.total} videos`;
}

function clearSearch() {
    // Clear search fields
    document.getElementById('searchQuery').value = '';
    document.getElementById('searchArtist').value = '';
    document.getElementById('searchStatus').value = '';
    document.getElementById('searchYear').value = '';
    
    // Clear results info
    document.getElementById('searchResults').textContent = '';
    
    // Reload all videos
    searchActive = false;
    loadVideos();
}

// Video filtering functions - previously missing
function applyVideoFilters() {
    console.log('Applying video filters...');
    
    // Helper function to safely get element value
    const getElementValue = (id) => {
        const element = document.getElementById(id);
        return element ? element.value : '';
    };
    
    // Get all filter values
    const filters = {
        status: getElementValue('videoStatusFilter'),
        quality: getElementValue('videoQualityFilter'),
        has_thumbnail: getElementValue('videoThumbnailFilter'),
        source: getElementValue('videoSourceFilter'),
        genre: getElementValue('videoGenreFilter'),
        duration_min: getElementValue('videoDurationMin'),
        duration_max: getElementValue('videoDurationMax'),
        date_from: getElementValue('videoDateFrom'),
        date_to: getElementValue('videoDateTo'),
        artist: getElementValue('videoArtistFilter'),
        keywords: getElementValue('videoKeywordsFilter'),
        sort_by: getElementValue('videoSortBy'),
        sort_order: getElementValue('videoSortOrder')
    };
    
    // Build query parameters
    const params = new URLSearchParams();
    
    // Add non-empty filters
    for (const [key, value] of Object.entries(filters)) {
        if (value && value.trim() !== '') {
            params.append(key, value);
        }
    }
    
    // Make API call to search/filter videos
    fetch(`/api/videos/search?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
            updateVideoFilterCount();
        })
        .catch(error => {
            console.error('Error filtering videos:', error);
            showError('Error filtering videos');
        });
}

function toggleVideoAdvancedFilters() {
    const filters = document.getElementById('videoAdvancedFilters');
    const button = document.getElementById('videoFiltersToggle');
    
    if (filters.style.display === 'none') {
        filters.style.display = 'block';
        button.textContent = 'Hide Filters';
    } else {
        filters.style.display = 'none';
        button.textContent = 'Show Filters';
    }
}

function clearAllVideoFilters() {
    // Helper function to safely clear element value
    const clearElementValue = (id) => {
        const element = document.getElementById(id);
        if (element) element.value = '';
    };
    
    // Clear all filter inputs
    clearElementValue('videoStatusFilter');
    clearElementValue('videoQualityFilter');
    clearElementValue('videoThumbnailFilter');
    clearElementValue('videoSourceFilter');
    clearElementValue('videoGenreFilter');
    clearElementValue('videoDurationMin');
    clearElementValue('videoDurationMax');
    clearElementValue('videoDateFrom');
    clearElementValue('videoDateTo');
    clearElementValue('videoArtistFilter');
    clearElementValue('videoKeywordsFilter');
    clearElementValue('videoSortBy');
    clearElementValue('videoSortOrder');
    
    // Reload all videos
    searchActive = false;
    loadVideos();
    updateVideoFilterCount();
}

function updateVideoFilterCount() {
    const filterCount = document.getElementById('videoFilterCount');
    let activeFilters = 0;
    
    // Count active filters
    const filterElements = [
        'videoStatusFilter', 'videoQualityFilter', 'videoThumbnailFilter',
        'videoSourceFilter', 'videoGenreFilter', 'videoDurationMin', 'videoDurationMax',
        'videoDateFrom', 'videoDateTo', 'videoArtistFilter', 'videoKeywordsFilter'
    ];
    
    filterElements.forEach(id => {
        const element = document.getElementById(id);
        if (element && element.value && element.value.trim() !== '') {
            activeFilters++;
        }
    });
    
    if (activeFilters > 0) {
        filterCount.textContent = activeFilters;
        filterCount.style.display = 'inline';
    } else {
        filterCount.style.display = 'none';
    }
}

function loadVideoGenreOptions() {
    // Load available genres from the API
    fetch('/api/genres')
        .then(response => response.json())
        .then(data => {
            const genreSelect = document.getElementById('videoGenreFilter');
            if (!genreSelect) {
                console.log('Genre filter element not found, skipping genre loading');
                return;
            }
            if (data.video_genres && data.video_genres.length > 0) {
                // Clear existing options (except the first "All Genres" option)
                genreSelect.innerHTML = '<option value="">All Genres</option>';
                
                // Add each genre as an option
                data.video_genres.forEach(genre => {
                    const option = document.createElement('option');
                    option.value = genre;
                    option.textContent = genre;
                    genreSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading video genres:', error);
        });
}

function saveVideoSearchPreset() {
    showInfo('Video search preset functionality coming soon!');
}

function exportVideoSearchResults() {
    showInfo('Video search results export functionality coming soon!');
}

function refreshThumbnails() {
    const selectedVideoIds = getSelectedVideoIds();
    const isSelectedVideos = selectedVideoIds.length > 0;
    const message = isSelectedVideos 
        ? `Download thumbnails for ${selectedVideoIds.length} selected videos that are missing them?`
        : 'Download thumbnails for all videos that are missing them?';
        
    toastConfirm(message, () => {
        const requestBody = isSelectedVideos ? { video_ids: selectedVideoIds } : {};
        
        fetch('/api/videos/refresh-thumbnails', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                showError('Error: ' + result.error);
            } else {
                showSuccess(result.message);
                loadVideos(); // Refresh the video list
            }
        })
        .catch(error => {
            console.error('Error refreshing thumbnails:', error);
            showError('Error refreshing thumbnails');
        });
    });
}

function viewVideo(id) {
    // Navigate to video detail page
    window.location.href = `/video/${id}`;
}

function editVideo(id) {
    // Fetch video data and populate the edit form
    fetch(`/api/videos/${id}`)
        .then(response => response.json())
        .then(video => {
            if (video.error) {
                showError('Error loading video data: ' + video.error);
                return;
            }
            
            // Populate the form with current video data
            document.getElementById('videoTitle').value = video.title || '';
            document.getElementById('videoArtist').value = video.artist_name || '';
            document.getElementById('videoYear').value = video.year || '';
            document.getElementById('videoGenre').value = (video.genres && video.genres.length > 0) ? video.genres[0] : '';
            document.getElementById('videoStatus').value = video.status || 'DOWNLOADED';
            document.getElementById('videoUrl').value = video.video_url || '';
            document.getElementById('videoThumbnailUrl').value = video.thumbnail_url || '';
            document.getElementById('videoDuration').value = video.duration || '';
            document.getElementById('videoImvdbId').value = video.imvdb_id || '';
            document.getElementById('moveFile').checked = true;
            
            // Store the current video ID for the form submission
            window.currentEditVideoId = id;
            
            // Reset the identify artist button and hide suggestions
            resetIdentifyArtistButton();
            document.getElementById('artistSuggestions').style.display = 'none';
            
            // Show the edit modal
            document.getElementById('editVideoModal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error fetching video data:', error);
            showError('Error loading video data');
        });
}

function closeEditVideoModal() {
    document.getElementById('editVideoModal').style.display = 'none';
    document.getElementById('artistSuggestions').style.display = 'none';
    resetIdentifyArtistButton();
    window.currentEditVideoId = null;
}

// Handle edit video form submission
document.getElementById('editVideoForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    if (!window.currentEditVideoId) {
        showWarning('No video selected for editing');
        return;
    }
    
    const formData = new FormData(this);
    const updateData = {
        title: formData.get('title'),
        artist_name: formData.get('artist_name'),
        year: formData.get('year') ? parseInt(formData.get('year')) : null,
        genres: formData.get('genre') ? [formData.get('genre')] : [],
        status: formData.get('status'),
        video_url: formData.get('video_url'),
        thumbnail_url: formData.get('thumbnail_url'),
        duration: formData.get('duration') ? parseInt(formData.get('duration')) : null,
        imvdb_id: formData.get('imvdb_id'),
        move_file: formData.get('move_file') === 'on'
    };
    
    // Remove empty string values
    Object.keys(updateData).forEach(key => {
        if (updateData[key] === '') {
            updateData[key] = null;
        }
    });
    
    fetch(`/api/videos/${window.currentEditVideoId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            showError('Error updating video: ' + result.error);
        } else {
            showSuccess('Video updated successfully!');
            closeEditVideoModal();
            loadVideos(); // Refresh the video list
        }
    })
    .catch(error => {
        console.error('Error updating video:', error);
        showError('Error updating video');
    });
});

function playVideo(videoId, title, localPath, videoUrl) {
    // Set modal title
    document.getElementById('videoModalTitle').textContent = title || 'Playing Video';
    
    // Create video player
    const playerDiv = document.getElementById('videoPlayer');
    
    // Prioritize local file if available
    if (localPath && localPath !== 'null' && localPath !== 'undefined') {
        // Check if this is a known unsupported format that needs VLC streaming
        let needsVLCStreaming = localPath.toLowerCase().endsWith('.mkv') || 
                                localPath.toLowerCase().endsWith('.avi');
        
        if (needsVLCStreaming) {
            // Use direct streaming for unsupported formats
            playerDiv.innerHTML = `
                <div class="video-loading">
                    <h3>🎬 Starting Video Stream...</h3>
                    <p>Transcoding video for browser playback using FFmpeg.</p>
                    <div class="loading-spinner"></div>
                </div>
            `;
            
            // Show modal
            document.getElementById('videoModal').style.display = 'block';
            
            // Track current video ID for cleanup
            window.currentVideoId = videoId;
            
            // Use the direct streaming endpoint
            const streamUrl = `/api/videos/${videoId}/stream`;
            
            // Give it a moment to show the loading message, then start the stream
            setTimeout(() => {
                playerDiv.innerHTML = `
                    <video width="800" height="450" controls autoplay>
                        <source src="${streamUrl}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                    <div class="stream-info">
                        <p><small>Streaming via FFmpeg transcoding</small></p>
                    </div>
                `;
            }, 1000);
            
            return;
        }
        
        // Determine MIME type based on file extension
        let mimeType = 'video/mp4'; // default
        if (localPath.toLowerCase().endsWith('.mkv')) {
            mimeType = 'video/x-matroska';
        } else if (localPath.toLowerCase().endsWith('.webm')) {
            mimeType = 'video/webm';
        } else if (localPath.toLowerCase().endsWith('.avi')) {
            mimeType = 'video/x-msvideo';
        } else if (localPath.toLowerCase().endsWith('.mov')) {
            mimeType = 'video/quicktime';
        }
        
        // Play local file via streaming endpoint with proper MIME type
        playerDiv.innerHTML = `
            <video width="800" height="450" controls preload="metadata">
                <source src="/api/videos/${videoId}/stream" type="${mimeType}">
                Your browser does not support the video tag or this video format.
            </video>
        `;
        
        // Add error handling for video load failures
        const video = playerDiv.querySelector('video');
        
        // Add timeout for video loading
        let loadTimeout;
        let hasLoaded = false;
        
        video.addEventListener('error', function(e) {
            console.error('Video playback error:', e);
            clearTimeout(loadTimeout);
            showVideoError(videoId, localPath, mimeType, 'Video failed to load');
        });
        
        video.addEventListener('loadstart', function() {
            console.log('Video load started for:', localPath, 'Type:', mimeType);
            hasLoaded = false;
            
            // Set timeout for loading - if video doesn't load within 10 seconds, show error
            loadTimeout = setTimeout(() => {
                if (!hasLoaded) {
                    console.warn('Video loading timeout for:', localPath);
                    showVideoError(videoId, localPath, mimeType, 'Video loading timeout - format may not be supported');
                }
            }, 10000);
        });
        
        video.addEventListener('loadeddata', function() {
            console.log('Video loaded successfully:', localPath);
            hasLoaded = true;
            clearTimeout(loadTimeout);
        });
        
        video.addEventListener('canplay', function() {
            hasLoaded = true;
            clearTimeout(loadTimeout);
        });
        
        // Check if format is likely unsupported and warn immediately
        let formatUnsupported = localPath.toLowerCase().endsWith('.mkv') || 
                               localPath.toLowerCase().endsWith('.avi');
        
        if (formatUnsupported) {
            // Show immediate warning for known unsupported formats
            setTimeout(() => {
                if (!hasLoaded) {
                    console.warn('Likely unsupported format detected:', localPath);
                    showVideoError(videoId, localPath, mimeType, 'This video format may not be supported by your browser');
                }
            }, 3000); // Check after 3 seconds
        }
        
    } else if (videoUrl && videoUrl !== 'null' && videoUrl !== 'undefined') {
        // Fall back to YouTube or other URL
        if (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be')) {
            // Extract YouTube video ID
            const youtubeId = extractYouTubeId(videoUrl);
            if (youtubeId) {
                playerDiv.innerHTML = `
                    <iframe width="800" height="450" 
                            src="https://www.youtube.com/embed/${youtubeId}" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen>
                    </iframe>
                `;
            }
        } else {
            // For other video URLs, try using HTML5 video element
            playerDiv.innerHTML = `
                <video width="800" height="450" controls>
                    <source src="${videoUrl}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            `;
        }
    } else {
        showWarning('No video file available for playback');
        return;
    }
    
    // Show modal
    document.getElementById('videoModal').style.display = 'block';
}

function extractYouTubeId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

function closeVideoModal() {
    const modal = document.getElementById('videoModal');
    const playerDiv = document.getElementById('videoPlayer');
    
    // Clear the player to stop playback
    playerDiv.innerHTML = '';
    
    // Hide modal
    modal.style.display = 'none';
    
    // Clear current video ID
    window.currentVideoId = null;
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const videoModal = document.getElementById('videoModal');
    const editModal = document.getElementById('editVideoModal');
    
    if (event.target === videoModal) {
        closeVideoModal();
    }
    
    if (event.target === editModal) {
        closeEditVideoModal();
    }
}

function downloadVideo(id) {
    // Removed download confirmation popup - direct download
    {
        fetch(`/api/videos/${id}/download`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                showError('Error: ' + result.error);
            } else {
                showSuccessToast('Video queued for download');
                loadVideos();
            }
        })
        .catch(error => {
            console.error('Error downloading video:', error);
            showErrorToast('Error queuing video for download');
        });
    }
}

function transcodeVideo(id) {
    toastConfirm('Convert this video to MP4 for better browser compatibility? This may take a few minutes depending on file size.', () => {
        // Show progress in the modal
        const playerDiv = document.getElementById('videoPlayer');
        playerDiv.innerHTML = `
            <div class="transcoding-progress">
                <h3>🔄 Converting Video...</h3>
                <p>Converting to MP4 format for better browser compatibility.</p>
                <p>This may take several minutes depending on the video size.</p>
                <div class="progress-spinner"></div>
                <button onclick="closeVideoModal()" class="btn btn-secondary">Close</button>
            </div>
        `;
        
        fetch(`/api/videos/${id}/transcode`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                playerDiv.innerHTML = `
                    <div class="transcoding-error">
                        <h3>❌ Conversion Failed</h3>
                        <p>Error: ${result.error}</p>
                        <button onclick="closeVideoModal()" class="btn btn-primary">Close</button>
                    </div>
                `;
            } else {
                // Start checking status
                checkTranscodingStatus(id);
            }
        })
        .catch(error => {
            console.error('Error transcoding video:', error);
            playerDiv.innerHTML = `
                <div class="transcoding-error">
                    <h3>❌ Conversion Failed</h3>
                    <p>Error starting video conversion: ${error.message}</p>
                    <button onclick="closeVideoModal()" class="btn btn-primary">Close</button>
                </div>
            `;
        });
    });
}

function checkTranscodingStatus(id) {
    const playerDiv = document.getElementById('videoPlayer');
    
    fetch(`/api/videos/${id}/transcode/status`)
        .then(response => response.json())
        .then(result => {
            if (result.status === 'completed') {
                playerDiv.innerHTML = `
                    <div class="transcoding-success">
                        <h3>✅ Conversion Complete!</h3>
                        <p>Video has been converted to MP4 format.</p>
                        <button onclick="refreshAndPlay(${id})" class="btn btn-success">Play Video</button>
                        <button onclick="closeVideoModal()" class="btn btn-secondary">Close</button>
                    </div>
                `;
            } else if (result.status === 'processing' || result.status === 'not_started') {
                // Keep checking every 5 seconds
                setTimeout(() => checkTranscodingStatus(id), 5000);
            } else {
                playerDiv.innerHTML = `
                    <div class="transcoding-error">
                        <h3>❌ Conversion Status Unknown</h3>
                        <p>Status: ${result.status}</p>
                        <button onclick="closeVideoModal()" class="btn btn-primary">Close</button>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error checking transcoding status:', error);
            // Stop checking on error
        });
}

function tryPlayAnyway(videoId, title, localPath, videoUrl) {
    // Proceed with normal playback attempt
    const playerDiv = document.getElementById('videoPlayer');
    
    // Determine MIME type based on file extension
    let mimeType = 'video/mp4'; // default
    if (localPath.toLowerCase().endsWith('.mkv')) {
        mimeType = 'video/x-matroska';
    } else if (localPath.toLowerCase().endsWith('.webm')) {
        mimeType = 'video/webm';
    } else if (localPath.toLowerCase().endsWith('.avi')) {
        mimeType = 'video/x-msvideo';
    } else if (localPath.toLowerCase().endsWith('.mov')) {
        mimeType = 'video/quicktime';
    }
    
    // Play local file via streaming endpoint with proper MIME type
    playerDiv.innerHTML = `
        <video width="800" height="450" controls preload="metadata">
            <source src="/api/videos/${videoId}/stream" type="${mimeType}">
            Your browser does not support the video tag or this video format.
        </video>
    `;
    
    // Add all the same error handling as the normal playback
    const video = playerDiv.querySelector('video');
    let loadTimeout;
    let hasLoaded = false;
    
    video.addEventListener('error', function(e) {
        console.error('Video playback error:', e);
        clearTimeout(loadTimeout);
        showVideoError(videoId, localPath, mimeType, 'Video failed to load');
    });
    
    video.addEventListener('loadstart', function() {
        console.log('Video load started for:', localPath, 'Type:', mimeType);
        hasLoaded = false;
        
        loadTimeout = setTimeout(() => {
            if (!hasLoaded) {
                console.warn('Video loading timeout for:', localPath);
                showVideoError(videoId, localPath, mimeType, 'Video loading timeout - format may not be supported');
            }
        }, 10000);
    });
    
    video.addEventListener('loadeddata', function() {
        console.log('Video loaded successfully:', localPath);
        hasLoaded = true;
        clearTimeout(loadTimeout);
    });
    
    video.addEventListener('canplay', function() {
        hasLoaded = true;
        clearTimeout(loadTimeout);
    });
}

function showVideoError(videoId, localPath, mimeType, errorMessage) {
    const playerDiv = document.getElementById('videoPlayer');
    let unsupportedVideoFormat = localPath.toLowerCase().endsWith('.mkv') || 
                                 localPath.toLowerCase().endsWith('.avi');
    
    playerDiv.innerHTML = `
        <div class="video-error">
            <p>⚠️ ${errorMessage}</p>
            <p><strong>File:</strong> ${localPath}</p>
            <p><strong>Type:</strong> ${mimeType}</p>
            ${unsupportedVideoFormat ? `
                <p><em>Note: .mkv and .avi files have limited browser support.</em></p>
                <button onclick="transcodeVideo(${videoId})" class="btn btn-warning">Convert to MP4</button>
            ` : ''}
            <button onclick="closeVideoModal()" class="btn btn-primary">Close</button>
        </div>
    `;
}

function refreshAndPlay(id) {
    // Refresh the video list to get updated paths
    loadVideos();
    
    // Close modal and show success message
    closeVideoModal();
    showSuccess('Video converted successfully! Try playing it again.');
}

function refreshVideoMetadata(id) {
    toastConfirm('Refresh metadata for this video from IMVDb? This will update year, directors, producers, and thumbnail information.', () => {
        // Find the video card to show loading state
        const videoCard = document.querySelector(`[data-video-id="${id}"]`).closest('.video-card');
        const originalContent = videoCard.innerHTML;
        
        // Show loading state
        videoCard.innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <div class="loading-spinner"></div>
                <p>Refreshing metadata from IMVDb...</p>
            </div>
        `;
        
        fetch(`/api/videos/${id}/refresh-metadata`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                showError('Error: ' + result.error);
                // Restore original content on error
                videoCard.innerHTML = originalContent;
            } else if (result.success === false) {
                showWarning('Warning: ' + result.message);
                // Restore original content if no match found
                videoCard.innerHTML = originalContent;
            } else {
                showSuccess('Metadata refreshed successfully!');
                // Update just this video card instead of reloading entire page
                updateSingleVideoCard(id);
            }
        })
        .catch(error => {
            console.error('Error refreshing metadata:', error);
            showError('Error refreshing metadata');
            // Restore original content on error
            videoCard.innerHTML = originalContent;
        });
    });
}

function updateSingleVideoCard(videoId) {
    // Fetch updated video data from API
    fetch(`/api/videos/${videoId}`)
        .then(response => response.json())
        .then(video => {
            if (video.error) {
                showError('Error loading updated video data');
                return;
            }
            
            // Find the video card that needs updating
            const videoElement = document.querySelector(`[data-video-id="${videoId}"]`);
            if (!videoElement) {
                console.error(`Video element with ID ${videoId} not found for update`);
                return;
            }
            
            const videoCard = videoElement.closest('.video-card');
            if (!videoCard) {
                console.error(`Video card not found for video ID ${videoId}`);
                return;
            }
            
            // Preserve checkbox state
            const checkbox = videoCard.querySelector('.video-checkbox');
            const isChecked = checkbox ? checkbox.checked : false;
            
            // Generate new video card HTML (matching the template from loadVideos)
            const newCardHTML = `
                <div class="video-select">
                    <input type="checkbox" class="video-checkbox" value="${video.id}" onchange="updateSelectedCount()" ${isChecked ? 'checked' : ''}>
                </div>
                <div class="video-thumbnail" data-video-id="${video.id}" data-action="play">
                    <img src="/api/videos/${video.id}/thumbnail" 
                         alt="${video.title}"
                         onerror="this.src='/static/default-thumbnail.png'">
                    <div class="video-overlay">
                        <div class="video-play-btn">▶</div>
                    </div>
                </div>
                <div class="video-info">
                    <h3>${video.title}</h3>
                    <p>Artist: ${video.artist ? video.artist.name : 'Unknown'}</p>
                    <p>Status: <span class="status-${video.status ? video.status.toLowerCase() : 'unknown'}">${video.status || 'Unknown'}</span></p>
                    <p>Year: ${video.year || 'Unknown'}</p>
                    ${video.directors ? `<p>Directors: ${video.directors}</p>` : ''}
                    ${video.producers ? `<p>Producers: ${video.producers}</p>` : ''}
                </div>
                <div class="video-actions">
                    <button data-video-id="${video.id}" data-action="edit" class="btn-icon" title="Edit Video">
                        <iconify-icon icon="tabler:edit"></iconify-icon>
                    </button>
                    <button data-video-id="${video.id}" data-action="download" class="btn-icon" title="Download Video">
                        <iconify-icon icon="tabler:download"></iconify-icon>
                    </button>
                    <button data-video-id="${video.id}" data-action="refresh-metadata" class="btn-icon" title="Refresh Metadata">
                        <iconify-icon icon="tabler:refresh"></iconify-icon>
                    </button>
                    <button data-video-id="${video.id}" data-action="delete" class="btn-icon btn-danger" title="Delete Video">
                        <iconify-icon icon="tabler:trash"></iconify-icon>
                    </button>
                </div>
            `;
            
            // Replace the video card content
            videoCard.innerHTML = newCardHTML;
        })
        .catch(error => {
            console.error('Error updating video card:', error);
            showError('Error updating video display');
        });
}

function refreshAllMetadata() {
    const selectedVideoIds = getSelectedVideoIds();
    const isSelectedVideos = selectedVideoIds.length > 0;
    const message = isSelectedVideos 
        ? `Refresh metadata from IMVDb for ${selectedVideoIds.length} selected videos that don't have IMVDb data? This may take several minutes.`
        : 'Refresh metadata from IMVDb for all videos that don\'t have IMVDb data? This may take several minutes.';
        
    toastConfirm(message, () => {
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = 'Refreshing...';
        button.disabled = true;
        
        const requestBody = {
            force_refresh: false,
            limit: isSelectedVideos ? selectedVideoIds.length : 100  // Process selected videos or first 100
        };
        
        if (isSelectedVideos) {
            requestBody.video_ids = selectedVideoIds;
        }
        
        fetch('/api/videos/refresh-all-metadata', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(result => {
            button.textContent = originalText;
            button.disabled = false;
            
            if (result.error) {
                showError('Error: ' + result.error);
            } else {
                const message = `Metadata refresh completed!\n\nProcessed: ${result.processed}\nUpdated: ${result.updated}\nErrors: ${result.errors}`;
                showSuccess(message);
                loadVideos(); // Refresh the video list
            }
        })
        .catch(error => {
            console.error('Error refreshing all metadata:', error);
            showError(`Error refreshing metadata: ${error.message}`);
            button.textContent = originalText;
            button.disabled = false;
        });
    });
}


function deleteVideo(id) {
    toastConfirm('Are you sure you want to delete this video? This action cannot be undone.', () => {
        fetch(`/api/videos/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                showError('Error: ' + result.error);
            } else {
                showSuccess('Video deleted successfully!');
                loadVideos();
            }
        })
        .catch(error => {
            console.error('Error deleting video:', error);
            showError('Error deleting video');
        });
    });
}

function identifyArtist() {
    const videoId = window.currentEditVideoId;
    if (!videoId) {
        showWarning('No video selected');
        return;
    }
    
    const button = document.getElementById('identifyArtistBtn');
    button.textContent = '🔄 Identifying...';
    button.disabled = true;
    
    // Store the request so it can be aborted if needed
    const abortController = new AbortController();
    window.currentIdentifyRequest = abortController;
    
    fetch(`/api/videos/${videoId}/identify-artist`, {
        method: 'POST',
        signal: abortController.signal
    })
    .then(response => response.json())
    .then(result => {
        // Only process if this request is still current
        if (window.currentIdentifyRequest === abortController) {
            resetIdentifyArtistButton();
            
            if (result.error) {
                showError('Error identifying artist: ' + result.error);
                return;
            }
            
            displayArtistSuggestions(result);
        }
    })
    .catch(error => {
        // Only show error if request wasn't aborted
        if (window.currentIdentifyRequest === abortController && error.name !== 'AbortError') {
            console.error('Error identifying artist:', error);
            showError('Error identifying artist');
        }
        
        // Reset button if this was the current request
        if (window.currentIdentifyRequest === abortController) {
            resetIdentifyArtistButton();
        }
    });
}

function displayArtistSuggestions(data) {
    const suggestionsDiv = document.getElementById('artistSuggestions');
    
    if (!data.suggestions || data.suggestions.length === 0) {
        suggestionsDiv.innerHTML = `
            <h4>No Artist Suggestions Found</h4>
            <p>No automatic suggestions could be generated for "${data.title}".</p>
            <div class="manual-entry">
                <label>Enter artist name manually:</label>
                <div class="autocomplete-container">
                    <input type="text" id="manualArtistInput" placeholder="Enter artist name" 
                           oninput="searchExistingArtists(this.value)" 
                           onkeydown="handleAutocompleteKeydown(event)"
                           autocomplete="off">
                    <div id="artistAutocomplete" class="autocomplete-suggestions" style="display: none;"></div>
                </div>
                <button type="button" onclick="applyManualArtist()" class="btn btn-primary btn-small" style="margin-top: 5px;">Apply</button>
            </div>
        `;
        suggestionsDiv.style.display = 'block';
        return;
    }
    
    let html = `<h4>Artist Suggestions for "${data.title}":</h4>`;
    
    data.suggestions.forEach((suggestion, index) => {
        const confidenceClass = getConfidenceClass(suggestion.confidence);
        const confidencePercent = Math.round(suggestion.confidence * 100);
        
        html += `
            <div class="artist-suggestion" onclick="selectArtistSuggestion('${suggestion.artist_name}')">
                <div class="artist-suggestion-name">${suggestion.artist_name}</div>
                <div class="artist-suggestion-details">
                    <span class="artist-suggestion-confidence ${confidenceClass}">
                        ${confidencePercent}%
                    </span>
                    Source: ${suggestion.source}
                    ${suggestion.reason ? `<br><em>${suggestion.reason}</em>` : ''}
                </div>
            </div>
        `;
    });
    
    // Add manual entry option
    html += `
        <div class="manual-entry">
            <label>Or enter artist name manually:</label>
            <input type="text" id="manualArtistInput" placeholder="Enter artist name">
            <button type="button" onclick="applyManualArtist()" class="btn btn-primary btn-small" style="margin-top: 5px;">Apply</button>
        </div>
    `;
    
    suggestionsDiv.innerHTML = html;
    suggestionsDiv.style.display = 'block';
}

function getConfidenceClass(confidence) {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.6) return 'medium';
    return 'low';
}

function selectArtistSuggestion(artistName) {
    document.getElementById('videoArtist').value = artistName;
    document.getElementById('artistSuggestions').style.display = 'none';
}

function applyManualArtist() {
    const manualInput = document.getElementById('manualArtistInput');
    const artistName = manualInput.value.trim();
    
    if (artistName) {
        document.getElementById('videoArtist').value = artistName;
        document.getElementById('artistSuggestions').style.display = 'none';
    } else {
        showWarning('Please enter an artist name');
    }
}

function resetIdentifyArtistButton() {
    // Abort any pending identify request
    if (window.currentIdentifyRequest) {
        window.currentIdentifyRequest.abort();
        window.currentIdentifyRequest = null;
    }
    
    const button = document.getElementById('identifyArtistBtn');
    if (button) {
        button.textContent = '🔍 Identify Artist';
        button.disabled = false;
    }
}

// Autocomplete functionality for artist search
let autocompleteTimeout;
let selectedAutocompleteIndex = -1;

function searchExistingArtists(query) {
    // Clear previous timeout
    if (autocompleteTimeout) {
        clearTimeout(autocompleteTimeout);
    }
    
    // Reset selection
    selectedAutocompleteIndex = -1;
    
    // Debounce the search
    autocompleteTimeout = setTimeout(() => {
        if (query.length < 2) {
            hideAutocomplete();
            return;
        }
        
        fetch(`/api/videos/search-artists?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displayAutocomplete(data.artists);
            })
            .catch(error => {
                console.error('Error searching artists:', error);
                hideAutocomplete();
            });
    }, 300); // Wait 300ms after user stops typing
}

function displayAutocomplete(artists) {
    const autocompleteDiv = document.getElementById('artistAutocomplete');
    
    if (!artists || artists.length === 0) {
        hideAutocomplete();
        return;
    }
    
    let html = '';
    artists.forEach((artist, index) => {
        html += `
            <div class="autocomplete-suggestion" data-artist-name="${artist.name.replace(/"/g, '&quot;')}" data-index="${index}">
                <span class="autocomplete-suggestion-name">${artist.name}</span>
                <span class="autocomplete-suggestion-count">(${artist.video_count} videos)</span>
            </div>
        `;
    });
    
    autocompleteDiv.innerHTML = html;
    autocompleteDiv.style.display = 'block';
    
    // Add click event listeners for autocomplete suggestions
    autocompleteDiv.querySelectorAll('.autocomplete-suggestion').forEach(suggestion => {
        suggestion.addEventListener('click', function() {
            const artistName = this.getAttribute('data-artist-name');
            selectAutocompleteArtist(artistName);
        });
    });
}

function hideAutocomplete() {
    const autocompleteDiv = document.getElementById('artistAutocomplete');
    if (autocompleteDiv) {
        autocompleteDiv.style.display = 'none';
    }
    selectedAutocompleteIndex = -1;
}

function selectAutocompleteArtist(artistName) {
    document.getElementById('manualArtistInput').value = artistName;
    hideAutocomplete();
}

function handleAutocompleteKeydown(event) {
    const autocompleteDiv = document.getElementById('artistAutocomplete');
    const suggestions = autocompleteDiv.querySelectorAll('.autocomplete-suggestion');
    
    if (suggestions.length === 0) {
        return;
    }
    
    switch (event.key) {
        case 'ArrowDown':
            event.preventDefault();
            selectedAutocompleteIndex = Math.min(selectedAutocompleteIndex + 1, suggestions.length - 1);
            updateAutocompleteSelection(suggestions);
            break;
            
        case 'ArrowUp':
            event.preventDefault();
            selectedAutocompleteIndex = Math.max(selectedAutocompleteIndex - 1, -1);
            updateAutocompleteSelection(suggestions);
            break;
            
        case 'Enter':
            event.preventDefault();
            if (selectedAutocompleteIndex >= 0) {
                const selectedSuggestion = suggestions[selectedAutocompleteIndex];
                const artistName = selectedSuggestion.getAttribute('data-artist-name');
                selectAutocompleteArtist(artistName);
            }
            break;
            
        case 'Escape':
            hideAutocomplete();
            break;
    }
}

function updateAutocompleteSelection(suggestions) {
    // Remove previous selection
    suggestions.forEach(suggestion => {
        suggestion.classList.remove('selected');
    });
    
    // Add selection to current item
    if (selectedAutocompleteIndex >= 0) {
        suggestions[selectedAutocompleteIndex].classList.add('selected');
    }
}

// Hide autocomplete when clicking outside
document.addEventListener('click', function(event) {
    const autocompleteContainer = document.querySelector('.autocomplete-container');
    if (autocompleteContainer && !autocompleteContainer.contains(event.target)) {
        hideAutocomplete();
    }
});

// Bulk Selection Functions
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllVideos');
    const videoCheckboxes = document.querySelectorAll('.video-checkbox');
    
    videoCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateSelectedCount();
}

function updateSelectedCount() {
    const selectedCheckboxes = document.querySelectorAll('.video-checkbox:checked');
    const count = selectedCheckboxes.length;
    
    const selectedCountEl = document.getElementById('selectedCount');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    
    if (selectedCountEl) selectedCountEl.textContent = count;
    if (deleteSelectedBtn) deleteSelectedBtn.disabled = count === 0;
    
    // Update select all checkbox state
    const selectAllCheckbox = document.getElementById('selectAllVideos');
    const videoCheckboxes = document.querySelectorAll('.video-checkbox');
    
    if (selectAllCheckbox) {
        if (count === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (count === videoCheckboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
        }
    }
}

function deleteSelectedVideos() {
    const selectedCheckboxes = document.querySelectorAll('.video-checkbox:checked');
    const videoIds = Array.from(selectedCheckboxes).map(checkbox => parseInt(checkbox.value));
    
    if (videoIds.length === 0) {
        showError('No videos selected');
        return;
    }
    
    const confirmed = confirm(`Are you sure you want to delete ${videoIds.length} selected video(s)?\n\nThis action cannot be undone.`);
    
    if (confirmed) {
        const deleteBtn = document.getElementById('deleteSelectedBtn');
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = '🔄 Deleting...';
        
        fetch('/api/videos/bulk/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_ids: videoIds
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.deleted_count > 0) {
                showSuccess(`Successfully deleted ${data.deleted_count} video(s)`);
                if (data.failed_count > 0) {
                    showWarning(`Failed to delete ${data.failed_count} video(s)`);
                }
                // Refresh the video list
                loadVideos();
            } else {
                showError('Failed to delete videos: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error deleting videos:', error);
            showError('Failed to delete videos: ' + error.message);
        })
        .finally(() => {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = '🗑️ Delete Selected (<span id="selectedCount">0</span>)';
            // Reset selection
            document.getElementById('selectAllVideos').checked = false;
            updateSelectedCount();
        });
    }
}