"""
OpenAPI documentation and specification for MVidarr REST API
"""

import os

from flask import Blueprint, Response, jsonify

from src.utils.logger import get_logger

logger = get_logger("mvidarr.api.openapi")

# Create OpenAPI blueprint
openapi_bp = Blueprint("openapi", __name__, url_prefix="/api/docs")

# OpenAPI specification
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "MVidarr API",
        "version": "1.0.0",
        "description": "Professional music video management system with artist tracking, video discovery, and external service integration",
        "contact": {
            "name": "MVidarr",
            "url": "https://github.com/mvidarr/mvidarr-enhanced",
        },
        "license": {"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    },
    "servers": [{"url": "http://localhost:5000", "description": "Development server"}],
    "components": {
        "schemas": {
            "Artist": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Taylor Swift"},
                    "imvdb_id": {"type": "string", "example": "1234"},
                    "spotify_id": {
                        "type": "string",
                        "example": "06HL4z0CvFAxyc27GXpf02",
                    },
                    "lastfm_name": {"type": "string", "example": "Taylor Swift"},
                    "thumbnail_url": {
                        "type": "string",
                        "example": "https://example.com/thumb.jpg",
                    },
                    "thumbnail_path": {
                        "type": "string",
                        "example": "/data/thumbnails/artist_1.jpg",
                    },
                    "thumbnail_source": {
                        "type": "string",
                        "enum": ["imvdb", "wikipedia", "manual", "generated"],
                    },
                    "auto_download": {"type": "boolean", "example": True},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "folder_path": {
                        "type": "string",
                        "example": "/data/downloads/Taylor Swift",
                    },
                    "monitored": {"type": "boolean", "example": True},
                    "source": {
                        "type": "string",
                        "enum": [
                            "imvdb",
                            "spotify_import",
                            "lastfm_import",
                            "plex_sync",
                            "manual",
                        ],
                    },
                    "last_discovery": {"type": "string", "format": "date-time"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                },
            },
            "Video": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "artist_id": {"type": "integer", "example": 1},
                    "title": {"type": "string", "example": "Shake It Off"},
                    "imvdb_id": {"type": "string", "example": "5678"},
                    "youtube_id": {"type": "string", "example": "nfWlot6h_JM"},
                    "youtube_url": {
                        "type": "string",
                        "example": "https://www.youtube.com/watch?v=nfWlot6h_JM",
                    },
                    "url": {
                        "type": "string",
                        "example": "https://example.com/video.mp4",
                    },
                    "playlist_id": {
                        "type": "string",
                        "example": "PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG",
                    },
                    "playlist_position": {"type": "integer", "example": 1},
                    "source": {
                        "type": "string",
                        "enum": ["imvdb", "youtube_playlist", "manual"],
                    },
                    "thumbnail_url": {
                        "type": "string",
                        "example": "https://example.com/thumb.jpg",
                    },
                    "thumbnail_path": {
                        "type": "string",
                        "example": "/data/thumbnails/video_1.jpg",
                    },
                    "local_path": {
                        "type": "string",
                        "example": "/data/downloads/Taylor Swift/Shake It Off.mp4",
                    },
                    "duration": {"type": "integer", "example": 242},
                    "year": {"type": "integer", "example": 2014},
                    "release_date": {"type": "string", "format": "date"},
                    "description": {"type": "string"},
                    "view_count": {"type": "integer", "example": 1000000},
                    "directors": {"type": "array", "items": {"type": "string"}},
                    "producers": {"type": "array", "items": {"type": "string"}},
                    "status": {
                        "type": "string",
                        "enum": [
                            "WANTED",
                            "DOWNLOADING",
                            "DOWNLOADED",
                            "IGNORED",
                            "FAILED",
                            "MONITORED",
                        ],
                    },
                    "quality": {"type": "string", "example": "720p"},
                    "discovered_date": {"type": "string", "format": "date-time"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                },
            },
            "Download": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "artist_id": {"type": "integer", "example": 1},
                    "video_id": {"type": "integer", "example": 1},
                    "title": {"type": "string", "example": "Shake It Off"},
                    "original_url": {
                        "type": "string",
                        "example": "https://www.youtube.com/watch?v=nfWlot6h_JM",
                    },
                    "file_path": {
                        "type": "string",
                        "example": "/data/downloads/Taylor Swift/Shake It Off.mp4",
                    },
                    "file_size": {"type": "integer", "example": 52428800},
                    "download_date": {"type": "string", "format": "date-time"},
                    "metube_id": {"type": "string", "example": "abc123"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "downloading", "completed", "failed"],
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "example": 5,
                    },
                    "progress": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "example": 75,
                    },
                    "error_message": {"type": "string"},
                    "quality": {"type": "string", "example": "720p"},
                    "format": {"type": "string", "example": "mp4"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                },
            },
            "PlaylistMonitor": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "playlist_id": {
                        "type": "string",
                        "example": "PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG",
                    },
                    "playlist_url": {
                        "type": "string",
                        "example": "https://www.youtube.com/playlist?list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG",
                    },
                    "name": {"type": "string", "example": "My Favorite Music Videos"},
                    "channel_title": {"type": "string", "example": "TaylorSwiftVEVO"},
                    "channel_id": {
                        "type": "string",
                        "example": "UCqECaJ8Gagnn7YCbPEzWH6g",
                    },
                    "auto_download": {"type": "boolean", "example": True},
                    "quality": {"type": "string", "example": "720p"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "last_check": {"type": "string", "format": "date-time"},
                    "last_video_count": {"type": "integer", "example": 42},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                },
            },
            "Setting": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "key": {"type": "string", "example": "metube_host"},
                    "value": {"type": "string", "example": "localhost"},
                    "description": {
                        "type": "string",
                        "example": "MeTube server hostname",
                    },
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                },
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Resource not found"},
                    "message": {
                        "type": "string",
                        "example": "The requested resource could not be found",
                    },
                    "code": {"type": "integer", "example": 404},
                },
            },
            "Success": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {
                        "type": "string",
                        "example": "Operation completed successfully",
                    },
                    "data": {"type": "object"},
                },
            },
        },
        "responses": {
            "NotFound": {
                "description": "Resource not found",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                },
            },
            "BadRequest": {
                "description": "Bad request",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                },
            },
            "InternalServerError": {
                "description": "Internal server error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"}
                    }
                },
            },
        },
    },
    "paths": {
        "/api/artists": {
            "get": {
                "summary": "Get all artists",
                "description": "Retrieve a list of all artists with optional filtering and pagination",
                "tags": ["Artists"],
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "description": "Page number",
                        "required": False,
                        "schema": {"type": "integer", "default": 1},
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Number of items per page",
                        "required": False,
                        "schema": {"type": "integer", "default": 50, "maximum": 200},
                    },
                    {
                        "name": "search",
                        "in": "query",
                        "description": "Search term for artist name",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "monitored",
                        "in": "query",
                        "description": "Filter by monitored status",
                        "required": False,
                        "schema": {"type": "boolean"},
                    },
                    {
                        "name": "source",
                        "in": "query",
                        "description": "Filter by source",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "imvdb",
                                "spotify_import",
                                "lastfm_import",
                                "plex_sync",
                                "manual",
                            ],
                        },
                    },
                    {
                        "name": "sort",
                        "in": "query",
                        "description": "Sort field",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "name",
                                "created_at",
                                "updated_at",
                                "last_discovery",
                            ],
                            "default": "name",
                        },
                    },
                    {
                        "name": "order",
                        "in": "query",
                        "description": "Sort order",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "default": "asc",
                        },
                    },
                ],
                "responses": {
                    "200": {
                        "description": "List of artists",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "artists": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/Artist"
                                            },
                                        },
                                        "total": {"type": "integer"},
                                        "page": {"type": "integer"},
                                        "limit": {"type": "integer"},
                                        "pages": {"type": "integer"},
                                    },
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "summary": "Create new artist",
                "description": "Add a new artist to the system",
                "tags": ["Artists"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "imvdb_id": {"type": "string"},
                                    "spotify_id": {"type": "string"},
                                    "lastfm_name": {"type": "string"},
                                    "auto_download": {
                                        "type": "boolean",
                                        "default": False,
                                    },
                                    "keywords": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "monitored": {"type": "boolean", "default": True},
                                    "source": {"type": "string", "default": "manual"},
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Artist created successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Artist"}
                            }
                        },
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "500": {"$ref": "#/components/responses/InternalServerError"},
                },
            },
        },
        "/api/artists/{id}": {
            "get": {
                "summary": "Get artist by ID",
                "description": "Retrieve detailed information about a specific artist",
                "tags": ["Artists"],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "description": "Artist ID",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Artist details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Artist"}
                            }
                        },
                    },
                    "404": {"$ref": "#/components/responses/NotFound"},
                },
            },
            "put": {
                "summary": "Update artist",
                "description": "Update an existing artist's information",
                "tags": ["Artists"],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "description": "Artist ID",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "imvdb_id": {"type": "string"},
                                    "spotify_id": {"type": "string"},
                                    "lastfm_name": {"type": "string"},
                                    "auto_download": {"type": "boolean"},
                                    "keywords": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "monitored": {"type": "boolean"},
                                    "source": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Artist updated successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Artist"}
                            }
                        },
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "500": {"$ref": "#/components/responses/InternalServerError"},
                },
            },
            "delete": {
                "summary": "Delete artist",
                "description": "Delete an artist and optionally associated videos",
                "tags": ["Artists"],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "description": "Artist ID",
                        "required": True,
                        "schema": {"type": "integer"},
                    },
                    {
                        "name": "delete_videos",
                        "in": "query",
                        "description": "Delete associated videos",
                        "required": False,
                        "schema": {"type": "boolean", "default": False},
                    },
                ],
                "responses": {
                    "200": {
                        "description": "Artist deleted successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Success"}
                            }
                        },
                    },
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "500": {"$ref": "#/components/responses/InternalServerError"},
                },
            },
        },
        "/api/videos": {
            "get": {
                "summary": "Get all videos",
                "description": "Retrieve a list of all videos with optional filtering and pagination",
                "tags": ["Videos"],
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "description": "Page number",
                        "required": False,
                        "schema": {"type": "integer", "default": 1},
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Number of items per page",
                        "required": False,
                        "schema": {"type": "integer", "default": 50, "maximum": 200},
                    },
                    {
                        "name": "search",
                        "in": "query",
                        "description": "Search term for video title",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "artist_id",
                        "in": "query",
                        "description": "Filter by artist ID",
                        "required": False,
                        "schema": {"type": "integer"},
                    },
                    {
                        "name": "status",
                        "in": "query",
                        "description": "Filter by status",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": [
                                "WANTED",
                                "DOWNLOADING",
                                "DOWNLOADED",
                                "IGNORED",
                                "FAILED",
                                "MONITORED",
                            ],
                        },
                    },
                    {
                        "name": "source",
                        "in": "query",
                        "description": "Filter by source",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["imvdb", "youtube_playlist", "manual"],
                        },
                    },
                    {
                        "name": "sort",
                        "in": "query",
                        "description": "Sort field",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["title", "created_at", "updated_at", "year"],
                            "default": "title",
                        },
                    },
                    {
                        "name": "order",
                        "in": "query",
                        "description": "Sort order",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "default": "asc",
                        },
                    },
                ],
                "responses": {
                    "200": {
                        "description": "List of videos",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "videos": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/Video"
                                            },
                                        },
                                        "total": {"type": "integer"},
                                        "page": {"type": "integer"},
                                        "limit": {"type": "integer"},
                                        "pages": {"type": "integer"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/spotify/status": {
            "get": {
                "summary": "Get Spotify integration status",
                "description": "Check if Spotify is configured and authenticated",
                "tags": ["External Integrations"],
                "responses": {
                    "200": {
                        "description": "Spotify status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "configured": {"type": "boolean"},
                                        "authenticated": {"type": "boolean"},
                                        "profile": {"type": "object"},
                                        "client_id": {"type": "string"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/youtube/playlists": {
            "get": {
                "summary": "Get monitored YouTube playlists",
                "description": "Retrieve all monitored YouTube playlists",
                "tags": ["External Integrations"],
                "responses": {
                    "200": {
                        "description": "List of monitored playlists",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "playlists": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/PlaylistMonitor"
                                            },
                                        },
                                        "count": {"type": "integer"},
                                    },
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "summary": "Create YouTube playlist monitor",
                "description": "Add a new YouTube playlist to monitor",
                "tags": ["External Integrations"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["playlist_url"],
                                "properties": {
                                    "playlist_url": {"type": "string"},
                                    "name": {"type": "string"},
                                    "auto_download": {
                                        "type": "boolean",
                                        "default": True,
                                    },
                                    "quality": {"type": "string", "default": "720p"},
                                    "keywords": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Playlist monitor created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Success"}
                            }
                        },
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                },
            },
        },
        "/api/lastfm/status": {
            "get": {
                "summary": "Get Last.fm integration status",
                "description": "Check if Last.fm is configured and authenticated",
                "tags": ["External Integrations"],
                "responses": {
                    "200": {
                        "description": "Last.fm status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "configured": {"type": "boolean"},
                                        "authenticated": {"type": "boolean"},
                                        "username": {"type": "string"},
                                        "subscriber": {"type": "boolean"},
                                        "profile": {"type": "object"},
                                        "api_key": {"type": "string"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/plex/status": {
            "get": {
                "summary": "Get Plex integration status",
                "description": "Check if Plex is configured and connected",
                "tags": ["External Integrations"],
                "responses": {
                    "200": {
                        "description": "Plex status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "configured": {"type": "boolean"},
                                        "connected": {"type": "boolean"},
                                        "server_url": {"type": "string"},
                                        "token": {"type": "string"},
                                        "server_info": {"type": "object"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/health": {
            "get": {
                "summary": "System health check",
                "description": "Check the health status of all system components",
                "tags": ["System"],
                "responses": {
                    "200": {
                        "description": "System health status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {
                                            "type": "string",
                                            "enum": [
                                                "healthy",
                                                "degraded",
                                                "unhealthy",
                                            ],
                                        },
                                        "timestamp": {
                                            "type": "string",
                                            "format": "date-time",
                                        },
                                        "services": {
                                            "type": "object",
                                            "properties": {
                                                "database": {"type": "object"},
                                                "metube": {"type": "object"},
                                                "imvdb": {"type": "object"},
                                                "filesystem": {"type": "object"},
                                            },
                                        },
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/settings": {
            "get": {
                "summary": "Get all settings",
                "description": "Retrieve all system settings",
                "tags": ["Settings"],
                "responses": {
                    "200": {
                        "description": "List of settings",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "settings": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/Setting"
                                            },
                                        }
                                    },
                                }
                            }
                        },
                    }
                },
            },
            "put": {
                "summary": "Update settings",
                "description": "Update one or more system settings",
                "tags": ["Settings"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Settings updated successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Success"}
                            }
                        },
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                },
            },
        },
    },
    "tags": [
        {"name": "Artists", "description": "Artist management operations"},
        {"name": "Videos", "description": "Video management operations"},
        {
            "name": "External Integrations",
            "description": "External service integrations (Spotify, YouTube, Last.fm, Plex)",
        },
        {"name": "System", "description": "System health and monitoring"},
        {"name": "Settings", "description": "System configuration and settings"},
    ],
}


@openapi_bp.route("/openapi.json", methods=["GET"])
def get_openapi_spec():
    """Get OpenAPI specification in JSON format"""
    return jsonify(OPENAPI_SPEC)


@openapi_bp.route("/swagger", methods=["GET"])
def swagger_ui():
    """Serve Swagger UI for API documentation"""
    swagger_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MVidarr API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
        <style>
            html {
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }
            *, *:before, *:after {
                box-sizing: inherit;
            }
            body {
                margin:0;
                background: #fafafa;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }
            .swagger-ui .topbar {
                background-color: #2d2d2d;
                border-bottom: 1px solid #444;
            }
            .swagger-ui .topbar .download-url-wrapper {
                display: none;
            }
            .swagger-ui .info {
                margin: 20px 0;
            }
            .swagger-ui .info .title {
                color: #4a90e2;
                font-size: 36px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .swagger-ui .info .description {
                color: #666;
                font-size: 16px;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/api/docs/openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    validatorUrl: null,
                    displayRequestDuration: true,
                    displayOperationId: false,
                    showExtensions: true,
                    showCommonExtensions: true,
                    tryItOutEnabled: true,
                    requestInterceptor: function(request) {
                        // Add any custom headers here
                        return request;
                    },
                    responseInterceptor: function(response) {
                        // Handle responses
                        return response;
                    }
                });
            };
        </script>
    </body>
    </html>
    """
    return Response(swagger_html, mimetype="text/html")


@openapi_bp.route("/redoc", methods=["GET"])
def redoc_ui():
    """Serve ReDoc UI for API documentation"""
    redoc_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MVidarr API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            }
        </style>
    </head>
    <body>
        <redoc spec-url='/api/docs/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return Response(redoc_html, mimetype="text/html")


@openapi_bp.route("/", methods=["GET"])
def api_docs_index():
    """API documentation index page"""
    index_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MVidarr API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                margin: 0;
                padding: 40px;
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
                background: #f5f5f5;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #4a90e2;
                font-size: 36px;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                font-size: 18px;
                margin-bottom: 30px;
            }
            .docs-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .doc-card {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
                text-decoration: none;
                color: inherit;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .doc-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                text-decoration: none;
                color: inherit;
            }
            .doc-card h3 {
                color: #4a90e2;
                margin-top: 0;
                margin-bottom: 10px;
            }
            .doc-card p {
                margin-bottom: 0;
                color: #666;
            }
            .features {
                margin-top: 40px;
            }
            .features h2 {
                color: #4a90e2;
                margin-bottom: 15px;
            }
            .features ul {
                list-style: none;
                padding: 0;
            }
            .features li {
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            .features li:last-child {
                border-bottom: none;
            }
            .features li:before {
                content: "✓";
                color: #28a745;
                font-weight: bold;
                margin-right: 10px;
            }
            .api-info {
                background: #e7f3ff;
                border: 1px solid #b3d9ff;
                border-radius: 8px;
                padding: 20px;
                margin-top: 30px;
            }
            .api-info h3 {
                color: #0066cc;
                margin-top: 0;
                margin-bottom: 10px;
            }
            .api-info code {
                background: #f1f1f1;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MVidarr API</h1>
            <p class="subtitle">Professional music video management system with comprehensive REST API</p>
            
            <div class="docs-grid">
                <a href="/api/docs/swagger" class="doc-card">
                    <h3>Swagger UI</h3>
                    <p>Interactive API documentation with try-it-out functionality. Perfect for testing and exploring endpoints.</p>
                </a>
                
                <a href="/api/docs/redoc" class="doc-card">
                    <h3>ReDoc</h3>
                    <p>Clean, responsive API documentation with detailed schemas and examples. Great for reference.</p>
                </a>
                
                <a href="/api/docs/openapi.json" class="doc-card">
                    <h3>OpenAPI Spec</h3>
                    <p>Raw OpenAPI 3.0 specification in JSON format. Use this for code generation and integrations.</p>
                </a>
            </div>
            
            <div class="features">
                <h2>API Features</h2>
                <ul>
                    <li>Complete artist and video management</li>
                    <li>External service integrations (Spotify, YouTube, Last.fm, Plex)</li>
                    <li>Advanced search and filtering capabilities</li>
                    <li>Bulk operations and batch processing</li>
                    <li>Real-time download management</li>
                    <li>Comprehensive system health monitoring</li>
                    <li>Flexible configuration and settings</li>
                    <li>RESTful design with consistent error handling</li>
                    <li>Pagination and sorting support</li>
                    <li>Detailed response schemas and validation</li>
                </ul>
            </div>
            
            <div class="api-info">
                <h3>Getting Started</h3>
                <p>The MVidarr API uses standard HTTP methods and returns JSON responses. All endpoints are prefixed with <code>/api</code>.</p>
                <p>Base URL: <code>http://localhost:5000/api</code></p>
                <p>For detailed information about authentication, rate limiting, and usage examples, please refer to the interactive documentation above.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return Response(index_html, mimetype="text/html")
