"""
API routes registration for MVidarr
"""

from flask import Blueprint

from src.api.admin_interface import admin_bp
from src.api.artists import artists_bp
from src.api.auth import auth_bp
from src.api.genres import genres_bp
from src.api.health import health_bp
from src.api.imvdb import imvdb_bp
from src.api.lastfm import lastfm_bp
from src.api.lidarr import lidarr_bp
from src.api.metube import metube_bp

# OpenAPI documentation
from src.api.openapi import openapi_bp
from src.api.optimization import optimization_bp
from src.api.plex import plex_bp
from src.api.settings import settings_bp

# External integration blueprints
from src.api.spotify import spotify_bp
from src.api.two_factor import two_factor_bp
from src.api.users import users_bp
from src.api.video_discovery import video_discovery_bp
from src.api.video_indexing import video_indexing_bp
from src.api.video_organization import video_org_bp
from src.api.videos import videos_bp
from src.api.vlc_streaming import vlc_bp

# Webhook system
from src.api.webhooks import webhooks_bp
from src.api.youtube import youtube_bp
from src.api.youtube_playlists import youtube_playlists_bp


def register_routes(app):
    """Register all API routes"""

    # Create main API blueprint
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    # Register core API sub-blueprints
    api_bp.register_blueprint(artists_bp)
    api_bp.register_blueprint(videos_bp)
    api_bp.register_blueprint(settings_bp)
    api_bp.register_blueprint(health_bp)
    api_bp.register_blueprint(users_bp)
    api_bp.register_blueprint(video_org_bp)
    api_bp.register_blueprint(video_indexing_bp)
    api_bp.register_blueprint(metube_bp)
    api_bp.register_blueprint(video_discovery_bp)
    api_bp.register_blueprint(vlc_bp)
    api_bp.register_blueprint(optimization_bp)
    api_bp.register_blueprint(genres_bp)

    # Register external integration blueprints
    api_bp.register_blueprint(spotify_bp)
    api_bp.register_blueprint(imvdb_bp)
    api_bp.register_blueprint(youtube_bp)
    api_bp.register_blueprint(youtube_playlists_bp)
    api_bp.register_blueprint(lastfm_bp)
    api_bp.register_blueprint(plex_bp)
    api_bp.register_blueprint(lidarr_bp, url_prefix="/lidarr")

    # Register webhook system
    api_bp.register_blueprint(webhooks_bp)

    # Register main API blueprint
    app.register_blueprint(api_bp)

    # Register authentication routes directly (not under /api)
    app.register_blueprint(auth_bp)
    app.register_blueprint(two_factor_bp)

    # Register admin interface directly (not under /api)
    app.register_blueprint(admin_bp)

    # Register OpenAPI documentation
    app.register_blueprint(openapi_bp)

    # Register frontend routes
    from src.api.frontend import frontend_bp

    app.register_blueprint(frontend_bp)

    app.logger.info("API routes registered successfully")
