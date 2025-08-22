"""
MusicBrainz API Integration Service for MVidarr 0.9.7
Provides authoritative music metadata from the MusicBrainz database.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import Artist, Video
from src.services.settings_service import settings
from src.utils.logger import get_logger

logger = get_logger("mvidarr.services.musicbrainz")


class MusicBrainzService:
    """Service for MusicBrainz API integration and metadata enrichment"""

    def __init__(self):
        self.base_url = "https://musicbrainz.org/ws/2"
        self.user_agent = "MVidarr/0.9.7 (https://github.com/prefect421/mvidarr)"
        self.rate_limit_delay = 1.0  # MusicBrainz rate limit: 1 request per second
        self.last_request_time = 0

        # Load settings
        self._settings_loaded = False
        self._enabled = None

    def _load_settings(self):
        """Load MusicBrainz settings from database"""
        if self._settings_loaded:
            return

        try:
            # MusicBrainz doesn't require API keys, but we allow disabling
            self._enabled = (
                settings.get("musicbrainz_enabled", "true").lower() == "true"
            )
            self._settings_loaded = True
            logger.debug(f"MusicBrainz settings loaded - enabled: {self._enabled}")
        except Exception as e:
            logger.error(f"Failed to load MusicBrainz settings: {e}")
            self._enabled = True  # Default to enabled since no auth required
            self._settings_loaded = True

    @property
    def enabled(self):
        """Check if MusicBrainz integration is enabled"""
        self._load_settings()
        return self._enabled

    def _safe_get_annotation(self, data: Dict) -> str:
        """Safely extract annotation text from API response"""
        annotation = data.get("annotation", "")
        if isinstance(annotation, str):
            return annotation
        elif isinstance(annotation, dict):
            return annotation.get("text", "")
        else:
            return ""

    def _respect_rate_limit(self):
        """Ensure we respect MusicBrainz rate limiting (1 request per second)"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to MusicBrainz API"""
        if not self.enabled:
            logger.debug("MusicBrainz integration is disabled")
            return None

        self._respect_rate_limit()

        if params is None:
            params = {}

        # Always request JSON format
        params["fmt"] = "json"

        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}

        url = f"{self.base_url}/{endpoint}"

        try:
            logger.debug(f"Making MusicBrainz request to: {url} with params: {params}")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            logger.error(f"MusicBrainz API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MusicBrainz response: {e}")
            return None

    def search_artist(self, artist_name: str) -> List[Dict]:
        """Search for artists by name in MusicBrainz database"""
        if not artist_name:
            return []

        # Clean and prepare search query
        query = quote_plus(artist_name.strip())

        params = {"query": f'artist:"{artist_name}"', "limit": 10, "offset": 0}

        data = self._make_request("artist", params)
        if not data:
            return []

        artists = []
        for artist in data.get("artists", []):
            # Calculate confidence based on name similarity
            confidence = self._calculate_name_similarity(
                artist_name, artist.get("name", "")
            )

            artist_info = {
                "mbid": artist.get("id"),
                "name": artist.get("name"),
                "sort_name": artist.get("sort-name"),
                "type": artist.get("type"),
                "country": artist.get("country"),
                "area": (
                    artist.get("area", {}).get("name") if artist.get("area") else None
                ),
                "begin_area": (
                    artist.get("begin-area", {}).get("name")
                    if artist.get("begin-area")
                    else None
                ),
                "life_span": artist.get("life-span", {}),
                "aliases": [alias.get("name") for alias in artist.get("aliases", [])],
                "tags": [tag.get("name") for tag in artist.get("tags", [])],
                "genres": [genre.get("name") for genre in artist.get("genres", [])],
                "confidence": confidence,
                "disambiguation": artist.get("disambiguation", ""),
            }
            artists.append(artist_info)

        # Sort by confidence score
        artists.sort(key=lambda x: x["confidence"], reverse=True)

        logger.info(f"Found {len(artists)} MusicBrainz artists for '{artist_name}'")
        return artists

    def get_artist_by_mbid(self, mbid: str) -> Optional[Dict]:
        """Get detailed artist information by MusicBrainz ID"""
        if not mbid:
            return None

        params = {
            "inc": "genres+tags+aliases+annotation+area-rels+artist-rels+label-rels+place-rels+recording-rels+release-rels+release-group-rels+series-rels+url-rels+work-rels"
        }

        data = self._make_request(f"artist/{mbid}", params)
        if not data:
            return None

        # Process relationships for additional metadata
        urls = {}
        relations_data = data.get("relations", [])
        if relations_data:
            for relation in relations_data:
                try:
                    rel_type = relation.get("type")
                    if rel_type in [
                        "official homepage",
                        "social network",
                        "streaming music",
                        "purchase for download",
                    ]:
                        url_info = relation.get("url")
                        if url_info and isinstance(url_info, dict):
                            url = url_info.get("resource", "")
                            if url:
                                if "spotify.com" in url:
                                    urls["spotify"] = url
                                elif "last.fm" in url or "lastfm" in url:
                                    urls["lastfm"] = url
                                elif "youtube.com" in url or "youtu.be" in url:
                                    urls["youtube"] = url
                                elif rel_type == "official homepage":
                                    urls["homepage"] = url
                except Exception as e:
                    # Skip problematic relations
                    continue

        artist_info = {
            "mbid": data.get("id"),
            "name": data.get("name"),
            "sort_name": data.get("sort-name"),
            "type": data.get("type"),
            "country": data.get("country"),
            "area": data.get("area", {}).get("name") if data.get("area") else None,
            "begin_area": (
                data.get("begin-area", {}).get("name")
                if data.get("begin-area")
                else None
            ),
            "life_span": data.get("life-span", {}),
            "aliases": [alias.get("name") for alias in data.get("aliases", [])],
            "tags": [tag.get("name") for tag in data.get("tags", [])],
            "genres": [genre.get("name") for genre in data.get("genres", [])],
            "disambiguation": data.get("disambiguation", ""),
            "annotation": self._safe_get_annotation(data),
            "external_urls": urls,
            "relations": data.get("relations", []),
        }

        logger.info(f"Retrieved MusicBrainz artist details for MBID: {mbid}")
        return artist_info

    def get_artist_releases(self, mbid: str, limit: int = 50) -> List[Dict]:
        """Get artist's releases from MusicBrainz"""
        if not mbid:
            return []

        params = {"artist": mbid, "limit": limit, "inc": "release-groups+media"}

        data = self._make_request("release", params)
        if not data:
            return []

        releases = []
        for release in data.get("releases", []):
            release_info = {
                "mbid": release.get("id"),
                "title": release.get("title"),
                "date": release.get("date"),
                "country": release.get("country"),
                "status": release.get("status"),
                "packaging": release.get("packaging"),
                "media": release.get("media", []),
                "release_group": release.get("release-group", {}),
            }
            releases.append(release_info)

        logger.info(f"Retrieved {len(releases)} releases for MBID: {mbid}")
        return releases

    def get_artist_metadata_for_enrichment(
        self, artist_name: str, mbid: str = None
    ) -> Optional[Dict]:
        """Get artist metadata formatted for the enrichment system"""
        if mbid:
            # Use existing MBID for direct lookup
            artist_data = self.get_artist_by_mbid(mbid)
        else:
            # Search for artist and use best match
            search_results = self.search_artist(artist_name)
            if not search_results:
                logger.warning(
                    f"No MusicBrainz results found for artist: {artist_name}"
                )
                return None

            # Use the highest confidence result
            best_match = search_results[0]
            if best_match.get("confidence", 0) < 0.7:
                logger.warning(
                    f"Low confidence MusicBrainz match for {artist_name}: {best_match.get('confidence', 0)}"
                )
                return None

            artist_data = self.get_artist_by_mbid(best_match.get("mbid"))

        if not artist_data:
            return None

        # Format for enrichment system
        metadata = {
            "name": artist_data.get("name"),
            "source": "musicbrainz",
            "confidence": 0.95,  # MusicBrainz is highly authoritative
            # Core metadata
            "genres": artist_data.get("genres", [])
            + artist_data.get("tags", [])[:5],  # Use tags as additional genres
            "mbid": artist_data.get("mbid"),
            # Rich metadata
            "country": artist_data.get("country"),
            "area": artist_data.get("area"),
            "disambiguation": artist_data.get("disambiguation"),
            "type": artist_data.get("type"),
            "aliases": artist_data.get("aliases", []),
            "life_span": artist_data.get("life_span", {}),
            # External links
            "external_urls": artist_data.get("external_urls", {}),
            # Source-specific data
            "raw_data": artist_data,
            "last_updated": datetime.now(),
        }

        # Extract formed year from life span if available
        life_span = artist_data.get("life_span", {})
        if life_span.get("begin"):
            try:
                formed_year = int(life_span["begin"].split("-")[0])
                metadata["formed_year"] = formed_year
            except (ValueError, AttributeError):
                pass

        logger.info(
            f"Successfully enriched artist metadata from MusicBrainz: {metadata['name']}"
        )
        return metadata

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two artist names"""
        if not name1 or not name2:
            return 0.0

        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()

        # Exact match
        if name1_clean == name2_clean:
            return 1.0

        # Simple substring matching for now
        # This could be enhanced with more sophisticated algorithms like Levenshtein distance
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return 0.8

        # Check for common word overlap
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())

        if words1 and words2:
            overlap = len(words1.intersection(words2))
            union = len(words1.union(words2))
            jaccard_similarity = overlap / union if union > 0 else 0
            return jaccard_similarity

        return 0.0

    def test_connection(self) -> bool:
        """Test MusicBrainz API connectivity"""
        try:
            # Simple test query
            data = self._make_request(
                "artist/5b11f4ce-a62d-471e-81fc-a69a8278c7da"
            )  # The Beatles MBID
            return data is not None and "id" in data
        except Exception as e:
            logger.error(f"MusicBrainz connection test failed: {e}")
            return False


# Create global instance
musicbrainz_service = MusicBrainzService()
