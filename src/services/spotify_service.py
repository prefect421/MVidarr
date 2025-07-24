"""
Spotify API integration service for importing playlists and discovering music videos
"""

import requests
import base64
import json
from typing import Dict, List, Optional
from urllib.parse import urlencode, quote_plus
import os
from datetime import datetime, timedelta
from src.utils.logger import get_logger
from src.database.connection import get_db
from src.database.models import Artist, Video, VideoStatus
from src.services.imvdb_service import imvdb_service
from src.services.settings_service import settings
from sqlalchemy import and_, or_

logger = get_logger('mvidarr.services.spotify')

class SpotifyService:
    """Service for Spotify API integration"""
    
    def __init__(self):
        self.base_url = 'https://api.spotify.com/v1'
        self.auth_url = 'https://accounts.spotify.com/api/token'
        self.access_token = None
        self.refresh_token = None
        self.token_expires = None
        # Cache for settings to avoid repeated calls
        self._client_id = None
        self._client_secret = None
        self._redirect_uri = None
        self._settings_loaded = False
        
    def _load_settings(self):
        """Load settings once and cache them"""
        if self._settings_loaded:
            logger.debug("Spotify settings already loaded, skipping reload")
            return
            
        try:
            logger.debug("Loading Spotify settings from database")
            self._client_id = settings.get('spotify_client_id')
            self._client_secret = settings.get('spotify_client_secret')
            
            # Try to get configured redirect URI first
            configured_uri = settings.get('spotify_redirect_uri')
            if configured_uri:
                self._redirect_uri = configured_uri
                logger.debug(f"Using configured redirect URI: {self._redirect_uri}")
            else:
                # Construct default redirect URI using server settings
                server_host = settings.get('server_host', '127.0.0.1')  # Use IPv4 loopback instead of localhost
                server_port = settings.get('server_port', 5000)
                self._redirect_uri = f"http://{server_host}:{server_port}/api/spotify/callback"
                logger.debug(f"Using default redirect URI: {self._redirect_uri}")
            
            self._settings_loaded = True
            logger.debug("Spotify settings loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Spotify settings: {e}")
            # Set fallback values
            self._client_id = None
            self._client_secret = None
            self._redirect_uri = 'http://127.0.0.1:5000/api/spotify/callback'
            self._settings_loaded = True
            logger.warning(f"Using fallback redirect URI: {self._redirect_uri}")
    
    @property
    def client_id(self):
        """Get Spotify client ID from database settings"""
        self._load_settings()
        return self._client_id
    
    @property
    def client_secret(self):
        """Get Spotify client secret from database settings"""
        self._load_settings()
        return self._client_secret
    
    @property
    def redirect_uri(self):
        """Get Spotify redirect URI from database settings or construct default"""
        self._load_settings()
        return self._redirect_uri
    
    def clear_cache(self):
        """Clear cached settings to force reload"""
        self._settings_loaded = False
        self._client_id = None
        self._client_secret = None
        self._redirect_uri = None
    
    def reload_settings(self):
        """Force reload of settings from database"""
        self.clear_cache()
        self._load_settings()
        logger.info("Spotify settings reloaded from database")
        
    def get_auth_url(self) -> str:
        """Generate Spotify authorization URL"""
        scopes = [
            'playlist-read-private',
            'playlist-read-collaborative',
            'user-library-read',
            'user-follow-read',
            'user-top-read'
        ]
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
            'show_dialog': 'true'
        }
        
        return f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    
    def get_access_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify client credentials not configured")
        
        # Prepare credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(self.auth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully obtained Spotify access token")
            return token_data
            
        except requests.RequestException as e:
            logger.error(f"Failed to get Spotify access token: {e}")
            raise
    
    def refresh_access_token(self) -> Dict:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        try:
            response = requests.post(self.auth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            # Update refresh token if provided
            if token_data.get('refresh_token'):
                self.refresh_token = token_data['refresh_token']
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully refreshed Spotify access token")
            return token_data
            
        except requests.RequestException as e:
            logger.error(f"Failed to refresh Spotify access token: {e}")
            raise
    
    def get_client_credentials_token(self) -> Dict:
        """Get access token using client credentials flow"""
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify client credentials not configured")
        
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(self.auth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully obtained Spotify client credentials token")
            return token_data
            
        except requests.RequestException as e:
            logger.error(f"Failed to get Spotify client credentials token: {e}")
            raise
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token:
            raise ValueError("No access token available")
        
        if self.token_expires and datetime.now() >= self.token_expires:
            self.refresh_access_token()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Spotify API"""
        self._ensure_valid_token()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Spotify API request failed: {e}")
            raise
    
    def get_user_profile(self) -> Dict:
        """Get current user's Spotify profile"""
        return self._make_request('me')
    
    def get_user_playlists(self, limit: int = 50, offset: int = 0) -> Dict:
        """Get user's playlists"""
        params = {
            'limit': limit,
            'offset': offset
        }
        return self._make_request('me/playlists', params)
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 100, offset: int = 0) -> Dict:
        """Get tracks from a specific playlist"""
        params = {
            'limit': limit,
            'offset': offset,
            'fields': 'items(track(id,name,artists(name,id),album(name,images),duration_ms,external_urls,popularity)),next,total'
        }
        return self._make_request(f'playlists/{playlist_id}/tracks', params)
    
    def get_user_top_artists(self, time_range: str = 'medium_term', limit: int = 50) -> Dict:
        """Get user's top artists"""
        params = {
            'time_range': time_range,  # short_term, medium_term, long_term
            'limit': limit
        }
        return self._make_request('me/top/artists', params)
    
    def get_user_top_tracks(self, time_range: str = 'medium_term', limit: int = 50) -> Dict:
        """Get user's top tracks"""
        params = {
            'time_range': time_range,
            'limit': limit
        }
        return self._make_request('me/top/tracks', params)
    
    def get_followed_artists(self, limit: int = 50) -> Dict:
        """Get artists the user follows"""
        params = {
            'type': 'artist',
            'limit': limit
        }
        return self._make_request('me/following', params)
    
    def search_artist(self, artist_name: str, limit: int = 10) -> Dict:
        """Search for artists on Spotify"""
        params = {
            'q': artist_name,
            'type': 'artist',
            'limit': limit
        }
        return self._make_request('search', params)
    
    def get_artist_albums(self, artist_id: str, limit: int = 50) -> Dict:
        """Get albums by an artist"""
        params = {
            'include_groups': 'album,single',
            'limit': limit,
            'market': 'US'
        }
        return self._make_request(f'artists/{artist_id}/albums', params)
    
    def get_artist_top_tracks(self, artist_id: str, market: str = 'US') -> Dict:
        """Get artist's top tracks"""
        params = {
            'market': market
        }
        return self._make_request(f'artists/{artist_id}/top-tracks', params)
    
    def import_playlist_artists(self, playlist_id: str) -> Dict:
        """Import artists from a Spotify playlist and search for music videos"""
        logger.info(f"Importing artists from Spotify playlist: {playlist_id}")
        
        try:
            # Get playlist details first
            playlist_info = self._make_request(f'playlists/{playlist_id}')
            playlist_name = playlist_info.get('name', 'Unknown Playlist')
            
            # Get all tracks from playlist
            all_tracks = []
            offset = 0
            limit = 100
            
            while True:
                tracks_data = self.get_playlist_tracks(playlist_id, limit, offset)
                tracks = tracks_data.get('items', [])
                
                if not tracks:
                    break
                
                all_tracks.extend(tracks)
                
                if len(tracks) < limit:
                    break
                
                offset += limit
            
            # Extract unique artists
            artists_data = {}
            for track_item in all_tracks:
                track = track_item.get('track')
                if not track:
                    continue
                
                for artist in track.get('artists', []):
                    artist_id = artist.get('id')
                    artist_name = artist.get('name')
                    
                    if artist_id and artist_name and artist_id not in artists_data:
                        artists_data[artist_id] = {
                            'name': artist_name,
                            'spotify_id': artist_id,
                            'tracks': []
                        }
                    
                    if artist_id in artists_data:
                        artists_data[artist_id]['tracks'].append({
                            'name': track.get('name'),
                            'popularity': track.get('popularity', 0)
                        })
            
            # Process artists and find music videos
            results = {
                'playlist_name': playlist_name,
                'total_tracks': len(all_tracks),
                'unique_artists': len(artists_data),
                'imported_artists': 0,
                'found_videos': 0,
                'errors': []
            }
            
            with get_db() as session:
                for spotify_id, artist_data in artists_data.items():
                    try:
                        # Check if artist already exists
                        existing_artist = session.query(Artist).filter(
                            or_(
                                Artist.name.ilike(f"%{artist_data['name']}%"),
                                Artist.spotify_id == spotify_id
                            )
                        ).first()
                        
                        if existing_artist:
                            # Update Spotify ID if missing
                            if not existing_artist.spotify_id:
                                existing_artist.spotify_id = spotify_id
                                session.commit()
                            
                            logger.info(f"Artist already exists: {artist_data['name']}")
                            continue
                        
                        # Search for artist on IMVDb
                        imvdb_results = imvdb_service.search_artist(artist_data['name'])
                        
                        if imvdb_results and imvdb_results.get('results'):
                            # Use the first (most relevant) result
                            imvdb_artist = imvdb_results['results'][0]
                            
                            # Create new artist
                            new_artist = Artist(
                                name=artist_data['name'],
                                imvdb_id=imvdb_artist.get('id'),
                                spotify_id=spotify_id,
                                monitored=True,
                                auto_download=False,
                                source='spotify_import'
                            )
                            
                            session.add(new_artist)
                            session.commit()
                            
                            results['imported_artists'] += 1
                            
                            # Search for music videos
                            video_results = imvdb_service.get_artist_videos(imvdb_artist.get('id'))
                            
                            if video_results and video_results.get('results'):
                                for video_data in video_results['results']:
                                    # Check if video already exists
                                    existing_video = session.query(Video).filter(
                                        Video.imvdb_id == video_data.get('id')
                                    ).first()
                                    
                                    if existing_video:
                                        continue
                                    
                                    # Create new video
                                    new_video = Video(
                                        title=video_data.get('song_title', 'Unknown'),
                                        artist_id=new_artist.id,
                                        imvdb_id=video_data.get('id'),
                                        video_url=video_data.get('image', {}).get('o'),
                                        thumbnail_url=video_data.get('image', {}).get('l'),
                                        year=video_data.get('year'),
                                        status=VideoStatus.WANTED,
                                        source='spotify_import'
                                    )
                                    
                                    session.add(new_video)
                                    results['found_videos'] += 1
                                
                                session.commit()
                            
                            logger.info(f"Imported artist: {artist_data['name']} with {len(video_results.get('results', []))} videos")
                        
                        else:
                            # Create artist without IMVDb data
                            new_artist = Artist(
                                name=artist_data['name'],
                                spotify_id=spotify_id,
                                monitored=True,
                                auto_download=False,
                                source='spotify_import'
                            )
                            
                            session.add(new_artist)
                            session.commit()
                            
                            results['imported_artists'] += 1
                            logger.info(f"Imported artist without IMVDb data: {artist_data['name']}")
                    
                    except Exception as e:
                        error_msg = f"Error importing artist {artist_data['name']}: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            
            logger.info(f"Playlist import completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to import playlist: {e}")
            raise
    
    def sync_followed_artists(self) -> Dict:
        """Sync user's followed artists from Spotify"""
        logger.info("Syncing followed artists from Spotify")
        
        try:
            # Get followed artists
            followed_data = self.get_followed_artists(limit=50)
            artists = followed_data.get('artists', {}).get('items', [])
            
            results = {
                'total_followed': len(artists),
                'imported_artists': 0,
                'found_videos': 0,
                'errors': []
            }
            
            with get_db() as session:
                for artist_data in artists:
                    try:
                        artist_name = artist_data.get('name')
                        spotify_id = artist_data.get('id')
                        
                        # Check if artist already exists
                        existing_artist = session.query(Artist).filter(
                            or_(
                                Artist.name.ilike(f"%{artist_name}%"),
                                Artist.spotify_id == spotify_id
                            )
                        ).first()
                        
                        if existing_artist:
                            # Update Spotify ID if missing
                            if not existing_artist.spotify_id:
                                existing_artist.spotify_id = spotify_id
                                session.commit()
                            continue
                        
                        # Search for artist on IMVDb
                        imvdb_results = imvdb_service.search_artist(artist_name)
                        
                        if imvdb_results and imvdb_results.get('results'):
                            imvdb_artist = imvdb_results['results'][0]
                            
                            # Create new artist
                            new_artist = Artist(
                                name=artist_name,
                                imvdb_id=imvdb_artist.get('id'),
                                spotify_id=spotify_id,
                                monitored=True,
                                auto_download=False,
                                source='spotify_followed'
                            )
                            
                            session.add(new_artist)
                            session.commit()
                            
                            results['imported_artists'] += 1
                            
                            # Find music videos
                            video_results = imvdb_service.get_artist_videos(imvdb_artist.get('id'))
                            
                            if video_results and video_results.get('results'):
                                for video_data in video_results['results']:
                                    existing_video = session.query(Video).filter(
                                        Video.imvdb_id == video_data.get('id')
                                    ).first()
                                    
                                    if existing_video:
                                        continue
                                    
                                    new_video = Video(
                                        title=video_data.get('song_title', 'Unknown'),
                                        artist_id=new_artist.id,
                                        imvdb_id=video_data.get('id'),
                                        video_url=video_data.get('image', {}).get('o'),
                                        thumbnail_url=video_data.get('image', {}).get('l'),
                                        year=video_data.get('year'),
                                        status=VideoStatus.WANTED,
                                        source='spotify_followed'
                                    )
                                    
                                    session.add(new_video)
                                    results['found_videos'] += 1
                                
                                session.commit()
                    
                    except Exception as e:
                        error_msg = f"Error importing followed artist {artist_name}: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            
            logger.info(f"Followed artists sync completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync followed artists: {e}")
            raise

# Global instance
spotify_service = SpotifyService()