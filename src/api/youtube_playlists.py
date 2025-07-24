"""
YouTube Playlist Monitoring API endpoints
"""

import requests
from flask import Blueprint, request, jsonify
from src.services.youtube_playlist_service import youtube_playlist_service
from src.utils.logger import get_logger

youtube_playlists_bp = Blueprint('youtube_playlists', __name__, url_prefix='/youtube/playlists')
logger = get_logger('mvidarr.api.youtube_playlists')

@youtube_playlists_bp.route('/', methods=['GET'])
def get_monitored_playlists():
    """Get all monitored playlists"""
    try:
        playlists = youtube_playlist_service.get_monitored_playlists()
        return jsonify({
            'playlists': playlists,
            'count': len(playlists)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get monitored playlists: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/', methods=['POST'])
def create_playlist_monitor():
    """Create a new playlist monitor"""
    try:
        data = request.get_json()
        
        if not data or 'playlist_url' not in data:
            return jsonify({'error': 'playlist_url is required'}), 400
        
        playlist_url = data['playlist_url']
        name = data.get('name')
        auto_download = data.get('auto_download', True)
        quality = data.get('quality', '720p')
        keywords = data.get('keywords', [])
        
        # Validate YouTube API key
        if not youtube_playlist_service.api_key:
            return jsonify({
                'error': 'YouTube API key not configured. Please set YOUTUBE_API_KEY environment variable.'
            }), 400
        
        result = youtube_playlist_service.create_playlist_monitor(
            playlist_url=playlist_url,
            name=name,
            auto_download=auto_download,
            quality=quality,
            keywords=keywords
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Failed to create playlist monitor: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/<int:monitor_id>', methods=['GET'])
def get_playlist_monitor(monitor_id):
    """Get a specific playlist monitor"""
    try:
        playlists = youtube_playlist_service.get_monitored_playlists()
        playlist = next((p for p in playlists if p['id'] == monitor_id), None)
        
        if not playlist:
            return jsonify({'error': 'Playlist monitor not found'}), 404
        
        return jsonify(playlist), 200
        
    except Exception as e:
        logger.error(f"Failed to get playlist monitor: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/<int:monitor_id>', methods=['PUT'])
def update_playlist_monitor(monitor_id):
    """Update playlist monitor settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Filter allowed updates
        allowed_fields = ['name', 'auto_download', 'quality', 'keywords']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        result = youtube_playlist_service.update_playlist_monitor(monitor_id, updates)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to update playlist monitor: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/<int:monitor_id>', methods=['DELETE'])
def delete_playlist_monitor(monitor_id):
    """Delete playlist monitor"""
    try:
        delete_videos = request.args.get('delete_videos', 'false').lower() == 'true'
        
        result = youtube_playlist_service.delete_playlist_monitor(monitor_id, delete_videos)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to delete playlist monitor: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/<int:monitor_id>/sync', methods=['POST'])
def sync_playlist(monitor_id):
    """Sync a specific playlist"""
    try:
        # Get playlist ID from monitor
        playlists = youtube_playlist_service.get_monitored_playlists()
        playlist = next((p for p in playlists if p['id'] == monitor_id), None)
        
        if not playlist:
            return jsonify({'error': 'Playlist monitor not found'}), 404
        
        result = youtube_playlist_service.sync_playlist_videos(playlist['playlist_id'])
        
        return jsonify({
            'success': True,
            'message': f"Synced playlist '{playlist['name']}'",
            'results': result
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to sync playlist: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/sync-all', methods=['POST'])
def sync_all_playlists():
    """Sync all monitored playlists"""
    try:
        result = youtube_playlist_service.sync_all_playlists()
        
        return jsonify({
            'success': True,
            'message': f"Synced {result['synced_playlists']} playlists with {result['total_new_videos']} new videos",
            'results': result
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to sync all playlists: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/extract-id', methods=['POST'])
def extract_playlist_id():
    """Extract playlist ID from YouTube URL"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'url is required'}), 400
        
        playlist_id = youtube_playlist_service.extract_playlist_id(data['url'])
        
        if not playlist_id:
            return jsonify({'error': 'Invalid YouTube playlist URL'}), 400
        
        return jsonify({
            'playlist_id': playlist_id,
            'valid': True
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to extract playlist ID: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/info', methods=['POST'])
def get_playlist_info():
    """Get playlist information without creating monitor"""
    try:
        data = request.get_json()
        
        if not data or 'playlist_url' not in data:
            return jsonify({'error': 'playlist_url is required'}), 400
        
        if not youtube_playlist_service.api_key:
            return jsonify({
                'error': 'YouTube API key not configured'
            }), 400
        
        playlist_id = youtube_playlist_service.extract_playlist_id(data['playlist_url'])
        
        if not playlist_id:
            return jsonify({'error': 'Invalid YouTube playlist URL'}), 400
        
        playlist_info = youtube_playlist_service.get_playlist_info(playlist_id)
        
        if not playlist_info:
            return jsonify({'error': 'Playlist not found or is private'}), 404
        
        return jsonify({
            'playlist_info': playlist_info,
            'valid': True
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get playlist info: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/preview', methods=['POST'])
def preview_playlist_videos():
    """Preview videos in a playlist without creating monitor"""
    try:
        data = request.get_json()
        
        if not data or 'playlist_url' not in data:
            return jsonify({'error': 'playlist_url is required'}), 400
        
        if not youtube_playlist_service.api_key:
            return jsonify({
                'error': 'YouTube API key not configured'
            }), 400
        
        playlist_id = youtube_playlist_service.extract_playlist_id(data['playlist_url'])
        
        if not playlist_id:
            return jsonify({'error': 'Invalid YouTube playlist URL'}), 400
        
        max_results = min(int(data.get('max_results', 20)), 50)
        
        # Get playlist info
        playlist_info = youtube_playlist_service.get_playlist_info(playlist_id)
        
        if not playlist_info:
            return jsonify({'error': 'Playlist not found or is private'}), 404
        
        # Get videos
        videos = youtube_playlist_service.get_playlist_videos(playlist_id, max_results)
        
        # Get video details
        video_ids = [v['video_id'] for v in videos if v['video_id']]
        video_details = youtube_playlist_service.get_video_details(video_ids)
        
        # Combine video data with details
        for video in videos:
            video_id = video['video_id']
            if video_id in video_details:
                video.update(video_details[video_id])
        
        return jsonify({
            'playlist_info': playlist_info,
            'videos': videos,
            'video_count': len(videos),
            'total_videos': playlist_info['item_count']
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to preview playlist videos: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/status', methods=['GET'])
def get_youtube_status():
    """Get YouTube integration status"""
    try:
        configured = youtube_playlist_service.api_key is not None
        
        return jsonify({
            'configured': configured,
            'api_key': youtube_playlist_service.api_key[:8] + '...' if configured else None,
            'metube_url': youtube_playlist_service.metube_url
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get YouTube status: {e}")
        return jsonify({'error': str(e)}), 500

@youtube_playlists_bp.route('/test', methods=['POST'])
def test_youtube_integration():
    """Test YouTube API connection"""
    try:
        # Check if API key is configured
        if not youtube_playlist_service.api_key:
            return jsonify({
                'status': 'error',
                'message': 'YouTube API key not configured. Please set youtube_api_key in settings.'
            }), 400
        
        # Test API connection with a simple request
        url = f"{youtube_playlist_service.base_url}/search"
        params = {
            'part': 'snippet',
            'q': 'test',
            'type': 'playlist',
            'maxResults': 1,
            'key': youtube_playlist_service.api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return jsonify({
            'status': 'success',
            'message': 'YouTube API connection successful',
            'api_quota_used': True,
            'response_items': len(data.get('items', []))
        }), 200
        
    except requests.RequestException as e:
        logger.error(f"YouTube API test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'YouTube API connection failed: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"YouTube integration test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'YouTube integration test failed: {str(e)}'
        }), 500

@youtube_playlists_bp.route('/sync', methods=['POST'])
def sync_playlists():
    """Sync all monitored playlists for settings page"""
    try:
        # Check if API key is configured
        if not youtube_playlist_service.api_key:
            return jsonify({
                'success': False,
                'error': 'YouTube API key not configured. Please set youtube_api_key in settings.'
            }), 400
        
        # Sync all playlists
        result = youtube_playlist_service.sync_all_playlists()
        
        return jsonify({
            'success': True,
            'synced_count': result.get('synced_playlists', 0),
            'new_videos': result.get('total_new_videos', 0),
            'message': f"Synced {result.get('synced_playlists', 0)} playlists with {result.get('total_new_videos', 0)} new videos"
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to sync playlists: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500