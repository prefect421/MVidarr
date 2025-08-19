"""
Metadata Enrichment API endpoints for Issue #75
Multi-source artist discovery and metadata aggregation endpoints
"""

import asyncio

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import Artist
from src.middleware.simple_auth_middleware import auth_required
from src.services.duplicate_detection_service import duplicate_detection_service
from src.services.metadata_enrichment_service import metadata_enrichment_service
from src.services.metadata_validation_service import metadata_validation_service
from src.utils.logger import get_logger

metadata_enrichment_bp = Blueprint(
    "metadata_enrichment", __name__, url_prefix="/metadata-enrichment"
)
logger = get_logger("mvidarr.api.metadata_enrichment")


@metadata_enrichment_bp.route("/enrich/<int:artist_id>", methods=["POST"])
@auth_required
def enrich_artist_metadata(artist_id: int):
    """Enrich metadata for a specific artist"""
    try:
        force_refresh = (
            request.json.get("force_refresh", False) if request.is_json else False
        )

        # Run async enrichment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                metadata_enrichment_service.enrich_artist_metadata(
                    artist_id, force_refresh
                )
            )
        finally:
            loop.close()

        if result.success:
            return (
                jsonify(
                    {
                        "success": True,
                        "artist_id": artist_id,
                        "sources_used": result.sources_used,
                        "metadata_found": result.metadata_found,
                        "confidence_score": result.confidence_score,
                        "processing_time": result.processing_time,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "artist_id": artist_id,
                        "errors": result.errors,
                        "processing_time": result.processing_time,
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Failed to enrich metadata for artist {artist_id}: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/enrich/video/<int:video_id>", methods=["POST"])
@auth_required
def enrich_video_metadata(video_id: int):
    """Enrich metadata for a specific video using multiple sources"""
    try:
        force_refresh = (
            request.json.get("force_refresh", False) if request.is_json else False
        )

        # Run async enrichment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                metadata_enrichment_service.enrich_video_metadata(
                    video_id, force_refresh
                )
            )
        finally:
            loop.close()

        if result.success:
            return (
                jsonify(
                    {
                        "success": True,
                        "video_id": video_id,
                        "enriched_fields": result.enriched_fields,
                        "metadata_sources": result.metadata_sources,
                        "errors": result.errors,
                        "processing_time": result.processing_time,
                        "message": f"Video metadata enriched from {', '.join(result.metadata_sources)}"
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "video_id": video_id,
                        "errors": result.errors,
                        "processing_time": result.processing_time,
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Failed to enrich metadata for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/enrich/batch", methods=["POST"])
@auth_required
def enrich_multiple_artists():
    """Enrich metadata for multiple artists"""
    try:
        if not request.is_json:
            return jsonify({"error": "JSON payload required"}), 400

        data = request.get_json()
        artist_ids = data.get("artist_ids", [])
        force_refresh = data.get("force_refresh", False)

        if not artist_ids:
            return jsonify({"error": "artist_ids list is required"}), 400

        if not isinstance(artist_ids, list):
            return jsonify({"error": "artist_ids must be a list"}), 400

        # Validate all IDs are integers
        try:
            artist_ids = [int(aid) for aid in artist_ids]
        except (ValueError, TypeError):
            return jsonify({"error": "All artist_ids must be valid integers"}), 400

        # Run async batch enrichment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                metadata_enrichment_service.enrich_multiple_artists(
                    artist_ids, force_refresh
                )
            )
        finally:
            loop.close()

        # Process results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        return (
            jsonify(
                {
                    "total_processed": len(results),
                    "successful": len(successful),
                    "failed": len(failed),
                    "results": [
                        {
                            "artist_id": r.artist_id,
                            "success": r.success,
                            "sources_used": r.sources_used,
                            "metadata_found": r.metadata_found if r.success else None,
                            "errors": r.errors if not r.success else None,
                            "confidence_score": r.confidence_score,
                            "processing_time": r.processing_time,
                        }
                        for r in results
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to enrich multiple artists: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/stats", methods=["GET"])
@auth_required
def get_enrichment_stats():
    """Get metadata enrichment statistics"""
    try:
        stats = metadata_enrichment_service.get_enrichment_stats()
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Failed to get enrichment stats: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/candidates", methods=["GET"])
@auth_required
def get_enrichment_candidates():
    """Get artists that are candidates for metadata enrichment"""
    try:
        # Parse query parameters
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        missing_external_ids = (
            request.args.get("missing_external_ids", "false").lower() == "true"
        )
        outdated_only = request.args.get("outdated_only", "false").lower() == "true"

        with get_db() as session:
            query = session.query(Artist)

            # Filter for artists missing external IDs OR lacking enriched metadata
            if missing_external_ids:
                # Include artists missing external IDs OR those with IDs but no enriched metadata
                query = query.filter(
                    (Artist.spotify_id.is_(None))
                    | (Artist.spotify_id == "")
                    | (Artist.lastfm_name.is_(None))
                    | (Artist.lastfm_name == "")
                    | (Artist.imvdb_id.is_(None))
                    | (Artist.imvdb_id == "")
                    | (Artist.imvdb_metadata.is_(None))
                    | (Artist.imvdb_metadata == {})
                    | (~Artist.imvdb_metadata.contains("enrichment_date"))
                )

            # Import datetime at function level since it's used later regardless of conditions
            from datetime import datetime, timedelta

            # Filter for outdated metadata (older than cache duration)
            if outdated_only:
                # Check for artists with outdated metadata
                cache_duration = timedelta(hours=24)  # Match service configuration
                cutoff_date = datetime.now() - cache_duration

                # Artists with no enrichment metadata or old enrichment data
                query = query.filter(
                    (Artist.imvdb_metadata.is_(None))
                    | (Artist.imvdb_metadata == {})
                    | (Artist.imvdb_metadata.op("->>")("enrichment_date").is_(None))
                )

            # Order by updated_at to prioritize older records
            query = query.order_by(Artist.updated_at.asc())

            # Apply pagination
            total = query.count()
            artists = query.offset(offset).limit(limit).all()

            candidates = []
            for artist in artists:
                # Determine what's missing (consistent with statistics logic)
                missing_ids = []
                if not artist.spotify_id or (
                    isinstance(artist.spotify_id, str) and not artist.spotify_id.strip()
                ):
                    missing_ids.append("spotify")
                if not artist.lastfm_name or (
                    isinstance(artist.lastfm_name, str)
                    and not artist.lastfm_name.strip()
                ):
                    missing_ids.append("lastfm")
                if not artist.imvdb_id or (
                    isinstance(artist.imvdb_id, str) and not artist.imvdb_id.strip()
                ):
                    missing_ids.append("imvdb")

                # Check metadata freshness
                metadata_age = None
                if isinstance(
                    artist.imvdb_metadata, dict
                ) and artist.imvdb_metadata.get("enrichment_date"):
                    try:
                        enrichment_date = datetime.fromisoformat(
                            artist.imvdb_metadata["enrichment_date"]
                        )
                        metadata_age = (datetime.now() - enrichment_date).days
                    except (ValueError, TypeError):
                        metadata_age = None

                candidates.append(
                    {
                        "id": artist.id,
                        "name": artist.name,
                        "missing_external_ids": missing_ids,
                        "metadata_age_days": metadata_age,
                        "has_enriched_metadata": isinstance(artist.imvdb_metadata, dict)
                        and "enrichment_date" in artist.imvdb_metadata,
                        "last_updated": (
                            artist.updated_at.isoformat() if artist.updated_at else None
                        ),
                    }
                )

            return (
                jsonify(
                    {
                        "candidates": candidates,
                        "pagination": {
                            "total": total,
                            "limit": limit,
                            "offset": offset,
                            "has_more": offset + limit < total,
                        },
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to get enrichment candidates: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/auto-enrich", methods=["POST"])
@auth_required
def auto_enrich_candidates():
    """Automatically enrich candidates based on criteria"""
    try:
        if not request.is_json:
            return jsonify({"error": "JSON payload required"}), 400

        data = request.get_json()
        limit = data.get("limit", 10)  # Process up to 10 artists at once
        missing_external_ids = data.get("missing_external_ids", True)
        outdated_only = data.get("outdated_only", False)
        force_refresh = data.get("force_refresh", False)

        # Import datetime at function level for consistency
        from datetime import datetime, timedelta

        with get_db() as session:
            query = session.query(Artist)

            # Apply same filters as candidates endpoint
            if missing_external_ids:
                query = query.filter(
                    (Artist.spotify_id.is_(None))
                    | (Artist.spotify_id == "")
                    | (Artist.lastfm_name.is_(None))
                    | (Artist.lastfm_name == "")
                    | (Artist.imvdb_id.is_(None))
                    | (Artist.imvdb_id == "")
                    | (Artist.imvdb_metadata.is_(None))
                    | (Artist.imvdb_metadata == {})
                    | (~Artist.imvdb_metadata.contains("enrichment_date"))
                )

            if outdated_only:
                cache_duration = timedelta(hours=24)
                cutoff_date = datetime.now() - cache_duration

                query = query.filter(
                    (Artist.imvdb_metadata.is_(None))
                    | (Artist.imvdb_metadata == {})
                    | (Artist.imvdb_metadata.op("->>")("enrichment_date").is_(None))
                )

            # Get candidates ordered by priority
            candidates = query.order_by(Artist.updated_at.asc()).limit(limit).all()

            if not candidates:
                return (
                    jsonify(
                        {
                            "message": "No candidates found for enrichment",
                            "processed": 0,
                            "results": [],
                        }
                    ),
                    200,
                )

            # Extract artist IDs
            artist_ids = [artist.id for artist in candidates]

        # Run batch enrichment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                metadata_enrichment_service.enrich_multiple_artists(
                    artist_ids, force_refresh
                )
            )
        finally:
            loop.close()

        # Process results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        return (
            jsonify(
                {
                    "message": f"Auto-enrichment completed for {len(results)} artists",
                    "processed": len(results),
                    "successful": len(successful),
                    "failed": len(failed),
                    "results": [
                        {
                            "artist_id": r.artist_id,
                            "success": r.success,
                            "sources_used": r.sources_used,
                            "confidence_score": r.confidence_score,
                            "errors": r.errors if not r.success else None,
                        }
                        for r in results
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to auto-enrich candidates: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/artist/<int:artist_id>/metadata", methods=["GET"])
def get_artist_enriched_metadata(artist_id: int):
    """Get enriched metadata for a specific artist"""
    try:
        with get_db() as session:
            artist = session.query(Artist).filter(Artist.id == artist_id).first()

            if not artist:
                return jsonify({"error": "Artist not found"}), 404

            # Extract enriched metadata from imvdb_metadata field
            enriched_metadata = {}
            if isinstance(artist.imvdb_metadata, dict):
                enriched_metadata = artist.imvdb_metadata

            return (
                jsonify(
                    {
                        "artist_id": artist.id,
                        "artist_name": artist.name,
                        "external_ids": {
                            "spotify": artist.spotify_id,
                            "lastfm": artist.lastfm_name,
                            "imvdb": artist.imvdb_id,
                            "musicbrainz": enriched_metadata.get("musicbrainz_id"),
                        },
                        "enriched_metadata": enriched_metadata,
                        "has_enriched_data": "enrichment_date" in enriched_metadata,
                        "last_updated": (
                            artist.updated_at.isoformat() if artist.updated_at else None
                        ),
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to get enriched metadata for artist {artist_id}: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/validate/<int:artist_id>", methods=["GET"])
def validate_artist_metadata(artist_id: int):
    """Validate metadata quality for a specific artist"""
    try:
        validation_result = metadata_validation_service.validate_artist_metadata(
            artist_id
        )

        return (
            jsonify(
                {
                    "artist_id": artist_id,
                    "is_valid": validation_result.is_valid,
                    "confidence_score": validation_result.confidence_score,
                    "data_quality_score": validation_result.data_quality_score,
                    "needs_enrichment": validation_result.needs_enrichment,
                    "issues": validation_result.issues,
                    "recommendations": validation_result.recommendations,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to validate metadata for artist {artist_id}: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/validation/report", methods=["GET"])
@auth_required
def get_validation_report():
    """Get a comprehensive validation report"""
    try:
        limit = request.args.get("limit", 100, type=int)
        report = metadata_validation_service.get_validation_report(limit)

        return jsonify(report), 200

    except Exception as e:
        logger.error(f"Failed to generate validation report: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/automation/run", methods=["POST"])
def run_automated_enrichment():
    """Run automated metadata enrichment"""
    try:
        if not request.is_json:
            data = {}
        else:
            data = request.get_json()

        limit = data.get("limit", 10)

        # Run automated enrichment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            stats = loop.run_until_complete(
                metadata_validation_service.auto_enrich_candidates(limit)
            )
        finally:
            loop.close()

        return (
            jsonify(
                {
                    "success": True,
                    "stats": {
                        "run_date": stats.run_date.isoformat(),
                        "candidates_found": stats.candidates_found,
                        "enriched_count": stats.enriched_count,
                        "validation_failures": stats.validation_failures,
                        "avg_confidence_improvement": stats.avg_confidence_improvement,
                        "total_processing_time": stats.total_processing_time,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to run automated enrichment: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/automation/schedule", methods=["POST"])
def schedule_automated_enrichment():
    """Schedule automated metadata enrichment"""
    try:
        success = metadata_validation_service.schedule_auto_enrichment()

        return (
            jsonify(
                {
                    "success": success,
                    "message": (
                        "Automated enrichment scheduled and executed"
                        if success
                        else "No artists were enriched"
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to schedule automated enrichment: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/duplicates/candidates", methods=["GET"])
@auth_required
def get_duplicate_candidates():
    """Get potential duplicate artist candidates"""
    try:
        limit = request.args.get("limit", 50, type=int)
        min_confidence = request.args.get("min_confidence", 0.5, type=float)

        candidates = duplicate_detection_service.find_duplicate_candidates(limit)

        # Filter by minimum confidence
        filtered_candidates = [
            c for c in candidates if c.match_confidence >= min_confidence
        ]

        results = []
        for candidate in filtered_candidates:
            results.append(
                {
                    "artist1_id": candidate.artist1_id,
                    "artist2_id": candidate.artist2_id,
                    "artist1_name": candidate.artist1_name,
                    "artist2_name": candidate.artist2_name,
                    "similarity_score": candidate.similarity_score,
                    "match_confidence": candidate.match_confidence,
                    "match_reasons": candidate.match_reasons,
                    "external_id_matches": candidate.external_id_matches,
                    "metadata_overlap": candidate.metadata_overlap,
                    "recommended_action": candidate.recommended_action,
                }
            )

        return (
            jsonify(
                {
                    "candidates": results,
                    "total_found": len(filtered_candidates),
                    "min_confidence": min_confidence,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get duplicate candidates: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/duplicates/stats", methods=["GET"])
def get_duplicate_stats():
    """Get duplicate detection statistics"""
    try:
        stats = duplicate_detection_service.get_duplicate_stats()
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Failed to get duplicate stats: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/duplicates/merge", methods=["POST"])
@auth_required
def merge_duplicate_artists():
    """Merge duplicate artists"""
    try:
        if not request.is_json:
            return jsonify({"error": "JSON payload required"}), 400

        data = request.get_json()
        primary_artist_id = data.get("primary_artist_id")
        duplicate_artist_id = data.get("duplicate_artist_id")
        auto_merge = data.get("auto_merge", False)

        if not primary_artist_id or not duplicate_artist_id:
            return (
                jsonify(
                    {"error": "primary_artist_id and duplicate_artist_id are required"}
                ),
                400,
            )

        result = duplicate_detection_service.merge_duplicate_artists(
            primary_artist_id, duplicate_artist_id, auto_merge
        )

        if result.success:
            return (
                jsonify(
                    {
                        "success": True,
                        "primary_artist_id": result.primary_artist_id,
                        "merged_artist_id": result.merged_artist_id,
                        "videos_moved": result.videos_moved,
                        "downloads_moved": result.downloads_moved,
                        "metadata_merged": result.metadata_merged,
                    }
                ),
                200,
            )
        else:
            return jsonify({"success": False, "errors": result.errors}), 400

    except Exception as e:
        logger.error(f"Failed to merge duplicate artists: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/duplicates/auto-merge", methods=["POST"])
@auth_required
def auto_merge_duplicates():
    """Automatically merge high-confidence duplicate pairs"""
    try:
        if not request.is_json:
            data = {}
        else:
            data = request.get_json()

        limit = data.get("limit", 10)

        results = duplicate_detection_service.auto_merge_high_confidence_duplicates(
            limit
        )

        successful_merges = [r for r in results if r.success]
        failed_merges = [r for r in results if not r.success]

        return (
            jsonify(
                {
                    "total_processed": len(results),
                    "successful_merges": len(successful_merges),
                    "failed_merges": len(failed_merges),
                    "results": [
                        {
                            "primary_artist_id": r.primary_artist_id,
                            "merged_artist_id": r.merged_artist_id,
                            "success": r.success,
                            "videos_moved": r.videos_moved if r.success else None,
                            "downloads_moved": r.downloads_moved if r.success else None,
                            "errors": r.errors if not r.success else None,
                        }
                        for r in results
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to auto-merge duplicates: {e}")
        return jsonify({"error": str(e)}), 500


@metadata_enrichment_bp.route("/blank-metadata-report/<int:artist_id>", methods=["GET"])
@auth_required
def get_blank_metadata_report(artist_id: int):
    """Get detailed report of blank/missing metadata fields for specific artist"""
    try:
        validation_service = metadata_validation_service
        report = validation_service.get_blank_metadata_report(artist_id)
        
        if "error" in report:
            return jsonify(report), 404 if "not found" in report["error"].lower() else 500
            
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"Failed to generate blank metadata report for artist {artist_id}: {e}")
        return jsonify({"error": str(e)}), 500
