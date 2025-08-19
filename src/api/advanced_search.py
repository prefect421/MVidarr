"""
Advanced Search API endpoints for MVidarr 0.9.7 - Issue #73
Provides comprehensive search and filtering capabilities with saved presets,
autocomplete, and advanced query building.
"""

from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, g, jsonify, request
from marshmallow import Schema, ValidationError, fields

from src.database.connection import get_db
from src.database.search_models import SearchPresetType
from src.services.advanced_search_service import advanced_search_service
from src.services.search_presets_service import search_presets_service
from src.utils.logger import get_logger

advanced_search_bp = Blueprint("advanced_search", __name__, url_prefix="/search")
logger = get_logger("mvidarr.api.advanced_search")


# Request/Response schemas for validation
class SearchCriteriaSchema(Schema):
    """Schema for search criteria validation"""

    text_query = fields.Str(allow_none=True)
    search_fields = fields.List(
        fields.Str(), missing=["title", "description", "search_keywords"]
    )
    status = fields.List(fields.Str(), allow_none=True)
    quality = fields.List(fields.Str(), allow_none=True)
    year_range = fields.Dict(allow_none=True)
    duration_range = fields.Dict(allow_none=True)
    genres = fields.List(fields.Str(), allow_none=True)
    has_thumbnail = fields.Bool(allow_none=True)
    source = fields.List(fields.Str(), allow_none=True)
    artist_filters = fields.Dict(allow_none=True)
    created_after = fields.Str(allow_none=True)
    created_before = fields.Str(allow_none=True)
    discovered_after = fields.Str(allow_none=True)
    discovered_before = fields.Str(allow_none=True)
    sort_by = fields.Str(missing="created_at")
    sort_order = fields.Str(missing="desc")
    include_relevance = fields.Bool(missing=True)


class SearchRequestSchema(Schema):
    """Schema for search request validation"""

    search_criteria = fields.Nested(SearchCriteriaSchema, required=True)
    page = fields.Int(missing=1, validate=lambda x: x >= 1)
    per_page = fields.Int(missing=50, validate=lambda x: 1 <= x <= 100)


class PresetCreateSchema(Schema):
    """Schema for creating search presets"""

    name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    description = fields.Str(allow_none=True)
    search_criteria = fields.Nested(SearchCriteriaSchema, required=True)
    is_public = fields.Bool(missing=False)
    is_favorite = fields.Bool(missing=False)


class PresetUpdateSchema(Schema):
    """Schema for updating search presets"""

    name = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    search_criteria = fields.Nested(SearchCriteriaSchema, allow_none=True)
    is_public = fields.Bool(allow_none=True)
    is_favorite = fields.Bool(allow_none=True)


@advanced_search_bp.route("/videos", methods=["POST"])
def search_videos():
    """
    Advanced video search with comprehensive filtering

    POST /api/search/videos
    {
        "search_criteria": {
            "text_query": "rock music video",
            "status": ["DOWNLOADED", "WANTED"],
            "quality": ["1080p", "720p"],
            "year_range": {"min": 2010, "max": 2023},
            "duration_range": {"min": 180, "max": 600},
            "genres": ["rock", "alternative"],
            "has_thumbnail": true,
            "artist_filters": {
                "monitored": true,
                "source": ["imvdb", "manual"]
            },
            "sort_by": "created_at",
            "sort_order": "desc"
        },
        "page": 1,
        "per_page": 50
    }
    """
    try:
        # Validate request data
        schema = SearchRequestSchema()
        try:
            validated_data = schema.load(request.get_json() or {})
        except ValidationError as e:
            return (
                jsonify({"error": "Invalid request data", "details": e.messages}),
                400,
            )

        # Get user context
        user_id = getattr(g, "current_user_id", None)
        session_id = request.headers.get("X-Session-ID")

        # Perform search
        result = advanced_search_service.search_videos(
            search_criteria=validated_data["search_criteria"],
            page=validated_data["page"],
            per_page=validated_data["per_page"],
            user_id=user_id,
            session_id=session_id,
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in advanced video search: {str(e)}")
        return jsonify({"error": "Search failed", "message": str(e)}), 500


@advanced_search_bp.route("/presets", methods=["GET"])
def get_search_presets():
    """
    Get all search presets available to the current user

    GET /api/search/presets?include_public=true&include_system=true
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        include_public = request.args.get("include_public", "true").lower() == "true"
        include_system = request.args.get("include_system", "true").lower() == "true"

        presets = search_presets_service.get_user_presets(
            user_id=user_id,
            include_public=include_public,
            include_system=include_system,
        )

        return jsonify(
            {"presets": [preset.to_dict() for preset in presets], "total": len(presets)}
        )

    except Exception as e:
        logger.error(f"Error getting search presets: {str(e)}")
        return jsonify({"error": "Failed to get presets", "message": str(e)}), 500


@advanced_search_bp.route("/presets", methods=["POST"])
def create_search_preset():
    """
    Create a new search preset

    POST /api/search/presets
    {
        "name": "My Custom Search",
        "description": "High quality rock videos from 2020+",
        "search_criteria": { ... },
        "is_public": false,
        "is_favorite": false
    }
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # Validate request data
        schema = PresetCreateSchema()
        try:
            validated_data = schema.load(request.get_json() or {})
        except ValidationError as e:
            return (
                jsonify({"error": "Invalid request data", "details": e.messages}),
                400,
            )

        # Create the preset
        preset = search_presets_service.create_preset(
            user_id=user_id,
            name=validated_data["name"],
            search_criteria=validated_data["search_criteria"],
            description=validated_data.get("description"),
            is_public=validated_data["is_public"],
            is_favorite=validated_data["is_favorite"],
        )

        return (
            jsonify(
                {
                    "message": "Search preset created successfully",
                    "preset": preset.to_dict(),
                }
            ),
            201,
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating search preset: {str(e)}")
        return jsonify({"error": "Failed to create preset", "message": str(e)}), 500


@advanced_search_bp.route("/presets/<int:preset_id>", methods=["GET"])
def get_search_preset(preset_id: int):
    """
    Get a specific search preset by ID

    GET /api/search/presets/123
    """
    try:
        user_id = getattr(g, "current_user_id", None)

        preset = search_presets_service.get_preset_by_id(preset_id, user_id)

        if not preset:
            return jsonify({"error": "Preset not found or access denied"}), 404

        return jsonify(preset.to_dict())

    except Exception as e:
        logger.error(f"Error getting search preset: {str(e)}")
        return jsonify({"error": "Failed to get preset", "message": str(e)}), 500


@advanced_search_bp.route("/presets/<int:preset_id>", methods=["PUT"])
def update_search_preset(preset_id: int):
    """
    Update an existing search preset

    PUT /api/search/presets/123
    {
        "name": "Updated Search Name",
        "search_criteria": { ... }
    }
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # Validate request data
        schema = PresetUpdateSchema()
        try:
            validated_data = schema.load(request.get_json() or {})
        except ValidationError as e:
            return (
                jsonify({"error": "Invalid request data", "details": e.messages}),
                400,
            )

        # Update the preset
        preset = search_presets_service.update_preset(
            preset_id=preset_id,
            user_id=user_id,
            **{k: v for k, v in validated_data.items() if v is not None},
        )

        return jsonify(
            {
                "message": "Search preset updated successfully",
                "preset": preset.to_dict(),
            }
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating search preset: {str(e)}")
        return jsonify({"error": "Failed to update preset", "message": str(e)}), 500


@advanced_search_bp.route("/presets/<int:preset_id>", methods=["DELETE"])
def delete_search_preset(preset_id: int):
    """
    Delete a search preset

    DELETE /api/search/presets/123
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        search_presets_service.delete_preset(preset_id, user_id)

        return jsonify({"message": "Search preset deleted successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error deleting search preset: {str(e)}")
        return jsonify({"error": "Failed to delete preset", "message": str(e)}), 500


@advanced_search_bp.route("/presets/<int:preset_id>/use", methods=["POST"])
def use_search_preset(preset_id: int):
    """
    Use a search preset (marks it as used and returns the search criteria)

    POST /api/search/presets/123/use
    """
    try:
        user_id = getattr(g, "current_user_id", None)

        preset = search_presets_service.use_preset(preset_id, user_id)

        return jsonify(
            {
                "message": "Preset used successfully",
                "preset": preset.to_dict(),
                "search_criteria": preset.search_criteria,
            }
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error using search preset: {str(e)}")
        return jsonify({"error": "Failed to use preset", "message": str(e)}), 500


@advanced_search_bp.route("/presets/popular", methods=["GET"])
def get_popular_presets():
    """
    Get popular public search presets

    GET /api/search/presets/popular?limit=10
    """
    try:
        limit = min(request.args.get("limit", 10, type=int), 50)

        presets = search_presets_service.get_popular_presets(limit=limit)

        return jsonify(
            {"presets": [preset.to_dict() for preset in presets], "total": len(presets)}
        )

    except Exception as e:
        logger.error(f"Error getting popular presets: {str(e)}")
        return (
            jsonify({"error": "Failed to get popular presets", "message": str(e)}),
            500,
        )


@advanced_search_bp.route("/presets/search", methods=["POST"])
def search_with_preset():
    """
    Perform a search using a saved preset

    POST /api/search/presets/search
    {
        "preset_id": 123,
        "page": 1,
        "per_page": 50,
        "override_criteria": {
            "page": 2,
            "text_query": "additional search terms"
        }
    }
    """
    try:
        data = request.get_json() or {}
        preset_id = data.get("preset_id")
        page = data.get("page", 1)
        per_page = min(data.get("per_page", 50), 100)
        override_criteria = data.get("override_criteria", {})

        if not preset_id:
            return jsonify({"error": "preset_id is required"}), 400

        user_id = getattr(g, "current_user_id", None)
        session_id = request.headers.get("X-Session-ID")

        # Get and use the preset
        preset = search_presets_service.use_preset(preset_id, user_id)

        # Merge preset criteria with any overrides
        search_criteria = preset.search_criteria.copy()
        search_criteria.update(override_criteria)

        # Perform the search
        result = advanced_search_service.search_videos(
            search_criteria=search_criteria,
            page=page,
            per_page=per_page,
            user_id=user_id,
            session_id=session_id,
        )

        # Add preset information to the result
        result["used_preset"] = {
            "id": preset.id,
            "name": preset.name,
            "description": preset.description,
        }

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error searching with preset: {str(e)}")
        return jsonify({"error": "Search with preset failed", "message": str(e)}), 500


@advanced_search_bp.route("/export", methods=["POST"])
def export_search_results():
    """
    Export search results in various formats

    POST /api/search/export
    {
        "search_criteria": { ... },
        "format": "json",  // json, csv, xml
        "include_metadata": true
    }
    """
    try:
        data = request.get_json() or {}
        search_criteria = data.get("search_criteria", {})
        export_format = data.get("format", "json").lower()
        include_metadata = data.get("include_metadata", True)

        if export_format not in ["json", "csv", "xml"]:
            return jsonify({"error": "Invalid format. Supported: json, csv, xml"}), 400

        user_id = getattr(g, "current_user_id", None)
        session_id = request.headers.get("X-Session-ID")

        # Get all results (no pagination for export)
        result = advanced_search_service.search_videos(
            search_criteria=search_criteria,
            page=1,
            per_page=10000,  # Large number to get all results
            user_id=user_id,
            session_id=session_id,
        )

        # Track export event
        from src.services.advanced_search_service import SearchAnalyticsEvent

        advanced_search_service._track_search_event(
            user_id=user_id,
            session_id=session_id,
            event_type=SearchAnalyticsEvent.SEARCH_EXPORTED,
            search_criteria=search_criteria,
            result_count=result["total_results"],
            event_metadata={
                "format": export_format,
                "include_metadata": include_metadata,
            },
        )

        if export_format == "json":
            export_data = {
                "videos": result["videos"],
                "export_metadata": (
                    {
                        "exported_at": datetime.utcnow().isoformat(),
                        "total_results": result["total_results"],
                        "search_criteria": search_criteria,
                        "format": "json",
                    }
                    if include_metadata
                    else None
                ),
            }
            return jsonify(export_data)

        elif export_format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id",
                    "title",
                    "artist_name",
                    "status",
                    "quality",
                    "source",
                    "year",
                    "duration",
                    "genres",
                    "youtube_url",
                    "created_at",
                ],
            )

            writer.writeheader()
            for video in result["videos"]:
                # Flatten the video data for CSV
                csv_row = {
                    "id": video["id"],
                    "title": video["title"],
                    "artist_name": video["artist_name"],
                    "status": video["status"],
                    "quality": video["quality"],
                    "source": video["source"],
                    "year": video["year"],
                    "duration": video["duration"],
                    "genres": ", ".join(video["genres"]) if video["genres"] else "",
                    "youtube_url": video["youtube_url"],
                    "created_at": video["created_at"],
                }
                writer.writerow(csv_row)

            from flask import Response

            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=search_results.csv"
                },
            )

        elif export_format == "xml":
            import xml.etree.ElementTree as ET

            root = ET.Element("search_results")

            if include_metadata:
                metadata = ET.SubElement(root, "metadata")
                ET.SubElement(metadata, "exported_at").text = (
                    datetime.utcnow().isoformat()
                )
                ET.SubElement(metadata, "total_results").text = str(
                    result["total_results"]
                )
                ET.SubElement(metadata, "format").text = "xml"

            videos_element = ET.SubElement(root, "videos")

            for video in result["videos"]:
                video_element = ET.SubElement(videos_element, "video")
                for key, value in video.items():
                    if value is not None:
                        if isinstance(value, list):
                            list_element = ET.SubElement(video_element, key)
                            for item in value:
                                ET.SubElement(list_element, "item").text = str(item)
                        else:
                            ET.SubElement(video_element, key).text = str(value)

            from flask import Response

            return Response(
                ET.tostring(root, encoding="unicode"),
                mimetype="application/xml",
                headers={
                    "Content-Disposition": "attachment; filename=search_results.xml"
                },
            )

    except Exception as e:
        logger.error(f"Error exporting search results: {str(e)}")
        return jsonify({"error": "Export failed", "message": str(e)}), 500


@advanced_search_bp.route("/suggestions", methods=["GET"])
def get_search_suggestions():
    """
    Get search suggestions for autocomplete

    GET /api/search/suggestions?query=rock&limit=10&type=all
    """
    try:
        query = request.args.get("query", "").strip()
        limit = min(request.args.get("limit", 10, type=int), 50)
        suggestion_type = request.args.get(
            "type", "all"
        )  # all, artist, title, genre, keyword

        if not query or len(query) < 2:
            return jsonify({"suggestions": []})

        # This is a simplified implementation
        # In a full implementation, this would use the SearchSuggestion model
        # and machine learning algorithms for better suggestions

        suggestions = []

        with get_db() as db:
            # Get artist suggestions
            if suggestion_type in ["all", "artist"]:
                from src.database.models import Artist

                artists = (
                    db.query(Artist.name)
                    .filter(Artist.name.ilike(f"%{query}%"))
                    .limit(limit // 2 if suggestion_type == "all" else limit)
                    .all()
                )

                for artist in artists:
                    suggestions.append(
                        {
                            "text": artist.name,
                            "type": "artist",
                            "category": "Artist Name",
                        }
                    )

            # Get video title suggestions
            if suggestion_type in ["all", "title"]:
                from src.database.models import Video

                videos = (
                    db.query(Video.title)
                    .filter(Video.title.ilike(f"%{query}%"))
                    .distinct()
                    .limit(limit // 2 if suggestion_type == "all" else limit)
                    .all()
                )

                for video in videos:
                    suggestions.append(
                        {
                            "text": video.title,
                            "type": "title",
                            "category": "Video Title",
                        }
                    )

        # Sort by relevance (simple alphabetical for now)
        suggestions.sort(key=lambda x: x["text"].lower())

        return jsonify(
            {
                "suggestions": suggestions[:limit],
                "query": query,
                "total": len(suggestions),
            }
        )

    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        return jsonify({"error": "Failed to get suggestions", "message": str(e)}), 500


@advanced_search_bp.route("/analytics", methods=["GET"])
def get_search_analytics():
    """
    Get search analytics for the current user (admin/manager only)

    GET /api/search/analytics?days=30&user_id=123
    """
    try:
        # This would typically require admin/manager permissions
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # For now, return a simple analytics summary
        # In a full implementation, this would aggregate SearchAnalytics data

        return jsonify(
            {
                "message": "Search analytics endpoint - implementation in progress",
                "note": "This endpoint will provide search usage statistics, popular queries, performance metrics, etc.",
            }
        )

    except Exception as e:
        logger.error(f"Error getting search analytics: {str(e)}")
        return jsonify({"error": "Failed to get analytics", "message": str(e)}), 500


# Initialize system presets on first import
try:
    search_presets_service.create_system_presets()
except Exception as e:
    logger.warning(f"Could not create system presets on import: {str(e)}")
