"""
VLC Streaming API endpoints for MVidarr Enhanced
"""

from flask import Blueprint, jsonify, request
from src.database.connection import get_db
from src.database.models import Video
from src.services.vlc_streaming_service import vlc_streaming_service
from src.utils.logger import get_logger
import os

vlc_bp = Blueprint('vlc', __name__, url_prefix='/vlc')
logger = get_logger('mvidarr.api.vlc_streaming')

@vlc_bp.route('/stream/<int:video_id>', methods=['POST'])
def start_video_stream(video_id):
    """Start a VLC stream for a video"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            
            if not video:
                return jsonify({'error': 'Video not found'}), 404
            
            if not video.local_path:
                return jsonify({'error': 'No local file available for streaming'}), 400
            
            # Construct absolute path
            if os.path.isabs(video.local_path):
                video_path = video.local_path
            else:
                video_path = os.path.join(os.getcwd(), video.local_path)
            
            if not os.path.exists(video_path):
                return jsonify({'error': 'Video file not found on disk'}), 404
            
            # Start the stream
            result = vlc_streaming_service.start_stream(video_id, video_path)
            
            if result['success']:
                logger.info(f"Started VLC stream for video {video_id}: {video.title}")
                return jsonify(result), 200
            else:
                logger.error(f"Failed to start VLC stream for video {video_id}: {result.get('error')}")
                return jsonify(result), 500
                
    except Exception as e:
        logger.error(f"Error starting VLC stream for video {video_id}: {e}")
        return jsonify({'error': str(e)}), 500

@vlc_bp.route('/stream/<int:video_id>', methods=['DELETE'])
def stop_video_stream(video_id):
    """Stop a VLC stream for a video"""
    try:
        result = vlc_streaming_service.stop_stream(video_id)
        
        if result['success']:
            logger.info(f"Stopped VLC stream for video {video_id}")
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error stopping VLC stream for video {video_id}: {e}")
        return jsonify({'error': str(e)}), 500

@vlc_bp.route('/stream/<int:video_id>', methods=['GET'])
def get_stream_info(video_id):
    """Get information about a video stream"""
    try:
        result = vlc_streaming_service.get_stream_info(video_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting VLC stream info for video {video_id}: {e}")
        return jsonify({'error': str(e)}), 500

@vlc_bp.route('/streams', methods=['GET'])
def list_active_streams():
    """List all active VLC streams"""
    try:
        streams = vlc_streaming_service.list_active_streams()
        return jsonify({'streams': streams, 'count': len(streams)}), 200
        
    except Exception as e:
        logger.error(f"Error listing VLC streams: {e}")
        return jsonify({'error': str(e)}), 500

@vlc_bp.route('/cleanup', methods=['POST'])
def cleanup_old_streams():
    """Clean up old/expired VLC streams"""
    try:
        vlc_streaming_service.cleanup_old_streams()
        return jsonify({'message': 'Cleanup completed'}), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up VLC streams: {e}")
        return jsonify({'error': str(e)}), 500