"""
Frontend routes for serving web interface
"""

from flask import Blueprint, render_template, send_from_directory
from pathlib import Path
from src.utils.logger import get_logger

frontend_bp = Blueprint('frontend', __name__)
logger = get_logger('mvidarr.api.frontend')

@frontend_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@frontend_bp.route('/artists')
def artists():
    """Artists management page"""
    return render_template('artists.html')

@frontend_bp.route('/artist/<int:artist_id>')
def artist_detail(artist_id):
    """Artist detail page"""
    return render_template('artist_detail.html')

@frontend_bp.route('/videos')
def videos():
    """Videos management page"""
    return render_template('videos.html')

@frontend_bp.route('/video/<int:video_id>')
def video_detail(video_id):
    """Video detail page"""
    return render_template('video_detail.html')

@frontend_bp.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@frontend_bp.route('/mvtv')
def mvtv():
    """MvTV continuous video player page"""
    return render_template('mvtv.html')

@frontend_bp.route('/youtube-playlists')
def youtube_playlists():
    """YouTube Playlists management page"""
    return render_template('youtube_playlists.html')

@frontend_bp.route('/spotify')
def spotify():
    """Spotify integration page"""
    return render_template('spotify.html')

@frontend_bp.route('/lastfm')
def lastfm():
    """Last.fm integration page"""
    return render_template('lastfm.html')

@frontend_bp.route('/plex')
def plex():
    """Plex integration page"""
    return render_template('plex.html')

@frontend_bp.route('/lidarr')
def lidarr():
    """Lidarr integration page"""
    return render_template('lidarr.html')

@frontend_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    static_dir = Path(__file__).parent.parent.parent / 'frontend' / 'static'
    return send_from_directory(static_dir, filename)

@frontend_bp.route('/css/<path:filename>')
def css_files(filename):
    """Serve CSS files"""
    css_dir = Path(__file__).parent.parent.parent / 'frontend' / 'CSS'
    return send_from_directory(css_dir, filename)