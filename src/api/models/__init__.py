"""
Centralized Pydantic Models for MVidarr FastAPI
Phase 3 Week 32: Pydantic Validation and Models

This module provides a centralized, well-organized collection of Pydantic models
for all FastAPI endpoints, eliminating duplication and ensuring consistent validation.
"""

# Base classes and mixins
from .base import (
    BaseRequest,
    BaseResponse,
    PaginationRequest,
    PaginationResponse,
    BulkOperationRequest,
    BulkOperationResponse,
    TaskSubmissionResponse,
    TaskStatusResponse,
    ErrorResponse
)

# Common shared models
from .common import (
    IdRequest,
    StatusUpdateRequest,
    ThumbnailSearchRequest,
    FileUploadResponse,
    SearchFilters,
    SortOptions
)

# Domain-specific models
from .video import (
    VideoResponse,
    VideoCreateRequest,
    VideoUpdateRequest,
    VideoSearchRequest,
    VideoBulkDeleteRequest,
    VideoBulkDownloadRequest,
    VideoBulkStatusUpdateRequest,
    VideoDownloadRequest,
    VideoStreamingResponse
)

from .artist import (
    ArtistResponse,
    ArtistCreateRequest,
    ArtistUpdateRequest,
    ArtistSearchRequest,
    ArtistBulkRequest,
    ArtistIMVDbImportRequest,
    ArtistStatsResponse
)

from .playlist import (
    PlaylistResponse,
    PlaylistEntryResponse,
    PlaylistCreateRequest,
    PlaylistUpdateRequest,
    PlaylistAddVideoRequest,
    PlaylistReorderRequest,
    DynamicPlaylistRequest,
    PlaylistFilterUpdateRequest
)

from .auth import (
    LoginRequest,
    LoginResponse,
    CredentialsRequest,
    UserSessionResponse,
    TokenResponse,
    OAuth2CallbackRequest
)

from .admin import (
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    UserRoleUpdateRequest,
    SystemStatusResponse,
    DashboardResponse,
    AuditLogResponse,
    SystemHealthResponse
)

from .settings import (
    SettingResponse,
    SettingUpdateRequest,
    BulkSettingsUpdateRequest,
    AllSettingsResponse,
    SchedulerStatusResponse,
    DatabaseConfigResponse
)

from .jobs import (
    JobRequest,
    JobResponse,
    JobProgressResponse,
    JobListResponse,
    JobStatusUpdateRequest,
    JobCancellationRequest
)

from .media import (
    VideoMetadataExtractionRequest,
    VideoMetadataResponse,
    VideoConversionRequest,
    VideoConversionResponse,
    VideoValidationRequest,
    VideoValidationResponse,
    BulkMediaRequest,
    BulkMediaResponse
)

from .ai import (
    ContentAnalysisRequest,
    ContentAnalysisResponse,
    TaggingRequest,
    TaggingResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    RecommendationRequest,
    RecommendationResponse
)

from .health import (
    HealthResponse,
    DetailedHealthResponse,
    ServiceHealthResponse,
    DatabaseHealthResponse,
    VersionInfoResponse
)

__all__ = [
    # Base classes
    "BaseRequest",
    "BaseResponse", 
    "PaginationRequest",
    "PaginationResponse",
    "BulkOperationRequest",
    "BulkOperationResponse",
    "TaskSubmissionResponse",
    "TaskStatusResponse",
    "ErrorResponse",
    
    # Common models
    "IdRequest",
    "StatusUpdateRequest",
    "ThumbnailSearchRequest",
    "FileUploadResponse",
    "SearchFilters",
    "SortOptions",
    
    # Video models
    "VideoResponse",
    "VideoCreateRequest",
    "VideoUpdateRequest",
    "VideoSearchRequest",
    "VideoBulkDeleteRequest",
    "VideoBulkDownloadRequest",
    "VideoBulkStatusUpdateRequest",
    "VideoDownloadRequest",
    "VideoStreamingResponse",
    
    # Artist models
    "ArtistResponse",
    "ArtistCreateRequest",
    "ArtistUpdateRequest",
    "ArtistSearchRequest",
    "ArtistBulkRequest",
    "ArtistIMVDbImportRequest",
    "ArtistStatsResponse",
    
    # Playlist models
    "PlaylistResponse",
    "PlaylistEntryResponse",
    "PlaylistCreateRequest",
    "PlaylistUpdateRequest",
    "PlaylistAddVideoRequest",
    "PlaylistReorderRequest",
    "DynamicPlaylistRequest",
    "PlaylistFilterUpdateRequest",
    
    # Auth models
    "LoginRequest",
    "LoginResponse",
    "CredentialsRequest",
    "UserSessionResponse",
    "TokenResponse",
    "OAuth2CallbackRequest",
    
    # Admin models
    "UserResponse",
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserRoleUpdateRequest",
    "SystemStatusResponse",
    "DashboardResponse",
    "AuditLogResponse",
    "SystemHealthResponse",
    
    # Settings models
    "SettingResponse",
    "SettingUpdateRequest",
    "BulkSettingsUpdateRequest",
    "AllSettingsResponse",
    "SchedulerStatusResponse",
    "DatabaseConfigResponse",
    
    # Job models
    "JobRequest",
    "JobResponse",
    "JobProgressResponse",
    "JobListResponse",
    "JobStatusUpdateRequest",
    "JobCancellationRequest",
    
    # Media models
    "VideoMetadataExtractionRequest",
    "VideoMetadataResponse",
    "VideoConversionRequest",
    "VideoConversionResponse",
    "VideoValidationRequest",
    "VideoValidationResponse",
    "BulkMediaRequest",
    "BulkMediaResponse",
    
    # AI models
    "ContentAnalysisRequest",
    "ContentAnalysisResponse",
    "TaggingRequest",
    "TaggingResponse",
    "BatchAnalysisRequest",
    "BatchAnalysisResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    
    # Health models
    "HealthResponse",
    "DetailedHealthResponse",
    "ServiceHealthResponse",
    "DatabaseHealthResponse",
    "VersionInfoResponse"
]