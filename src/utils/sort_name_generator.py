"""
Sort Name Generator Utility

Generates sort names for artists following standard library/music collection conventions.
Used to implement Issue #17: automatic sort name generation with intelligent formatting.
"""

import re
from typing import Optional


class SortNameGenerator:
    """Generate sort names for artists with intelligent formatting rules"""

    # Common articles/prefixes to move to the end
    ARTICLES = ["the", "a", "an"]

    # Special character patterns to remove or normalize
    SPECIAL_CHARS_PATTERN = re.compile(
        r'[""' "`]"
    )  # Remove curly quotes and backticks, but preserve apostrophes
    MULTIPLE_SPACES_PATTERN = re.compile(r"\s+")  # Collapse multiple spaces

    @classmethod
    def generate_sort_name(cls, artist_name: str) -> str:
        """
        Generate a sort name from an artist name.

        Rules:
        1. Move common articles to the end: "The Beatles" -> "Beatles, The"
        2. Strip special characters: "Weird" Al Yankovic -> "Weird Al Yankovic"
        3. Normalize whitespace
        4. Handle edge cases

        Args:
            artist_name: Original artist name

        Returns:
            Sort name following library conventions
        """
        if not artist_name or not artist_name.strip():
            return ""

        # Start with the original name
        sort_name = artist_name.strip()

        # Remove special characters (quotes, etc.)
        sort_name = cls.SPECIAL_CHARS_PATTERN.sub("", sort_name)

        # Normalize multiple spaces to single spaces
        sort_name = cls.MULTIPLE_SPACES_PATTERN.sub(" ", sort_name).strip()

        # Handle article movement (case-insensitive)
        words = sort_name.split()
        if len(words) > 1:
            first_word = words[0].lower()
            if first_word in cls.ARTICLES:
                # Move article to the end: "The Beatles" -> "Beatles, The"
                article = words[0]  # Keep original capitalization
                remaining = " ".join(words[1:])
                sort_name = f"{remaining}, {article}"

        return sort_name

    @classmethod
    def ensure_sort_name(
        cls, artist_name: str, current_sort_name: Optional[str] = None
    ) -> str:
        """
        Ensure an artist has a valid sort name.

        If current_sort_name is provided and not empty, return it.
        Otherwise, generate a new sort name from artist_name.

        Args:
            artist_name: Original artist name
            current_sort_name: Existing sort name (if any)

        Returns:
            Valid sort name
        """
        if current_sort_name and current_sort_name.strip():
            return current_sort_name.strip()

        return cls.generate_sort_name(artist_name)


# Convenience function for easy import
def generate_sort_name(artist_name: str) -> str:
    """Generate sort name from artist name"""
    return SortNameGenerator.generate_sort_name(artist_name)


def ensure_sort_name(artist_name: str, current_sort_name: Optional[str] = None) -> str:
    """Ensure artist has valid sort name"""
    return SortNameGenerator.ensure_sort_name(artist_name, current_sort_name)
