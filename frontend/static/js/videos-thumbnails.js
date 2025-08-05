// Video Thumbnail Management Functions
let currentVideoThumbnailId = null;

function openVideoThumbnailManager() {
    if (!window.currentEditVideoId) {
        showError('No video selected for thumbnail management');
        return;
    }
    
    currentVideoThumbnailId = window.currentEditVideoId;
    document.getElementById('videoThumbnailModal').style.display = 'block';
    
    // Load current thumbnail info
    loadVideoThumbnailInfo();
    
    // Initialize drag & drop
    initializeVideoThumbnailUpload();
}

function closeVideoThumbnailModal() {
    document.getElementById('videoThumbnailModal').style.display = 'none';
    currentVideoThumbnailId = null;
}

function switchVideoUploadTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.upload-tab').forEach(tab => tab.classList.remove('active'));
    document.getElementById(`video${tabName.charAt(0).toUpperCase() + tabName.slice(1)}UploadTab`).classList.add('active');
    
    // Update panels
    document.querySelectorAll('.upload-panel').forEach(panel => panel.style.display = 'none');
    document.getElementById(`video${tabName.charAt(0).toUpperCase() + tabName.slice(1)}UploadPanel`).style.display = 'block';
}

function loadVideoThumbnailInfo() {
    if (!currentVideoThumbnailId) return;
    
    fetch(`/api/videos/${currentVideoThumbnailId}/thumbnail/info`)
        .then(response => response.json())
        .then(data => {
            const thumbnailImg = document.getElementById('currentVideoThumbnailImg');
            const placeholder = document.getElementById('noVideoThumbnailPlaceholder');
            const overlay = document.getElementById('videoThumbnailOverlay');
            const metadata = document.getElementById('videoThumbnailMetadata');
            
            if (data.has_thumbnail) {
                // Show thumbnail image with cache busting
                thumbnailImg.src = `/api/videos/${currentVideoThumbnailId}/thumbnail?t=${Date.now()}`;
                thumbnailImg.style.display = 'block';
                placeholder.style.display = 'none';
                overlay.style.display = 'block';
                
                // Update metadata
                document.getElementById('videoThumbnailSource').textContent = data.thumbnail_source || 'Unknown';
                document.getElementById('videoThumbnailSize').textContent = data.file_size || 'Unknown';
                document.getElementById('videoThumbnailFormat').textContent = data.format || 'Unknown';
                metadata.style.display = 'block';
            } else {
                // Show placeholder
                thumbnailImg.style.display = 'none';
                placeholder.style.display = 'block';
                overlay.style.display = 'none';
                metadata.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error loading thumbnail info:', error);
            showError('Failed to load thumbnail information');
        });
}

function initializeVideoThumbnailUpload() {
    const dragDropArea = document.getElementById('videoDragDropArea');
    const fileInput = document.getElementById('videoThumbnailFileInput');
    
    if (!dragDropArea || !fileInput) return;
    
    // Drag & drop handlers
    dragDropArea.addEventListener('click', () => fileInput.click());
    
    dragDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dragDropArea.classList.add('drag-over');
    });
    
    dragDropArea.addEventListener('dragleave', () => {
        dragDropArea.classList.remove('drag-over');
    });
    
    dragDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dragDropArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleVideoThumbnailFile(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleVideoThumbnailFile(e.target.files[0]);
        }
    });
}

function handleVideoThumbnailFile(file) {
    if (!file.type.startsWith('image/')) {
        showError('Please select an image file');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB
        showError('File size must be less than 10MB');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const progress = document.getElementById('videoUploadProgress');
    const progressFill = document.getElementById('videoUploadProgressFill');
    const progressText = document.getElementById('videoUploadProgressText');
    
    progress.style.display = 'block';
    progressFill.style.width = '0%';
    
    fetch(`/api/videos/${currentVideoThumbnailId}/thumbnail/upload`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        progressFill.style.width = '100%';
        return response.json();
    })
    .then(data => {
        progress.style.display = 'none';
        
        if (data.error) {
            showError('Upload failed: ' + data.error);
        } else {
            showSuccess('Thumbnail uploaded successfully');
            loadVideoThumbnailInfo();
            refreshVideoDisplayThumbnail();
            
            // Update the thumbnail URL field in the edit form
            document.getElementById('videoThumbnailUrl').value = '';
        }
    })
    .catch(error => {
        progress.style.display = 'none';
        console.error('Upload error:', error);
        showError('Upload failed: ' + error.message);
    });
}

function previewVideoUrlImage() {
    const url = document.getElementById('videoThumbnailUrlInput').value;
    if (!url) {
        showError('Please enter an image URL');
        return;
    }
    
    const preview = document.getElementById('videoUrlPreview');
    const img = document.getElementById('videoUrlPreviewImg');
    
    img.src = url;
    preview.style.display = 'block';
}

function uploadVideoFromUrl() {
    const url = document.getElementById('videoThumbnailUrlInput').value;
    if (!url) {
        showError('Please enter an image URL');
        return;
    }
    
    fetch(`/api/videos/${currentVideoThumbnailId}/thumbnail`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'update',
            thumbnail_url: url
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError('Failed to update thumbnail: ' + data.error);
        } else {
            showSuccess('Thumbnail URL updated successfully');
            loadVideoThumbnailInfo();
            refreshVideoDisplayThumbnail();
            
            // Update the thumbnail URL field in the edit form
            document.getElementById('videoThumbnailUrl').value = url;
        }
    })
    .catch(error => {
        console.error('Error updating thumbnail:', error);
        showError('Failed to update thumbnail');
    });
}

function searchVideoThumbnails() {
    console.log('searchVideoThumbnails called, currentVideoThumbnailId:', currentVideoThumbnailId);
    
    const youtubeCheckbox = document.getElementById('searchYoutube');
    const imvdbCheckbox = document.getElementById('searchImvdb');
    const googleCheckbox = document.getElementById('searchGoogle');
    
    console.log('YouTube checkbox element:', youtubeCheckbox);
    console.log('IMVDb checkbox element:', imvdbCheckbox);
    console.log('Google checkbox element:', googleCheckbox);
    
    if (!youtubeCheckbox || !imvdbCheckbox || !googleCheckbox) {
        showError('Search checkboxes not found');
        return;
    }
    
    const includeYoutube = youtubeCheckbox.checked;
    const includeImvdb = imvdbCheckbox.checked;
    const includeGoogle = googleCheckbox.checked;
    
    console.log('YouTube checked:', includeYoutube, 'IMVDb checked:', includeImvdb, 'Google checked:', includeGoogle);
    
    const sources = [];
    if (includeYoutube) sources.push('youtube');
    if (includeImvdb) sources.push('imvdb');
    if (includeGoogle) sources.push('google');
    
    if (sources.length === 0) {
        showError('Please select at least one search source');
        return;
    }
    
    if (!currentVideoThumbnailId) {
        showError('No video selected for thumbnail search');
        return;
    }
    
    console.log('Making API call with sources:', sources);
    
    fetch(`/api/videos/${currentVideoThumbnailId}/thumbnail/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sources: sources
        })
    })
    .then(response => {
        console.log('API response received:', response.status, response.statusText);
        return response.json();
    })
    .then(data => {
        console.log('API response data:', data);
        if (data.error) {
            showError('Search failed: ' + data.error);
        } else {
            displayVideoThumbnailResults(data.results);
        }
    })
    .catch(error => {
        console.error('Search error:', error);
        showError('Search failed: ' + error.message);
    });
}

function displayVideoThumbnailResults(results) {
    console.log('displayVideoThumbnailResults called with:', results);
    const resultsContainer = document.getElementById('videoThumbnailSearchResults');
    const grid = document.getElementById('videoThumbnailResultsGrid');
    
    console.log('Results container:', resultsContainer);
    console.log('Results container class:', resultsContainer.className);
    console.log('Results container style:', resultsContainer.style.display);
    console.log('Grid container:', grid);
    console.log('Grid container class:', grid.className);
    
    if (!resultsContainer || !grid) {
        console.error('Results container or grid not found');
        showError('Search results container not found');
        return;
    }
    
    if (results.length === 0) {
        grid.innerHTML = '<p>No thumbnails found</p>';
        console.log('No results found, showing "No thumbnails found" message');
    } else {
        const htmlContent = results.map(result => `
            <div class="thumbnail-result" onclick="selectVideoThumbnailResult('${result.url}')">
                <img src="${result.url}" alt="${result.title || 'Thumbnail'}" 
                     style="max-width: 150px; max-height: 150px; cursor: pointer;"
                     onerror="this.style.display='none'">
                <div class="result-info">
                    <small>${result.source} - ${result.quality || 'Standard'}</small>
                </div>
            </div>
        `).join('');
        
        console.log('Generated HTML content:', htmlContent);
        grid.innerHTML = htmlContent;
        console.log('Grid innerHTML set to:', grid.innerHTML);
    }
    
    resultsContainer.style.display = 'block';
    resultsContainer.style.visibility = 'visible';
    resultsContainer.style.opacity = '1';
    
    // Ensure the grid is also visible
    grid.style.display = 'block';
    grid.style.visibility = 'visible';
    
    console.log('Results container display set to block');
    console.log('Results container final style:', resultsContainer.style.cssText);
    console.log('Results container computed style:', window.getComputedStyle(resultsContainer).display);
    console.log('Grid final style:', grid.style.cssText);
    
    // Show the refresh button once results are displayed
    document.getElementById('videoThumbnailRefreshBtn').style.display = 'inline-block';
}

function selectVideoThumbnailResult(url) {
    // Update the URL input and preview
    document.getElementById('videoThumbnailUrlInput').value = url;
    previewVideoUrlImage();
    
    // Automatically upload the selected thumbnail
    uploadVideoFromUrl();
    
    // Switch back to the URL tab to show the selection
    switchVideoUploadTab('url');
}

function refreshVideoThumbnailSearch() {
    if (!currentVideoThumbnailId) {
        showError('No video selected for thumbnail refresh');
        return;
    }
    
    // Clear current results
    const resultsContainer = document.getElementById('videoThumbnailSearchResults');
    const grid = document.getElementById('videoThumbnailResultsGrid');
    
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
    
    if (grid) {
        grid.innerHTML = '<div class="loading-placeholder">Refreshing search results...</div>';
    }
    
    // Hide refresh button during refresh
    document.getElementById('videoThumbnailRefreshBtn').style.display = 'none';
    
    // Trigger a new search with current settings
    searchVideoThumbnails();
}

function deleteVideoThumbnail() {
    if (!confirm('Are you sure you want to delete this thumbnail?')) {
        return;
    }
    
    fetch(`/api/videos/${currentVideoThumbnailId}/thumbnail`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'remove'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError('Failed to delete thumbnail: ' + data.error);
        } else {
            showSuccess('Thumbnail deleted successfully');
            loadVideoThumbnailInfo();
            refreshVideoDisplayThumbnail();
            
            // Clear the thumbnail URL field in the edit form
            document.getElementById('videoThumbnailUrl').value = '';
        }
    })
    .catch(error => {
        console.error('Error deleting thumbnail:', error);
        showError('Failed to delete thumbnail');
    });
}

function replaceVideoThumbnail() {
    // Switch to manual upload tab for replacement
    switchVideoUploadTab('manual');
}

function cropVideoThumbnail() {
    if (!currentVideoThumbnailId) {
        showError('No video selected for cropping');
        return;
    }
    
    // Load the current thumbnail image
    const thumbnailImg = document.getElementById('currentVideoThumbnailImg');
    if (!thumbnailImg.src || thumbnailImg.style.display === 'none') {
        showError('No thumbnail available to crop');
        return;
    }
    
    // Open crop modal
    document.getElementById('thumbnailCropModal').style.display = 'block';
    
    // Initialize cropping interface
    initializeCropInterface(thumbnailImg.src);
}

function closeThumbnailCropModal() {
    document.getElementById('thumbnailCropModal').style.display = 'none';
    // Clean up crop interface
    if (window.cropImage) {
        window.cropImage = null;
    }
}

// Advanced Cropping Functions
let cropImage = null;
let cropSelection = { x: 0, y: 0, width: 100, height: 100 };
let cropAspectRatio = 0; // 0 = free form
let isDragging = false;
let dragStart = { x: 0, y: 0 };
let dragMode = 'move'; // 'move' or resize direction

function initializeCropInterface(imageSrc) {
    const canvas = document.getElementById('cropCanvas');
    const ctx = canvas.getContext('2d');
    
    // Load image
    cropImage = new Image();
    cropImage.crossOrigin = 'anonymous';
    cropImage.onload = function() {
        // Set canvas size
        const maxWidth = 600;
        const maxHeight = 400;
        const ratio = Math.min(maxWidth / cropImage.width, maxHeight / cropImage.height);
        
        canvas.width = cropImage.width * ratio;
        canvas.height = cropImage.height * ratio;
        
        // Draw image
        ctx.drawImage(cropImage, 0, 0, canvas.width, canvas.height);
        
        // Initialize crop selection (center 50% of image)
        const margin = 0.25;
        cropSelection = {
            x: canvas.width * margin,
            y: canvas.height * margin,
            width: canvas.width * (1 - 2 * margin),
            height: canvas.height * (1 - 2 * margin)
        };
        
        // Setup crop overlay
        setupCropOverlay();
        updateCropPreview();
        updateCropInputs();
    };
    
    cropImage.src = imageSrc;
}

function setupCropOverlay() {
    const canvas = document.getElementById('cropCanvas');
    const overlay = document.getElementById('cropOverlay');
    const selection = document.getElementById('cropSelection');
    
    // Position overlay to match canvas
    const rect = canvas.getBoundingClientRect();
    overlay.style.width = rect.width + 'px';
    overlay.style.height = rect.height + 'px';
    
    // Position selection
    updateCropSelectionDisplay();
    
    // Add event listeners
    selection.addEventListener('mousedown', handleCropMouseDown);
    document.addEventListener('mousemove', handleCropMouseMove);
    document.addEventListener('mouseup', handleCropMouseUp);
    
    // Add handle event listeners
    document.querySelectorAll('.crop-handle').forEach(handle => {
        handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            dragMode = handle.dataset.direction;
            isDragging = true;
            dragStart = { x: e.clientX, y: e.clientY };
        });
    });
}

function updateCropSelectionDisplay() {
    const selection = document.getElementById('cropSelection');
    const canvas = document.getElementById('cropCanvas');
    const canvasRect = canvas.getBoundingClientRect();
    
    const scaleX = canvasRect.width / canvas.width;
    const scaleY = canvasRect.height / canvas.height;
    
    selection.style.left = (cropSelection.x * scaleX) + 'px';
    selection.style.top = (cropSelection.y * scaleY) + 'px';
    selection.style.width = (cropSelection.width * scaleX) + 'px';
    selection.style.height = (cropSelection.height * scaleY) + 'px';
}

function handleCropMouseDown(e) {
    if (!e.target.classList.contains('crop-handle')) {
        dragMode = 'move';
        isDragging = true;
        dragStart = { x: e.clientX, y: e.clientY };
    }
}

function handleCropMouseMove(e) {
    if (!isDragging) return;
    
    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;
    const canvas = document.getElementById('cropCanvas');
    const canvasRect = canvas.getBoundingClientRect();
    
    // Convert screen coordinates to canvas coordinates
    const scaleX = canvas.width / canvasRect.width;
    const scaleY = canvas.height / canvasRect.height;
    const scaledDeltaX = deltaX * scaleX;
    const scaledDeltaY = deltaY * scaleY;
    
    let newSelection = { ...cropSelection };
    
    switch (dragMode) {
        case 'move':
            newSelection.x += scaledDeltaX;
            newSelection.y += scaledDeltaY;
            break;
        case 'nw':
            newSelection.x += scaledDeltaX;
            newSelection.y += scaledDeltaY;
            newSelection.width -= scaledDeltaX;
            newSelection.height -= scaledDeltaY;
            break;
        case 'ne':
            newSelection.y += scaledDeltaY;
            newSelection.width += scaledDeltaX;
            newSelection.height -= scaledDeltaY;
            break;
        case 'sw':
            newSelection.x += scaledDeltaX;
            newSelection.width -= scaledDeltaX;
            newSelection.height += scaledDeltaY;
            break;
        case 'se':
            newSelection.width += scaledDeltaX;
            newSelection.height += scaledDeltaY;
            break;
        case 'n':
            newSelection.y += scaledDeltaY;
            newSelection.height -= scaledDeltaY;
            break;
        case 's':
            newSelection.height += scaledDeltaY;
            break;
        case 'e':
            newSelection.width += scaledDeltaX;
            break;
        case 'w':
            newSelection.x += scaledDeltaX;
            newSelection.width -= scaledDeltaX;
            break;
    }
    
    // Apply aspect ratio constraint
    if (cropAspectRatio > 0) {
        if (dragMode.includes('e') || dragMode.includes('w')) {
            newSelection.height = newSelection.width / cropAspectRatio;
        } else if (dragMode.includes('n') || dragMode.includes('s')) {
            newSelection.width = newSelection.height * cropAspectRatio;
        }
    }
    
    // Constrain to canvas bounds
    newSelection.x = Math.max(0, Math.min(newSelection.x, canvas.width - newSelection.width));
    newSelection.y = Math.max(0, Math.min(newSelection.y, canvas.height - newSelection.height));
    newSelection.width = Math.max(10, Math.min(newSelection.width, canvas.width - newSelection.x));
    newSelection.height = Math.max(10, Math.min(newSelection.height, canvas.height - newSelection.y));
    
    cropSelection = newSelection;
    updateCropSelectionDisplay();
    updateCropPreview();
    updateCropInputs();
    
    dragStart = { x: e.clientX, y: e.clientY };
}

function handleCropMouseUp() {
    isDragging = false;
    dragMode = 'move';
}

function setCropAspectRatio(ratio) {
    cropAspectRatio = ratio;
    
    if (ratio > 0) {
        // Adjust current selection to match aspect ratio
        const centerX = cropSelection.x + cropSelection.width / 2;
        const centerY = cropSelection.y + cropSelection.height / 2;
        
        if (cropSelection.width / cropSelection.height > ratio) {
            // Too wide, adjust width
            cropSelection.width = cropSelection.height * ratio;
        } else {
            // Too tall, adjust height
            cropSelection.height = cropSelection.width / ratio;
        }
        
        // Re-center
        cropSelection.x = centerX - cropSelection.width / 2;
        cropSelection.y = centerY - cropSelection.height / 2;
        
        // Constrain to canvas
        const canvas = document.getElementById('cropCanvas');
        cropSelection.x = Math.max(0, Math.min(cropSelection.x, canvas.width - cropSelection.width));
        cropSelection.y = Math.max(0, Math.min(cropSelection.y, canvas.height - cropSelection.height));
        
        updateCropSelectionDisplay();
        updateCropPreview();
        updateCropInputs();
    }
}

function updateCropFromInput() {
    const canvas = document.getElementById('cropCanvas');
    const width = parseInt(document.getElementById('cropWidth').value) || cropSelection.width;
    const height = parseInt(document.getElementById('cropHeight').value) || cropSelection.height;
    const x = parseInt(document.getElementById('cropX').value) || cropSelection.x;
    const y = parseInt(document.getElementById('cropY').value) || cropSelection.y;
    
    cropSelection = {
        x: Math.max(0, Math.min(x, canvas.width - width)),
        y: Math.max(0, Math.min(y, canvas.height - height)),
        width: Math.max(10, Math.min(width, canvas.width)),
        height: Math.max(10, Math.min(height, canvas.height))
    };
    
    updateCropSelectionDisplay();
    updateCropPreview();
}

function updateCropInputs() {
    document.getElementById('cropWidth').value = Math.round(cropSelection.width);
    document.getElementById('cropHeight').value = Math.round(cropSelection.height);
    document.getElementById('cropX').value = Math.round(cropSelection.x);
    document.getElementById('cropY').value = Math.round(cropSelection.y);
}

function updateCropPreview() {
    if (!cropImage) return;
    
    const previewCanvas = document.getElementById('cropPreviewCanvas');
    const previewCtx = previewCanvas.getContext('2d');
    const canvas = document.getElementById('cropCanvas');
    
    // Calculate scale factors
    const scaleX = cropImage.width / canvas.width;
    const scaleY = cropImage.height / canvas.height;
    
    // Set preview canvas size
    previewCanvas.width = cropSelection.width;
    previewCanvas.height = cropSelection.height;
    
    // Apply image effects
    const brightness = document.getElementById('brightnessSlider').value;
    const contrast = document.getElementById('contrastSlider').value;
    const saturation = document.getElementById('saturationSlider').value;
    const blur = document.getElementById('blurSlider').value;
    
    previewCtx.filter = `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%) blur(${blur}px)`;
    
    // Draw cropped image
    previewCtx.drawImage(
        cropImage,
        cropSelection.x * scaleX, cropSelection.y * scaleY,
        cropSelection.width * scaleX, cropSelection.height * scaleY,
        0, 0,
        cropSelection.width, cropSelection.height
    );
    
    // Update preview info
    document.getElementById('previewSize').textContent = `${Math.round(cropSelection.width)}x${Math.round(cropSelection.height)}`;
    document.getElementById('previewAspectRatio').textContent = `${Math.round(cropSelection.width / cropSelection.height * 100) / 100}:1`;
    
    // Estimate file size (rough approximation)
    const pixels = cropSelection.width * cropSelection.height;
    const estimatedSize = Math.round(pixels * 3 / 1024); // Rough JPEG estimate
    document.getElementById('previewFileSize').textContent = `~${estimatedSize}KB`;
    
    // Update slider value displays
    document.getElementById('brightnessValue').textContent = brightness + '%';
    document.getElementById('contrastValue').textContent = contrast + '%';
    document.getElementById('saturationValue').textContent = saturation + '%';
    document.getElementById('blurValue').textContent = blur + 'px';
}

function resetImageEffects() {
    document.getElementById('brightnessSlider').value = 100;
    document.getElementById('contrastSlider').value = 100;
    document.getElementById('saturationSlider').value = 100;
    document.getElementById('blurSlider').value = 0;
    updateCropPreview();
}

function applyImageFilter(filterType) {
    const brightness = document.getElementById('brightnessSlider');
    const contrast = document.getElementById('contrastSlider');
    const saturation = document.getElementById('saturationSlider');
    
    switch (filterType) {
        case 'grayscale':
            saturation.value = 0;
            break;
        case 'sepia':
            brightness.value = 110;
            contrast.value = 90;
            saturation.value = 180;
            break;
        case 'invert':
            brightness.value = 0;
            contrast.value = 200;
            break;
    }
    
    updateCropPreview();
}

function resetCrop() {
    const canvas = document.getElementById('cropCanvas');
    const margin = 0.25;
    cropSelection = {
        x: canvas.width * margin,
        y: canvas.height * margin,
        width: canvas.width * (1 - 2 * margin),
        height: canvas.height * (1 - 2 * margin)
    };
    
    cropAspectRatio = 0;
    resetImageEffects();
    updateCropSelectionDisplay();
    updateCropPreview();
    updateCropInputs();
}

function applyCrop() {
    updateCropPreview();
    showSuccess('Crop applied to preview');
}

function saveCroppedThumbnail() {
    if (!cropImage || !currentVideoThumbnailId) {
        showError('No image or video selected');
        return;
    }
    
    // Convert preview canvas to blob
    const previewCanvas = document.getElementById('cropPreviewCanvas');
    previewCanvas.toBlob((blob) => {
        if (!blob) {
            showError('Failed to generate cropped image');
            return;
        }
        
        // Create form data
        const formData = new FormData();
        formData.append('file', blob, 'cropped_thumbnail.jpg');
        
        // Upload cropped thumbnail
        fetch(`/api/videos/${currentVideoThumbnailId}/thumbnail/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError('Failed to save cropped thumbnail: ' + data.error);
            } else {
                showSuccess('Cropped thumbnail saved successfully');
                closeThumbnailCropModal();
                loadVideoThumbnailInfo();
                refreshVideoDisplayThumbnail();
            }
        })
        .catch(error => {
            console.error('Error saving cropped thumbnail:', error);
            showError('Error saving cropped thumbnail');
        });
    }, 'image/jpeg', 0.9);
}

function refreshVideoDisplayThumbnail() {
    // Refresh the thumbnail in the main video grid
    const videoCard = document.querySelector(`[data-video-id="${currentVideoThumbnailId}"]`);
    if (videoCard) {
        const thumbnailImg = videoCard.querySelector('img');
        if (thumbnailImg) {
            // Update with cache busting
            thumbnailImg.src = `/api/videos/${currentVideoThumbnailId}/thumbnail?t=${Date.now()}`;
        }
    }
    
    // Also refresh the video list if we're currently searching
    if (window.searchActive) {
        performSearch();
    } else {
        loadVideos();
    }
}

// Close thumbnail modal when clicking outside
window.addEventListener('click', function(event) {
    const thumbnailModal = document.getElementById('videoThumbnailModal');
    if (event.target === thumbnailModal) {
        closeVideoThumbnailModal();
    }
});

// Enhanced Bulk Actions Functions
function toggleBulkActionsPanel() {
    const panel = document.getElementById('bulkActionsPanel');
    if (panel.style.display === 'none' || panel.style.display === '') {
        panel.style.display = 'block';
        updateBulkButtonStates();
    } else {
        panel.style.display = 'none';
    }
}

function closeBulkActionsPanel() {
    document.getElementById('bulkActionsPanel').style.display = 'none';
}

function switchBulkTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Deactivate all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => button.classList.remove('active'));
    
    // Show selected tab content
    document.getElementById(`bulk${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`).classList.add('active');
    
    // Activate selected tab button
    event.target.classList.add('active');
    
    updateBulkButtonStates();
}

function updateBulkButtonStates() {
    const selectedCount = document.querySelectorAll('.video-checkbox:checked').length;
    const bulkButtons = document.querySelectorAll('.bulk-btn');
    
    bulkButtons.forEach(button => {
        button.disabled = selectedCount === 0;
    });
}

function getSelectedVideoIds() {
    const selectedCheckboxes = document.querySelectorAll('.video-checkbox:checked');
    return Array.from(selectedCheckboxes).map(checkbox => parseInt(checkbox.value));
}

function showBulkProgress(text) {
    const progressDiv = document.getElementById('bulkProgress');
    const progressText = document.getElementById('bulkProgressText');
    const progressFill = document.getElementById('bulkProgressFill');
    
    progressText.textContent = text;
    progressFill.style.width = '0%';
    progressDiv.style.display = 'block';
}

function updateBulkProgress(percentage, text) {
    const progressText = document.getElementById('bulkProgressText');
    const progressFill = document.getElementById('bulkProgressFill');
    
    if (text) progressText.textContent = text;
    progressFill.style.width = percentage + '%';
}

function hideBulkProgress() {
    document.getElementById('bulkProgress').style.display = 'none';
}

// Bulk Actions Functions
function bulkDownloadSelected() {
    const videoIds = getSelectedVideoIds();
    if (videoIds.length === 0) {
        showError('No videos selected');
        return;
    }
    
    showBulkProgress('Initiating downloads...');
    
    fetch('/api/videos/bulk/download', {
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
        hideBulkProgress();
        if (data.error) {
            showError('Error initiating downloads: ' + data.error);
        } else {
            showSuccess(`Successfully initiated ${data.queued_count} downloads`);
            if (data.failed_count > 0) {
                showWarning(`Failed to queue ${data.failed_count} videos`);
            }
            loadVideos();
        }
    })
    .catch(error => {
        hideBulkProgress();
        console.error('Error:', error);
        showError('Error initiating bulk downloads');
    });
}

function bulkDeleteSelected() {
    const videoIds = getSelectedVideoIds();
    if (videoIds.length === 0) {
        showError('No videos selected');
        return;
    }
    
    const confirmed = confirm(`Are you sure you want to delete ${videoIds.length} selected video(s)?\n\nThis action cannot be undone.`);
    
    if (confirmed) {
        showBulkProgress('Deleting videos...');
        
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
            hideBulkProgress();
            if (data.deleted_count > 0) {
                showSuccess(`Successfully deleted ${data.deleted_count} video(s)`);
            }
            if (data.failed_count > 0) {
                showWarning(`Failed to delete ${data.failed_count} video(s)`);
            }
            loadVideos();
            updateSelectedCount();
        })
        .catch(error => {
            hideBulkProgress();
            console.error('Error:', error);
            showError('Error deleting videos');
        });
    }
}

function bulkRefreshMetadata() {
    const videoIds = getSelectedVideoIds();
    if (videoIds.length === 0) {
        showError('No videos selected');
        return;
    }
    
    const confirmed = confirm(`Refresh metadata from IMVDb for ${videoIds.length} selected video(s)? This will update year, directors, producers, and thumbnail information.`);
    
    if (confirmed) {
        showBulkProgress('Refreshing metadata...');
        
        fetch('/api/videos/bulk/refresh-metadata', {
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
            hideBulkProgress();
            if (data.updated_count > 0) {
                showSuccess(`Successfully refreshed metadata for ${data.updated_count} video(s)`);
            }
            if (data.failed_count > 0) {
                showWarning(`Failed to refresh metadata for ${data.failed_count} video(s)`);
            }
            if (data.skipped_count > 0) {
                showInfo(`Skipped ${data.skipped_count} video(s) - no IMVDb ID available`);
            }
            loadVideos();
            updateSelectedCount();
        })
        .catch(error => {
            hideBulkProgress();
            console.error('Error:', error);
            showError('Error refreshing metadata');
        });
    }
}

function bulkSetStatus(status) {
    const videoIds = getSelectedVideoIds();
    if (videoIds.length === 0) {
        showError('No videos selected');
        return;
    }
    
    showBulkProgress(`Setting status to ${status}...`);
    
    fetch('/api/videos/bulk/status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_ids: videoIds,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        hideBulkProgress();
        if (data.error) {
            showError('Error updating status: ' + data.error);
        } else {
            showSuccess(`Successfully updated status for ${data.updated_count} videos`);
            loadVideos();
        }
    })
    .catch(error => {
        hideBulkProgress();
        console.error('Error:', error);
        showError('Error updating video status');
    });
}

function applyBulkEdit() {
    const videoIds = getSelectedVideoIds();
    if (videoIds.length === 0) {
        showError('No videos selected');
        return;
    }
    
    const updates = {};
    
    // Collect changes
    const artistChange = document.getElementById('bulkArtistChange').value.trim();
    const yearChange = document.getElementById('bulkYearChange').value.trim();
    const statusChange = document.getElementById('bulkStatusChange').value;
    const priorityChange = document.getElementById('bulkPriorityChange').value;
    
    if (artistChange) updates.artist_name = artistChange;
    if (yearChange) updates.year = parseInt(yearChange);
    if (statusChange) updates.status = statusChange;
    if (priorityChange) updates.priority = priorityChange;
    
    if (Object.keys(updates).length === 0) {
        showError('No changes specified');
        return;
    }
    
    showBulkProgress('Applying bulk edits...');
    
    fetch('/api/videos/bulk/edit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_ids: videoIds,
            updates: updates
        })
    })
    .then(response => response.json())
    .then(data => {
        hideBulkProgress();
        if (data.error) {
            showError('Error applying bulk edits: ' + data.error);
        } else {
            showSuccess(`Successfully updated ${data.updated_count} videos`);
            loadVideos();
            
            // Clear form
            document.getElementById('bulkArtistChange').value = '';
            document.getElementById('bulkYearChange').value = '';
            document.getElementById('bulkStatusChange').value = '';
            document.getElementById('bulkPriorityChange').value = '';
        }
    })
    .catch(error => {
        hideBulkProgress();
        console.error('Error:', error);
        showError('Error applying bulk edits');
    });
}

function bulkOrganizeFiles() {
    const videoIds = getSelectedVideoIds();
    if (videoIds.length === 0) {
        showError('No videos selected');
        return;
    }
    
    const options = {
        create_folders: document.getElementById('bulkCreateFolders').checked,
        rename_files: document.getElementById('bulkRenameFiles').checked,
        remove_duplicates: document.getElementById('bulkRemoveDuplicates').checked
    };
    
    showBulkProgress('Organizing files...');
    
    fetch('/api/videos/bulk/organize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_ids: videoIds,
            options: options
        })
    })
    .then(response => response.json())
    .then(data => {
        hideBulkProgress();
        if (data.error) {
            showError('Error organizing files: ' + data.error);
        } else {
            showSuccess(`Successfully organized ${data.organized_count} files`);
            if (data.failed_count > 0) {
                showWarning(`Failed to organize ${data.failed_count} files`);
            }
            loadVideos();
        }
    })
    .catch(error => {
        hideBulkProgress();
        console.error('Error:', error);
        showError('Error organizing files');
    });
}

// Selection helper functions
function selectByStatus() {
    const status = prompt('Select videos by status (WANTED, DOWNLOADING, DOWNLOADED, IGNORED, FAILED):');
    if (!status) return;
    
    const videoCards = document.querySelectorAll('.video-card');
    videoCards.forEach(card => {
        const statusText = card.querySelector('.video-info p:nth-child(3)').textContent;
        const checkbox = card.querySelector('.video-checkbox');
        
        if (statusText.includes(status.toUpperCase())) {
            checkbox.checked = true;
        }
    });
    
    updateSelectedCount();
}

function selectByArtist() {
    const artist = prompt('Select videos by artist:');
    if (!artist) return;
    
    const videoCards = document.querySelectorAll('.video-card');
    videoCards.forEach(card => {
        const artistText = card.querySelector('.video-info p:nth-child(2)').textContent;
        const checkbox = card.querySelector('.video-checkbox');
        
        if (artistText.toLowerCase().includes(artist.toLowerCase())) {
            checkbox.checked = true;
        }
    });
    
    updateSelectedCount();
}

function selectByYear() {
    const year = prompt('Select videos by year:');
    if (!year) return;
    
    const videoCards = document.querySelectorAll('.video-card');
    videoCards.forEach(card => {
        const yearElement = card.querySelector('.video-info p:nth-child(4)');
        const checkbox = card.querySelector('.video-checkbox');
        
        if (yearElement && yearElement.textContent.includes(year)) {
            checkbox.checked = true;
        }
    });
    
    updateSelectedCount();
}

function deselectAll() {
    const checkboxes = document.querySelectorAll('.video-checkbox');
    checkboxes.forEach(checkbox => checkbox.checked = false);
    document.getElementById('selectAllVideos').checked = false;
    updateSelectedCount();
}

// Update the existing updateSelectedCount function to work with new bulk actions
function updateSelectedCount() {
    const selectedCheckboxes = document.querySelectorAll('.video-checkbox:checked');
    const count = selectedCheckboxes.length;
    
    document.getElementById('selectedCount').textContent = count;
    
    // Update legacy delete button
    const deleteBtn = document.getElementById('deleteSelectedBtn');
    if (deleteBtn) {
        deleteBtn.disabled = count === 0;
    }
    
    // Update bulk action buttons
    updateBulkButtonStates();
    
    // Update select all checkbox state
    const selectAllCheckbox = document.getElementById('selectAllVideos');
    const videoCheckboxes = document.querySelectorAll('.video-checkbox');
    
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

// Close bulk actions panel when clicking outside
window.addEventListener('click', function(event) {
    const bulkPanel = document.getElementById('bulkActionsPanel');
    const bulkButton = document.getElementById('bulkActionsToggle');
    
    if (event.target === bulkPanel) {
        closeBulkActionsPanel();
    }
});

// Pagination Functions
function updatePaginationControls() {
    // Show pagination controls if we have videos
    const showPagination = totalVideos > 0;
    document.getElementById('topPagination').style.display = showPagination ? 'flex' : 'none';
    document.getElementById('bottomPagination').style.display = showPagination ? 'flex' : 'none';
    
    if (!showPagination) return;
    
    // Update pagination info
    const startIndex = ((currentPage - 1) * pageSize) + 1;
    const endIndex = Math.min(currentPage * pageSize, totalVideos);
    const infoText = `Showing ${startIndex}-${endIndex} of ${totalVideos} videos`;
    
    const countInfo = document.getElementById('videoCountInfo');
    const countInfoBottom = document.getElementById('videoCountInfoBottom');
    if (countInfo) countInfo.textContent = infoText;
    if (countInfoBottom) countInfoBottom.textContent = infoText;
    
    // Update page inputs
    const pageInputTop = document.getElementById('pageInputTop');
    const pageInputBottom = document.getElementById('pageInputBottom');
    if (pageInputTop) pageInputTop.value = currentPage;
    if (pageInputBottom) pageInputBottom.value = currentPage;
    const totalPagesTop = document.getElementById('topTotalPages');
    const totalPagesBottom = document.getElementById('bottomTotalPages');
    const currentPageSizeEl = document.getElementById('currentPageSize');
    if (totalPagesTop) totalPagesTop.textContent = totalPages;
    if (totalPagesBottom) totalPagesBottom.textContent = totalPages;
    if (currentPageSizeEl) currentPageSizeEl.textContent = pageSize;
    
    // Update button states
    const hasPrevious = currentPage > 1;
    const hasNext = currentPage < totalPages;
    
    // Update pagination buttons with null checks
    const prevBtnTop = document.getElementById('topPrevBtn');
    const prevBtnBottom = document.getElementById('bottomPrevBtn');
    const nextBtnTop = document.getElementById('topNextBtn');
    const nextBtnBottom = document.getElementById('bottomNextBtn');
    const firstBtnTop = document.getElementById('topFirstBtn');
    const firstBtnBottom = document.getElementById('bottomFirstBtn');
    const lastBtnTop = document.getElementById('topLastBtn');
    const lastBtnBottom = document.getElementById('bottomLastBtn');
    
    if (prevBtnTop) prevBtnTop.disabled = !hasPrevious;
    if (prevBtnBottom) prevBtnBottom.disabled = !hasPrevious;
    if (nextBtnTop) nextBtnTop.disabled = !hasNext;
    if (nextBtnBottom) nextBtnBottom.disabled = !hasNext;
    if (firstBtnTop) firstBtnTop.disabled = !hasPrevious;
    if (firstBtnBottom) firstBtnBottom.disabled = !hasPrevious;
    if (lastBtnTop) lastBtnTop.disabled = !hasNext;
    if (lastBtnBottom) lastBtnBottom.disabled = !hasNext;
    
    // Update page size selector
    const pageSizeSelect = document.getElementById('topPageSize');
    if (pageSizeSelect) pageSizeSelect.value = pageSize;
}

function nextPage() {
    if (currentPage < totalPages) {
        loadVideos(currentPage + 1, pageSize);
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function previousPage() {
    if (currentPage > 1) {
        loadVideos(currentPage - 1, pageSize);
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function goToPage(page) {
    const pageNum = parseInt(page);
    if (pageNum >= 1 && pageNum <= totalPages && pageNum !== currentPage) {
        loadVideos(pageNum, pageSize);
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        // Reset invalid input
        const pageInputTop = document.getElementById('pageInputTop');
        const pageInputBottom = document.getElementById('pageInputBottom');
        if (pageInputTop) pageInputTop.value = currentPage;
        if (pageInputBottom) pageInputBottom.value = currentPage;
    }
}

function changePageSize(newSize) {
    const size = parseInt(newSize);
    if (size !== pageSize) {
        pageSize = size;
        // Reset to page 1 when changing page size
        loadVideos(1, pageSize, true);
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Override existing loadVideos calls to use pagination
const originalLoadVideos = loadVideos;
window.refreshVideosWithPagination = function() {
    loadVideos(currentPage, pageSize);
};

// Update other functions to use the new pagination-aware reload
function refreshVideoList() {
    loadVideos(currentPage, pageSize);
}