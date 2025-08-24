"""
Discogs API integration service for comprehensive release information and music metadata
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from urllib.parse import quote

import requests

from src.services.settings_service import settings
from src.utils.logger import get_logger

logger = get_logger("mvidarr.services.discogs")


class DiscogsService:
    """Service for Discogs API integration"""

    def __init__(self):
        self.base_url = "https://api.discogs.com"
        self.user_agent = "MVidarr/0.9.8 (https://github.com/prefect421/mvidarr)"

        # Discogs requires User-Agent header
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/vnd.discogs.v2.discogs+json",
            }
        )

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Discogs allows 60 requests per minute

        # Configuration
        self.enabled = settings.get_bool("discogs_enabled", True)
        self.token = settings.get("discogs_token", "")  # Optional personal access token

        if self.token:
            self.session.headers.update(
                {"Authorization": f"Discogs token={self.token}"}
            )
            self._min_request_interval = 0.25  # Authenticated users get higher limits

        # Cache settings
        self.cache_duration_hours = 24
        self._artist_cache = {}
        self._release_cache = {}

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to Discogs API"""
        if not self.enabled:
            logger.debug("Discogs integration is disabled")
            return None

        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.get(url, params=params or {})
            self._last_request_time = time.time()

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited - wait longer
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited by Discogs API, waiting {retry_after}s")
                time.sleep(retry_after)
                return self._make_request(endpoint, params)  # Retry once
            elif response.status_code == 404:
                logger.debug(f"Discogs API returned 404 for {endpoint}")
                return None
            else:
                logger.error(
                    f"Discogs API error {response.status_code}: {response.text}"
                )
                return None

        except requests.RequestException as e:
            logger.error(f"Discogs API request failed: {e}")
            return None

    def search_artist(self, artist_name: str, limit: int = 10) -> Optional[List[Dict]]:
        """Search for artist on Discogs"""
        if not artist_name:
            return None

        # Check cache first
        cache_key = f"artist_search_{artist_name.lower()}"
        if cache_key in self._artist_cache:
            cached_result, cached_time = self._artist_cache[cache_key]
            if datetime.now() - cached_time < timedelta(
                hours=self.cache_duration_hours
            ):
                return cached_result

        logger.debug(f"Searching Discogs for artist: {artist_name}")

        params = {"q": artist_name, "type": "artist", "per_page": limit}

        result = self._make_request("database/search", params)
        if not result or "results" not in result:
            return None

        artists = []
        for item in result["results"]:
            artist_data = {
                "id": item.get("id"),
                "title": item.get("title"),
                "resource_url": item.get("resource_url"),
                "uri": item.get("uri"),
                "thumb": item.get("thumb"),
                "cover_image": item.get("cover_image"),
                "profile": item.get("profile", ""),
                "aliases": item.get("aliases", []),
                "real_name": item.get("real_name"),
                "confidence": self._calculate_name_similarity(
                    artist_name, item.get("title", "")
                ),
            }
            artists.append(artist_data)

        # Sort by confidence
        artists.sort(key=lambda x: x["confidence"], reverse=True)

        # Cache result
        self._artist_cache[cache_key] = (artists, datetime.now())

        return artists

    def get_artist_details(self, discogs_artist_id: Union[str, int]) -> Optional[Dict]:
        """Get detailed artist information from Discogs"""
        if not discogs_artist_id:
            return None

        # Check cache first
        cache_key = f"artist_details_{discogs_artist_id}"
        if cache_key in self._artist_cache:
            cached_result, cached_time = self._artist_cache[cache_key]
            if datetime.now() - cached_time < timedelta(
                hours=self.cache_duration_hours
            ):
                return cached_result

        logger.debug(f"Getting Discogs artist details for ID: {discogs_artist_id}")

        result = self._make_request(f"artists/{discogs_artist_id}")
        if not result:
            return None

        artist_details = {
            "id": result.get("id"),
            "name": result.get("name"),
            "real_name": result.get("real_name"),
            "profile": result.get("profile", ""),
            "images": result.get("images", []),
            "aliases": result.get("aliases", []),
            "namevariations": result.get("namevariations", []),
            "urls": result.get("urls", []),
            "data_quality": result.get("data_quality"),
            "resource_url": result.get("resource_url"),
            "uri": result.get("uri"),
            "members": result.get("members", []),
            "groups": result.get("groups", []),
        }

        # Cache result
        self._artist_cache[cache_key] = (artist_details, datetime.now())

        return artist_details

    def get_artist_releases(
        self,
        discogs_artist_id: Union[str, int],
        release_type: str = None,
        limit: int = 50,
    ) -> Optional[List[Dict]]:
        """Get artist's releases from Discogs"""
        if not discogs_artist_id:
            return None

        cache_key = f"artist_releases_{discogs_artist_id}_{release_type}_{limit}"
        if cache_key in self._release_cache:
            cached_result, cached_time = self._release_cache[cache_key]
            if datetime.now() - cached_time < timedelta(
                hours=self.cache_duration_hours
            ):
                return cached_result

        logger.debug(f"Getting Discogs releases for artist ID: {discogs_artist_id}")

        params = {
            "per_page": min(limit, 100),  # Discogs max is 100
            "sort": "year",
            "sort_order": "desc",
        }

        if release_type:
            # Discogs release types: release, master, single, album, etc.
            params["type"] = release_type

        result = self._make_request(f"artists/{discogs_artist_id}/releases", params)
        if not result or "releases" not in result:
            return None

        releases = []
        for release in result["releases"]:
            release_data = {
                "id": release.get("id"),
                "title": release.get("title"),
                "year": release.get("year"),
                "format": release.get("format"),
                "label": release.get("label"),
                "catno": release.get("catno"),
                "resource_url": release.get("resource_url"),
                "role": release.get("role"),
                "type": release.get("type"),
                "status": release.get("status"),
                "thumb": release.get("thumb"),
                "artist": release.get("artist"),
                "main_release": release.get("main_release"),
            }
            releases.append(release_data)

        # Cache result
        self._release_cache[cache_key] = (releases, datetime.now())

        return releases

    def get_release_details(
        self, discogs_release_id: Union[str, int]
    ) -> Optional[Dict]:
        """Get detailed release information"""
        if not discogs_release_id:
            return None

        cache_key = f"release_details_{discogs_release_id}"
        if cache_key in self._release_cache:
            cached_result, cached_time = self._release_cache[cache_key]
            if datetime.now() - cached_time < timedelta(
                hours=self.cache_duration_hours
            ):
                return cached_result

        logger.debug(f"Getting Discogs release details for ID: {discogs_release_id}")

        result = self._make_request(f"releases/{discogs_release_id}")
        if not result:
            return None

        release_details = {
            "id": result.get("id"),
            "title": result.get("title"),
            "year": result.get("year"),
            "released": result.get("released"),
            "genres": result.get("genres", []),
            "styles": result.get("styles", []),
            "labels": result.get("labels", []),
            "formats": result.get("formats", []),
            "country": result.get("country"),
            "artists": result.get("artists", []),
            "tracklist": result.get("tracklist", []),
            "identifiers": result.get("identifiers", []),
            "videos": result.get("videos", []),
            "companies": result.get("companies", []),
            "images": result.get("images", []),
            "notes": result.get("notes", ""),
            "data_quality": result.get("data_quality"),
            "community": result.get("community", {}),
            "estimated_weight": result.get("estimated_weight"),
            "lowest_price": result.get("lowest_price"),
            "num_for_sale": result.get("num_for_sale"),
            "resource_url": result.get("resource_url"),
            "uri": result.get("uri"),
        }

        # Cache result
        self._release_cache[cache_key] = (release_details, datetime.now())

        return release_details

    def search_release(self, query: str, limit: int = 10) -> Optional[List[Dict]]:
        """Search for releases on Discogs"""
        if not query:
            return None

        logger.debug(f"Searching Discogs for release: {query}")

        params = {"q": query, "type": "release", "per_page": limit}

        result = self._make_request("database/search", params)
        if not result or "results" not in result:
            return None

        releases = []
        for item in result["results"]:
            release_data = {
                "id": item.get("id"),
                "title": item.get("title"),
                "year": item.get("year"),
                "format": item.get("format", []),
                "label": item.get("label", []),
                "genre": item.get("genre", []),
                "style": item.get("style", []),
                "country": item.get("country"),
                "catno": item.get("catno"),
                "thumb": item.get("thumb"),
                "cover_image": item.get("cover_image"),
                "resource_url": item.get("resource_url"),
                "uri": item.get("uri"),
                "confidence": self._calculate_release_similarity(
                    query, item.get("title", "")
                ),
            }
            releases.append(release_data)

        # Sort by confidence and year (newer releases first for same confidence)
        releases.sort(
            key=lambda x: (x["confidence"], x.get("year", 0) or 0), reverse=True
        )

        return releases

    def get_artist_metadata_for_enrichment(self, artist_name: str) -> Optional[Dict]:
        """Get artist metadata formatted for metadata enrichment system"""
        try:
            # Search for artist
            search_results = self.search_artist(artist_name, limit=5)
            if not search_results:
                return None

            # Get the best match
            best_match = search_results[0]
            if best_match["confidence"] < 0.6:  # Require reasonable confidence
                logger.debug(
                    f"Low confidence match for {artist_name} on Discogs: {best_match['confidence']}"
                )
                return None

            # Get detailed artist information
            artist_details = self.get_artist_details(best_match["id"])
            if not artist_details:
                return None

            # Get artist's releases for additional metadata
            releases = self.get_artist_releases(best_match["id"], limit=20)

            # Extract genres from releases
            genres = set()
            if releases:
                for release in releases[:10]:  # Check first 10 releases
                    release_details = self.get_release_details(release["id"])
                    if release_details:
                        genres.update(release_details.get("genres", []))
                        genres.update(release_details.get("styles", []))

            # Format for enrichment system
            metadata = {
                "name": artist_details["name"],
                "confidence": best_match["confidence"],
                "genres": list(genres)[:10],  # Limit to 10 genres
                "biography": artist_details.get("profile", ""),
                "discogs_id": str(artist_details["id"]),
                "real_name": artist_details.get("real_name"),
                "aliases": artist_details.get("aliases", []),
                "name_variations": artist_details.get("namevariations", []),
                "external_urls": artist_details.get("urls", []),
                "images": artist_details.get("images", []),
                "members": [
                    member.get("name") for member in artist_details.get("members", [])
                ],
                "groups": [
                    group.get("name") for group in artist_details.get("groups", [])
                ],
                "data_quality": artist_details.get("data_quality"),
                "discography_count": len(releases) if releases else 0,
                "raw_data": {
                    "artist_details": artist_details,
                    "sample_releases": releases[:5] if releases else [],
                },
            }

            return metadata

        except Exception as e:
            logger.error(f"Error getting Discogs metadata for {artist_name}: {e}")
            return None

    def get_label_information(self, label_name: str) -> Optional[Dict]:
        """Get record label information from Discogs"""
        logger.debug(f"Searching Discogs for label: {label_name}")

        params = {"q": label_name, "type": "label", "per_page": 5}

        result = self._make_request("database/search", params)
        if not result or "results" not in result or not result["results"]:
            return None

        # Get the best match
        best_match = result["results"][0]
        label_id = best_match.get("id")

        if not label_id:
            return None

        # Get detailed label information
        label_details = self._make_request(f"labels/{label_id}")
        if not label_details:
            return None

        return {
            "id": label_details.get("id"),
            "name": label_details.get("name"),
            "profile": label_details.get("profile", ""),
            "contact_info": label_details.get("contact_info", ""),
            "parent_label": label_details.get("parent_label"),
            "sublabels": label_details.get("sublabels", []),
            "urls": label_details.get("urls", []),
            "images": label_details.get("images", []),
            "data_quality": label_details.get("data_quality"),
            "resource_url": label_details.get("resource_url"),
        }

    def _calculate_name_similarity(self, query: str, result: str) -> float:
        """Calculate similarity between query and result names"""
        if not query or not result:
            return 0.0

        query_clean = query.lower().strip()
        result_clean = result.lower().strip()

        # Exact match
        if query_clean == result_clean:
            return 1.0

        # Check if one contains the other
        if query_clean in result_clean or result_clean in query_clean:
            return 0.85

        # Token-based similarity
        query_tokens = set(query_clean.split())
        result_tokens = set(result_clean.split())

        if not query_tokens or not result_tokens:
            return 0.0

        intersection = query_tokens.intersection(result_tokens)
        union = query_tokens.union(result_tokens)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_release_similarity(self, query: str, result: str) -> float:
        """Calculate similarity between query and result for releases"""
        # Similar to name similarity but can be enhanced for release-specific matching
        return self._calculate_name_similarity(query, result)

    def get_service_status(self) -> Dict:
        """Get service status and configuration"""
        return {
            "enabled": self.enabled,
            "authenticated": bool(self.token),
            "rate_limit_interval": self._min_request_interval,
            "cache_duration_hours": self.cache_duration_hours,
            "cached_artists": len(self._artist_cache),
            "cached_releases": len(self._release_cache),
            "base_url": self.base_url,
        }

    def clear_cache(self):
        """Clear all cached data"""
        self._artist_cache.clear()
        self._release_cache.clear()
        logger.info("Discogs service cache cleared")


# Global instance
discogs_service = DiscogsService()
