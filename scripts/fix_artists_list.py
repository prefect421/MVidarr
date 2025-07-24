#!/usr/bin/env python3
"""
Fix Artists List Display Issue
Patches the artists.html template to use basic API instead of advanced search
"""

import re
from pathlib import Path

def patch_artists_template():
    """Patch the artists template to use basic API instead of advanced search"""
    
    template_path = Path(__file__).parent.parent / 'frontend' / 'templates' / 'artists.html'
    
    if not template_path.exists():
        print(f"❌ Artists template not found: {template_path}")
        return False
    
    # Read the current template
    with open(template_path, 'r') as f:
        content = f.read()
    
    print("🔧 Patching artists.html template...")
    
    # Find the loadArtists function and replace the advanced search call with basic API
    # Look for the pattern where it tries advanced search first
    advanced_search_pattern = r"fetch\(`/api/artists/search/advanced\?\${params\}.*?\)\.then"
    
    if re.search(advanced_search_pattern, content):
        print("   Found advanced search pattern - replacing with basic API call")
        
        # Replace the loadArtists function to use basic API directly
        old_function_start = "function loadArtists(page = 1) {"
        old_function_end = "});"
        
        # Find the start and end of the loadArtists function
        start_pos = content.find(old_function_start)
        if start_pos == -1:
            print("❌ Could not find loadArtists function")
            return False
        
        # Find the matching closing brace for the function
        brace_count = 0
        pos = start_pos + len(old_function_start)
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                if brace_count == 0:
                    break
                brace_count -= 1
            pos += 1
        
        if pos >= len(content):
            print("❌ Could not find end of loadArtists function")
            return False
        
        # Extract the full function
        old_function = content[start_pos:pos + 1]
        
        # Create the new simplified function
        new_function = """function loadArtists(page = 1) {
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('per_page', 50);
    
    // Add search term
    const searchTerm = document.getElementById('searchInput').value.trim();
    if (searchTerm) {
        params.append('search', searchTerm);
    }
    
    // Add basic filters
    const monitored = document.getElementById('monitoredFilter').value;
    if (monitored) {
        params.append('monitored', monitored);
    }
    
    const autoDownload = document.getElementById('autoDownloadFilter').value;
    if (autoDownload) {
        params.append('auto_download', autoDownload);
    }
    
    // Add sorting
    const sortBy = document.getElementById('sortBy').value || 'name';
    const sortOrder = document.getElementById('sortOrder').value || 'asc';
    params.append('sort', sortBy);
    params.append('order', sortOrder);
    
    // Clear current results
    const grid = document.getElementById('artists-grid');
    grid.innerHTML = '<div class="loading"><p>Loading artists...</p></div>';
    
    // Fetch from basic artists API
    fetch(`/api/artists/?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.artists && data.artists.length > 0) {
                const artistsHtml = data.artists.map(artist => {
                    const thumbnailUrl = artist.thumbnail_url || artist.thumbnail_path || '/static/placeholder-artist.png';
                    const keywords = Array.isArray(artist.keywords) ? artist.keywords.join(', ') : (artist.keywords || '');
                    const lastDiscovery = artist.last_discovery ? new Date(artist.last_discovery).toLocaleDateString() : 'Never';
                    
                    return `
                        <div class="artist-card" data-artist-id="${artist.id}">
                            <div class="artist-thumbnail">
                                <img src="${thumbnailUrl}" alt="${artist.name}" onerror="this.src='/static/placeholder-artist.png'">
                                <div class="artist-overlay">
                                    <button onclick="viewArtist(${artist.id})" class="btn btn-primary btn-small">View</button>
                                </div>
                            </div>
                            <div class="artist-info">
                                <h3>${artist.name}</h3>
                                <div class="artist-meta">
                                    <span class="status ${artist.monitored ? 'monitored' : 'not-monitored'}">
                                        ${artist.monitored ? 'Monitored' : 'Not Monitored'}
                                    </span>
                                    <span class="auto-download ${artist.auto_download ? 'enabled' : 'disabled'}">
                                        Auto-DL: ${artist.auto_download ? 'On' : 'Off'}
                                    </span>
                                </div>
                                <div class="artist-details">
                                    <small>Keywords: ${keywords || 'None'}</small><br>
                                    <small>Last Discovery: ${lastDiscovery}</small>
                                </div>
                            </div>
                            <div class="artist-actions">
                                <button onclick="toggleArtistSelection(${artist.id})" class="btn btn-secondary btn-small selection-btn">
                                    <span class="select-text">Select</span>
                                    <span class="selected-text" style="display: none;">✓ Selected</span>
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
                
                // Create pagination
                let paginationHtml = '';
                if (data.pages > 1) {
                    paginationHtml = '<div class="pagination">';
                    
                    // Previous button
                    if (data.page > 1) {
                        paginationHtml += `<button onclick="loadArtists(${data.page - 1})" class="btn btn-small">Previous</button>`;
                    }
                    
                    // Page numbers
                    const startPage = Math.max(1, data.page - 2);
                    const endPage = Math.min(data.pages, data.page + 2);
                    
                    for (let i = startPage; i <= endPage; i++) {
                        const active = i === data.page ? 'active' : '';
                        paginationHtml += `<button onclick="loadArtists(${i})" class="btn btn-small ${active}">${i}</button>`;
                    }
                    
                    // Next button
                    if (data.page < data.pages) {
                        paginationHtml += `<button onclick="loadArtists(${data.page + 1})" class="btn btn-small">Next</button>`;
                    }
                    
                    paginationHtml += '</div>';
                }
                
                grid.innerHTML = `
                    <div class="artists-list">
                        ${artistsHtml}
                    </div>
                    ${paginationHtml}
                `;
                
                // Update current page
                currentPage = data.page;
                totalPages = data.pages;
                
            } else {
                grid.innerHTML = '<div class="no-results"><p>No artists found. Try adjusting your search or filters.</p></div>';
            }
        })
        .catch(error => {
            console.error('Error loading artists:', error);
            document.getElementById('artists-grid').innerHTML = '<div class="error-message"><p>Error loading artists. Please try again.</p></div>';
        });
}"""
        
        # Replace the function in the content
        new_content = content.replace(old_function, new_function)
        
        # Write the updated template
        with open(template_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Successfully patched artists.html template")
        print("   - Replaced advanced search with basic API call")
        print("   - Simplified pagination handling")
        print("   - Added proper error handling")
        
        return True
    else:
        print("⚠️  Advanced search pattern not found - template may already be patched")
        return True

def main():
    """Main execution function"""
    
    print("=" * 60)
    print("MVidarr - Fix Artists List Display")
    print("=" * 60)
    
    if patch_artists_template():
        print()
        print("✅ Artists list fix completed successfully!")
        print()
        print("📋 Next steps:")
        print("  1. Restart the application: ./manage.sh restart")
        print("  2. Access the artists page: http://localhost:5000/artists")
        print("  3. Verify the artist 'Willy Nelson' now appears in the list")
        print("  4. Test adding new artists to confirm the fix works")
    else:
        print("❌ Failed to patch artists template!")

if __name__ == "__main__":
    main()