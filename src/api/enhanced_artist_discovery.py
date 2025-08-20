"""
Enhanced Artist Discovery API endpoints for MVidarr 0.9.7 - Issue #75
Multi-source artist discovery with metadata enrichment and recommendations.
"""

from typing import Dict, List
from flask import Blueprint, jsonify, request, g
from marshmallow import Schema, ValidationError, fields

from src.middleware.simple_auth_middleware import auth_required
from src.services.enhanced_artist_discovery_service import enhanced_artist_discovery_service
from src.database.connection import get_db
from src.database.models import Artist
from src.utils.logger import get_logger

enhanced_discovery_bp = Blueprint("enhanced_discovery", __name__, url_prefix="/enhanced_discovery")
logger = get_logger("mvidarr.api.enhanced_discovery")


# Request/Response schemas
class DiscoverySearchSchema(Schema):
    """Schema for artist discovery search"""
    query = fields.Str(required=True, validate=lambda x: len(x.strip()) >= 2)
    max_results = fields.Int(missing=50, validate=lambda x: 1 <= x <= 100)


class EnrichmentRequestSchema(Schema):
    """Schema for artist enrichment request"""
    artist_ids = fields.List(fields.Int(), required=True, validate=lambda x: len(x) <= 50)


class RecommendationRequestSchema(Schema):
    """Schema for recommendation request"""
    artist_id = fields.Int(required=True)
    limit = fields.Int(missing=20, validate=lambda x: 1 <= x <= 50)


@enhanced_discovery_bp.route("/search", methods=["POST"])
@auth_required
def discover_artists_multi_source():
    """
    Discover artists from multiple sources with intelligent ranking
    
    POST /api/enhanced_discovery/search
    {
        "query": "Taylor Swift",
        "max_results": 25
    }
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # Validate request
        schema = DiscoverySearchSchema()
        try:
            data = schema.load(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"error": "Invalid request data", "details": e.messages}), 400

        query = data["query"]
        max_results = data["max_results"]

        logger.info(f"Enhanced discovery search for '{query}' by user {user_id}")

        # Perform multi-source discovery
        discovered_artists = enhanced_artist_discovery_service.discover_artists_multi_source(
            search_query=query,
            max_results=max_results
        )

        # Convert to JSON-serializable format
        results = []
        for artist_metadata in discovered_artists:
            result = {
                "name": artist_metadata.name,
                "source": artist_metadata.source.value,
                "confidence": round(artist_metadata.confidence, 3),
                "genres": artist_metadata.genres,
                "biography": artist_metadata.biography[:500] + "..." if len(artist_metadata.biography or "") > 500 else artist_metadata.biography,
                "formed_year": artist_metadata.formed_year,
                "country": artist_metadata.country,
                "image_url": artist_metadata.image_url,
                "external_ids": artist_metadata.external_ids,
                "similar_artists": artist_metadata.similar_artists[:10],  # Limit similar artists
                "popularity_score": round(artist_metadata.popularity_score, 3),
                "quality_score": artist_metadata.quality_score.name,
                "last_updated": artist_metadata.last_updated.isoformat()
            }
            results.append(result)

        return jsonify({
            "success": True,
            "query": query,
            "total_results": len(results),
            "artists": results
        })

    except Exception as e:
        logger.error(f"Error in multi-source artist discovery: {e}")
        return jsonify({"error": "Discovery failed", "message": str(e)}), 500


@enhanced_discovery_bp.route("/enrich", methods=["POST"])
@auth_required
def enrich_artists():
    """
    Enrich existing artists with metadata from multiple sources
    
    POST /api/enhanced_discovery/enrich
    {
        "artist_ids": [1, 2, 3, 4, 5]
    }
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # Validate request
        schema = EnrichmentRequestSchema()
        try:
            data = schema.load(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"error": "Invalid request data", "details": e.messages}), 400

        artist_ids = data["artist_ids"]

        logger.info(f"Enriching {len(artist_ids)} artists for user {user_id}")

        # Perform enrichment for each artist
        enrichment_results = []
        successful_enrichments = 0
        failed_enrichments = 0

        for artist_id in artist_ids:
            try:
                success = enhanced_artist_discovery_service.enrich_artist_metadata(artist_id)
                
                # Get updated artist info
                with get_db() as db:
                    artist = db.query(Artist).filter(Artist.id == artist_id).first()
                    if artist:
                        result = {
                            "artist_id": artist_id,
                            "name": artist.name,
                            "success": success,
                            "enriched_fields": []
                        }
                        
                        # Check what was enriched (simplified check)
                        if artist.genres:
                            result["enriched_fields"].append("genres")
                        if artist.biography:
                            result["enriched_fields"].append("biography")
                        if artist.country:
                            result["enriched_fields"].append("country")
                            
                        enrichment_results.append(result)
                        
                        if success:
                            successful_enrichments += 1
                        else:
                            failed_enrichments += 1
                    else:
                        enrichment_results.append({
                            "artist_id": artist_id,
                            "name": "Unknown",
                            "success": False,
                            "error": "Artist not found"
                        })
                        failed_enrichments += 1
                        
            except Exception as e:
                logger.error(f"Error enriching artist {artist_id}: {e}")
                enrichment_results.append({
                    "artist_id": artist_id,
                    "name": "Unknown",
                    "success": False,
                    "error": str(e)
                })
                failed_enrichments += 1

        return jsonify({
            "success": True,
            "total_artists": len(artist_ids),
            "successful_enrichments": successful_enrichments,
            "failed_enrichments": failed_enrichments,
            "results": enrichment_results
        })

    except Exception as e:
        logger.error(f"Error in artist enrichment: {e}")
        return jsonify({"error": "Enrichment failed", "message": str(e)}), 500


@enhanced_discovery_bp.route("/duplicates", methods=["GET"])
@auth_required
def detect_duplicate_artists():
    """
    Detect potential duplicate artists in the library
    
    GET /api/enhanced_discovery/duplicates?limit=50
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        limit = min(request.args.get("limit", 50, type=int), 100)

        logger.info(f"Detecting duplicate artists (limit: {limit}) for user {user_id}")

        # Detect duplicates
        duplicates = enhanced_artist_discovery_service.detect_duplicate_artists(limit)

        # Format results
        duplicate_results = []
        for duplicate in duplicates:
            # Get artist names
            with get_db() as db:
                artist1 = db.query(Artist).filter(Artist.id == duplicate.artist_id).first()
                artist2 = db.query(Artist).filter(Artist.id == duplicate.candidate_id).first()

                if artist1 and artist2:
                    result = {
                        "artist_1": {
                            "id": artist1.id,
                            "name": artist1.name,
                            "genres": artist1.genres
                        },
                        "artist_2": {
                            "id": artist2.id,
                            "name": artist2.name,
                            "genres": artist2.genres
                        },
                        "similarity_score": round(duplicate.similarity_score, 3),
                        "matching_factors": duplicate.matching_factors,
                        "confidence": round(duplicate.confidence, 3),
                        "suggested_action": duplicate.suggested_action
                    }
                    duplicate_results.append(result)

        return jsonify({
            "success": True,
            "total_duplicates": len(duplicate_results),
            "duplicates": duplicate_results
        })

    except Exception as e:
        logger.error(f"Error detecting duplicates: {e}")
        return jsonify({"error": "Duplicate detection failed", "message": str(e)}), 500


@enhanced_discovery_bp.route("/recommendations", methods=["POST"])
@auth_required
def get_artist_recommendations():
    """
    Get artist recommendations based on library content
    
    POST /api/enhanced_discovery/recommendations
    {
        "artist_id": 123,
        "limit": 20
    }
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # Validate request
        schema = RecommendationRequestSchema()
        try:
            data = schema.load(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"error": "Invalid request data", "details": e.messages}), 400

        artist_id = data["artist_id"]
        limit = data["limit"]

        # Verify artist exists
        with get_db() as db:
            artist = db.query(Artist).filter(Artist.id == artist_id).first()
            if not artist:
                return jsonify({"error": "Artist not found"}), 404

        logger.info(f"Getting recommendations for artist '{artist.name}' (ID: {artist_id})")

        # Get recommendations
        recommendations = enhanced_artist_discovery_service.get_artist_recommendations(
            artist_id=artist_id,
            limit=limit
        )

        # Format results
        recommendation_results = []
        for rec in recommendations:
            result = {
                "name": rec.name,
                "source": rec.source.value,
                "confidence": round(rec.confidence, 3),
                "genres": rec.genres,
                "biography": rec.biography[:300] + "..." if len(rec.biography or "") > 300 else rec.biography,
                "image_url": rec.image_url,
                "external_ids": rec.external_ids,
                "popularity_score": round(rec.popularity_score, 3),
                "quality_score": rec.quality_score.name
            }
            recommendation_results.append(result)

        return jsonify({
            "success": True,
            "base_artist": {
                "id": artist.id,
                "name": artist.name,
                "genres": artist.genres
            },
            "total_recommendations": len(recommendation_results),
            "recommendations": recommendation_results
        })

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({"error": "Recommendations failed", "message": str(e)}), 500


@enhanced_discovery_bp.route("/stats", methods=["GET"])
@auth_required
def get_discovery_stats():
    """
    Get enhanced discovery statistics and metadata quality metrics
    
    GET /api/enhanced_discovery/stats
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        logger.info(f"Getting discovery stats for user {user_id}")

        with get_db() as db:
            # Basic library stats
            total_artists = db.query(Artist).count()
            
            # Metadata completeness
            artists_with_genres = db.query(Artist).filter(Artist.genres.isnot(None)).filter(Artist.genres != "").count()
            artists_with_biography = db.query(Artist).filter(Artist.biography.isnot(None)).filter(Artist.biography != "").count()
            artists_with_country = db.query(Artist).filter(Artist.country.isnot(None)).filter(Artist.country != "").count()

            # Calculate completeness percentages
            genre_completeness = (artists_with_genres / total_artists * 100) if total_artists > 0 else 0
            biography_completeness = (artists_with_biography / total_artists * 100) if total_artists > 0 else 0
            country_completeness = (artists_with_country / total_artists * 100) if total_artists > 0 else 0

            # Overall metadata quality score
            overall_completeness = (genre_completeness + biography_completeness + country_completeness) / 3

            stats = {
                "library_overview": {
                    "total_artists": total_artists,
                    "metadata_completeness": {
                        "genres": {
                            "count": artists_with_genres,
                            "percentage": round(genre_completeness, 1)
                        },
                        "biographies": {
                            "count": artists_with_biography,
                            "percentage": round(biography_completeness, 1)
                        },
                        "countries": {
                            "count": artists_with_country,
                            "percentage": round(country_completeness, 1)
                        },
                        "overall_score": round(overall_completeness, 1)
                    }
                },
                "discovery_sources": {
                    "imvdb": {"enabled": True, "description": "Internet Music Video Database"},
                    "spotify": {"enabled": True, "description": "Spotify Music Platform"},
                    "lastfm": {"enabled": True, "description": "Last.fm Social Music"},
                    "wikipedia": {"enabled": True, "description": "Wikipedia Encyclopedia"}
                },
                "recommendations": {
                    "available": True,
                    "sources": ["genre_based", "similar_artists", "collaborative_filtering"]
                }
            }

        return jsonify({
            "success": True,
            "stats": stats
        })

    except Exception as e:
        logger.error(f"Error getting discovery stats: {e}")
        return jsonify({"error": "Stats retrieval failed", "message": str(e)}), 500