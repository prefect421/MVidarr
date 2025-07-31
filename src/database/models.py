"""
Database models for MVidarr
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import backref, relationship, validates
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.connection import Base


class VideoStatus(Enum):
    """Video status enumeration"""

    WANTED = "WANTED"
    DOWNLOADING = "DOWNLOADING"
    DOWNLOADED = "DOWNLOADED"
    IGNORED = "IGNORED"
    FAILED = "FAILED"
    MONITORED = "MONITORED"  # Video is being monitored but not actively wanted


class UserRole(Enum):
    """User role enumeration"""

    ADMIN = "ADMIN"  # Full access to everything
    MANAGER = "MANAGER"  # Can manage content and users (except admins)
    USER = "USER"  # Can view and download content
    READONLY = "READONLY"  # Can only view content, no modifications


class SessionStatus(Enum):
    """Session status enumeration"""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class Setting(Base):
    """Application settings"""

    __tablename__ = "settings"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Setting(key='{self.key}', value='{self.value}')>"


class User(Base):
    """Application users"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 compatible
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    two_factor_secret = Column(String(32), nullable=True)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    backup_codes = Column(JSON, nullable=True)  # List of backup codes
    preferences = Column(JSON, nullable=True)  # User preferences like theme, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, username, email, password, role=UserRole.USER):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role

    def set_password(self, password):
        """Set password hash with validation"""
        from src.utils.security import PasswordValidator

        # Validate password strength
        is_valid, errors = PasswordValidator.validate_password_strength(password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")

        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def is_locked(self):
        """Check if user account is locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def lock_account(self, duration_minutes=30):
        """Lock user account for specified duration"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0

    def unlock_account(self):
        """Unlock user account"""
        self.locked_until = None
        self.failed_login_attempts = 0

    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()

    def reset_failed_login(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0

    def generate_email_verification_token(self):
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token

    def generate_password_reset_token(self, expires_hours=1):
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=expires_hours)
        return self.password_reset_token

    def verify_password_reset_token(self, token):
        """Verify password reset token"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        if datetime.utcnow() > self.password_reset_expires:
            return False
        return self.password_reset_token == token

    def has_permission(self, required_role):
        """Check if user has required permission level"""
        role_hierarchy = {
            UserRole.READONLY: 0,
            UserRole.USER: 1,
            UserRole.MANAGER: 2,
            UserRole.ADMIN: 3,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def can_access_admin(self):
        """Check if user can access admin functions"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]

    def can_modify_content(self):
        """Check if user can modify content"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.USER]

    def can_delete_content(self):
        """Check if user can delete content"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]

    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role == UserRole.ADMIN

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_email_verified": self.is_email_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "preferences": self.preferences or {},
        }

        if include_sensitive:
            data.update(
                {
                    "failed_login_attempts": self.failed_login_attempts,
                    "is_locked": self.is_locked(),
                    "locked_until": (
                        self.locked_until.isoformat() if self.locked_until else None
                    ),
                    "last_login_ip": self.last_login_ip,
                    "two_factor_enabled": self.two_factor_enabled,
                }
            )

        return data

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role.value}')>"


class UserSession(Base):
    """User session management"""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    status = Column(
        SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False
    )
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __init__(self, user_id, ip_address=None, user_agent=None, expires_hours=24):
        self.user_id = user_id
        self.session_token = self.generate_session_token()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

    @staticmethod
    def generate_session_token():
        """Generate secure session token"""
        return secrets.token_urlsafe(32)

    def is_valid(self):
        """Check if session is valid"""
        return (
            self.status == SessionStatus.ACTIVE and datetime.utcnow() < self.expires_at
        )

    def refresh(self, extend_hours=24):
        """Refresh session expiry"""
        self.last_activity = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=extend_hours)

    def revoke(self):
        """Revoke session"""
        self.status = SessionStatus.REVOKED

    def expire(self):
        """Mark session as expired"""
        self.status = SessionStatus.EXPIRED

    def to_dict(self):
        """Convert session to dictionary"""
        return {
            "id": self.id,
            "session_token": self.session_token,
            "status": self.status.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_valid": self.is_valid(),
        }

    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, status='{self.status.value}')>"


class Artist(Base):
    """Artists being tracked"""

    __tablename__ = "artists"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    imvdb_id = Column(String(100), unique=True, nullable=True)
    spotify_id = Column(String(100), nullable=True)  # Spotify artist ID
    lastfm_name = Column(String(255), nullable=True)  # Last.fm artist name
    thumbnail_url = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    thumbnail_source = Column(
        String(50), nullable=True
    )  # 'imvdb', 'wikipedia', 'manual', 'generated'
    thumbnail_metadata = Column(JSON, nullable=True)  # Store sizes, upload info, etc.
    thumbnail_uploaded_at = Column(DateTime, nullable=True)  # When manually uploaded
    auto_download = Column(Boolean, default=False)
    keywords = Column(JSON, nullable=True)  # Video filtering keywords
    folder_path = Column(String(500), nullable=True)
    imvdb_metadata = Column(JSON, nullable=True)  # Additional IMVDB metadata
    genres = Column(
        JSON, nullable=True
    )  # Artist genres (automatically updated from videos)
    monitored = Column(Boolean, default=True)
    source = Column(
        String(50), nullable=True
    )  # Source: 'imvdb', 'spotify_import', 'manual', etc.
    last_discovery = Column(DateTime, nullable=True)  # Last time videos were discovered
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    videos = relationship(
        "Video", back_populates="artist", cascade="all, delete-orphan"
    )
    downloads = relationship(
        "Download", back_populates="artist", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_artist_name", "name"),
        Index("idx_artist_imvdb_id", "imvdb_id"),
        Index("idx_artist_spotify_id", "spotify_id"),
        Index("idx_artist_monitored", "monitored"),
        Index("idx_artist_source", "source"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<Artist(name='{self.name}', imvdb_id='{self.imvdb_id}')>"


class Video(Base):
    """Videos discovered for artists"""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    title = Column(String(500), nullable=False)
    imvdb_id = Column(String(100), unique=True, nullable=True)
    youtube_id = Column(String(100), nullable=True)
    youtube_url = Column(String(500), nullable=True)  # YouTube video URL
    url = Column(String(500), nullable=True)  # Video URL (YouTube, etc.)
    playlist_id = Column(
        String(100), nullable=True
    )  # YouTube playlist ID if from playlist
    playlist_position = Column(Integer, nullable=True)  # Position in playlist
    source = Column(
        String(50), nullable=True
    )  # Source: 'imvdb', 'youtube_playlist', 'manual', etc.
    thumbnail_url = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    thumbnail_source = Column(
        String(50), nullable=True
    )  # 'imvdb', 'youtube', 'manual', 'generated'
    thumbnail_metadata = Column(JSON, nullable=True)  # Store sizes, upload info, etc.
    thumbnail_uploaded_at = Column(DateTime, nullable=True)  # When manually uploaded
    local_path = Column(String(500), nullable=True)  # Path to local video file
    duration = Column(Integer, nullable=True)  # Duration in seconds
    year = Column(Integer, nullable=True)
    release_date = Column(DateTime, nullable=True)  # Video release/publish date
    description = Column(Text, nullable=True)  # Video description
    view_count = Column(Integer, nullable=True)  # View count
    like_count = Column(Integer, nullable=True)  # Like count from video platforms
    genres = Column(JSON, nullable=True)  # Video genres
    directors = Column(JSON, nullable=True)
    producers = Column(JSON, nullable=True)
    status = Column(SQLEnum(VideoStatus), default=VideoStatus.WANTED)
    quality = Column(String(50), nullable=True)
    video_metadata = Column(JSON, nullable=True)  # General metadata
    imvdb_metadata = Column(JSON, nullable=True)  # Full IMVDB metadata
    search_keywords = Column(Text, nullable=True)  # Keywords for matching
    discovered_date = Column(DateTime, nullable=True)  # When video was first discovered
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    artist = relationship("Artist", back_populates="videos")
    downloads = relationship(
        "Download", back_populates="video", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_video_artist_id", "artist_id"),
        Index("idx_video_imvdb_id", "imvdb_id"),
        Index("idx_video_youtube_id", "youtube_id"),
        Index("idx_video_playlist_id", "playlist_id"),
        Index("idx_video_status", "status"),
        Index("idx_video_title", "title"),
        Index("idx_video_source", "source"),
        {"extend_existing": True},
    )

    @validates("title")
    def validate_title(self, key, value):
        """Ensure title is always a string"""
        if value is None:
            return ""
        return str(value)

    def __repr__(self):
        return f"<Video(title='{self.title}', artist_id={self.artist_id}, status='{self.status}')>"


class Download(Base):
    """Download history and file tracking"""

    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    title = Column(String(500), nullable=False)
    original_url = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    download_date = Column(DateTime, default=datetime.utcnow)
    metube_id = Column(String(100), nullable=True)  # MeTube download ID
    status = Column(
        String(50), default="pending"
    )  # pending, downloading, completed, failed
    priority = Column(
        Integer, default=5
    )  # 1-10, lower is higher priority (1=highest, 10=lowest)
    progress = Column(Integer, default=0)  # Download progress percentage
    error_message = Column(Text, nullable=True)
    quality = Column(String(50), nullable=True)
    format = Column(String(50), nullable=True)
    download_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    artist = relationship("Artist", back_populates="downloads")
    video = relationship("Video", back_populates="downloads")

    # Indexes
    __table_args__ = (
        Index("idx_download_artist_id", "artist_id"),
        Index("idx_download_video_id", "video_id"),
        Index("idx_download_status", "status"),
        Index("idx_download_priority", "priority"),
        Index("idx_download_date", "download_date"),
        Index("idx_download_metube_id", "metube_id"),
        Index(
            "idx_download_priority_status", "priority", "status"
        ),  # Composite index for queue ordering
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<Download(title='{self.title}', status='{self.status}', artist_id={self.artist_id})>"


# User class is defined above with full authentication features


class TaskQueue(Base):
    """Background task queue"""

    __tablename__ = "task_queue"

    id = Column(Integer, primary_key=True)
    task_type = Column(String(100), nullable=False)  # artist_scan, video_download, etc.
    task_data = Column(JSON, nullable=True)
    status = Column(
        String(50), default="pending"
    )  # pending, running, completed, failed
    priority = Column(Integer, default=5)  # 1-10, lower is higher priority
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_task_status", "status"),
        Index("idx_task_priority", "priority"),
        Index("idx_task_type", "task_type"),
        Index("idx_task_created_at", "created_at"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<TaskQueue(task_type='{self.task_type}', status='{self.status}')>"


class PlaylistMonitor(Base):
    """YouTube playlist monitoring"""

    __tablename__ = "playlist_monitors"

    id = Column(Integer, primary_key=True)
    playlist_id = Column(
        String(100), unique=True, nullable=False
    )  # YouTube playlist ID
    playlist_url = Column(String(500), nullable=False)  # Original playlist URL
    name = Column(String(255), nullable=False)  # Display name for the playlist
    channel_title = Column(String(255), nullable=True)  # Channel that owns the playlist
    channel_id = Column(String(100), nullable=True)  # YouTube channel ID
    auto_download = Column(Boolean, default=True)  # Auto-download new videos
    quality = Column(String(50), default="720p")  # Download quality preference
    keywords = Column(JSON, nullable=True)  # Keywords to filter videos
    last_check = Column(DateTime, nullable=True)  # Last time playlist was checked
    last_video_count = Column(Integer, default=0)  # Track video count changes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_playlist_id", "playlist_id"),
        Index("idx_playlist_channel_id", "channel_id"),
        Index("idx_playlist_auto_download", "auto_download"),
        Index("idx_playlist_last_check", "last_check"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return (
            f"<PlaylistMonitor(name='{self.name}', playlist_id='{self.playlist_id}')>"
        )


class CustomTheme(Base):
    """Custom theme model for theme customization"""

    __tablename__ = "custom_themes"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_built_in = Column(Boolean, default=False, nullable=False)

    # Theme definition stored as JSON with CSS variables
    theme_data = Column(JSON, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", backref="created_themes")

    __table_args__ = (
        Index("idx_custom_theme_name", "name"),
        Index("idx_custom_theme_creator", "created_by"),
        Index("idx_custom_theme_public", "is_public"),
        {"extend_existing": True},
    )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "created_by": self.created_by,
            "creator_username": self.creator.username if self.creator else None,
            "is_public": self.is_public,
            "is_built_in": self.is_built_in,
            "theme_data": self.theme_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CustomTheme(name='{self.name}', display_name='{self.display_name}')>"
