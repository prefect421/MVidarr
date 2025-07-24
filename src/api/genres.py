"""
Genre management API endpoints
"""

from flask import Blueprint, request, jsonify
from src.services.genre_service import genre_service
from src.utils.logger import get_logger

logger = get_logger('mvidarr.api.genres')

genres_bp = Blueprint('genres', __name__)

@genres_bp.route('/genres', methods=['GET'])
def get_all_genres():
    """Get all unique genres from videos and artists"""
    try:
        genres = genre_service.get_all_genres()
        return jsonify(genres), 200
    except Exception as e:
        logger.error(f"Error getting all genres: {e}")
        return jsonify({'error': 'Failed to get genres'}), 500

@genres_bp.route('/genres/videos/<int:video_id>', methods=['GET'])
def get_video_genres(video_id):
    """Get genres for a specific video"""
    try:
        genres = genre_service.get_video_genres(video_id)
        return jsonify({'genres': genres}), 200
    except Exception as e:
        logger.error(f"Error getting video genres: {e}")
        return jsonify({'error': 'Failed to get video genres'}), 500

@genres_bp.route('/genres/videos/<int:video_id>', methods=['PUT'])
def set_video_genres(video_id):
    """Set genres for a specific video"""
    try:
        data = request.get_json()
        genres = data.get('genres', [])
        
        if not isinstance(genres, list):
            return jsonify({'error': 'Genres must be a list'}), 400
        
        success = genre_service.set_video_genres(video_id, genres)
        if success:
            return jsonify({'message': 'Video genres updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update video genres'}), 404
    except Exception as e:
        logger.error(f"Error setting video genres: {e}")
        return jsonify({'error': 'Failed to set video genres'}), 500

@genres_bp.route('/genres/artists/<int:artist_id>', methods=['GET'])
def get_artist_genres(artist_id):
    """Get genres for a specific artist"""
    try:
        genres = genre_service.get_artist_genres(artist_id)
        return jsonify({'genres': genres}), 200
    except Exception as e:
        logger.error(f"Error getting artist genres: {e}")
        return jsonify({'error': 'Failed to get artist genres'}), 500

@genres_bp.route('/genres/artists/update', methods=['POST'])
def update_all_artist_genres():
    """Update all artist genres based on their videos"""
    try:
        result = genre_service.update_all_artist_genres()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error updating all artist genres: {e}")
        return jsonify({'error': 'Failed to update artist genres'}), 500

@genres_bp.route('/genres/<genre>/videos', methods=['GET'])
def get_videos_by_genre(genre):
    """Get videos that match a specific genre"""
    try:
        limit = request.args.get('limit', 50, type=int)
        videos = genre_service.get_videos_by_genre(genre, limit)
        return jsonify({'videos': videos}), 200
    except Exception as e:
        logger.error(f"Error getting videos by genre: {e}")
        return jsonify({'error': 'Failed to get videos by genre'}), 500

@genres_bp.route('/genres/<genre>/artists', methods=['GET'])
def get_artists_by_genre(genre):
    """Get artists that match a specific genre"""
    try:
        limit = request.args.get('limit', 50, type=int)
        artists = genre_service.get_artists_by_genre(genre, limit)
        return jsonify({'artists': artists}), 200
    except Exception as e:
        logger.error(f"Error getting artists by genre: {e}")
        return jsonify({'error': 'Failed to get artists by genre'}), 500

@genres_bp.route('/genres/suggest/videos/<int:video_id>', methods=['GET'])
def suggest_genres_for_video(video_id):
    """Suggest genres for a video based on artist and similar videos"""
    try:
        suggestions = genre_service.suggest_genres_for_video(video_id)
        return jsonify({'suggested_genres': suggestions}), 200
    except Exception as e:
        logger.error(f"Error suggesting genres for video: {e}")
        return jsonify({'error': 'Failed to suggest genres'}), 500