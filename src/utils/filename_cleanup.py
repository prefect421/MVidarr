"""
Filename cleanup utilities for music videos
"""

import re
import unicodedata
from pathlib import Path
from typing import Tuple, Optional

class FilenameCleanup:
    """Utility class for cleaning up music video filenames"""
    
    # Common patterns to remove from filenames
    CLEANUP_PATTERNS = [
        # Video quality and format indicators
        r'\b(?:4K|1080p|720p|480p|HD|SD|UHD)\b',
        r'\b(?:mp4|avi|mkv|mov|wmv|flv|webm)\b',
        r'\[(?:4K|1080p|720p|480p|HD|SD|UHD)\]',
        
        # YouTube and platform specific
        r'\[.*?YouTube.*?\]',
        r'\(.*?YouTube.*?\)',
        r'\[.*?Official.*?Video.*?\]',
        r'\(.*?Official.*?Video.*?\)',
        r'\[.*?Music.*?Video.*?\]',
        r'\(.*?Music.*?Video.*?\)',
        
        # Download metadata
        r'\[.*?\d{4}-\d{2}-\d{2}.*?\]',
        r'\[.*?\d{8}.*?\]',
        r'\[.*?Downloaded.*?\]',
        r'\(.*?Downloaded.*?\)',
        
        # Common prefixes/suffixes
        r'^\s*-\s*',
        r'\s*-\s*$',
        r'^\s*\|\s*',
        r'\s*\|\s*$',
        
        # Multiple spaces and special characters
        r'\s+',  # Replace with single space
        r'[^\w\s\-\(\)\[\]&]',  # Remove special chars except basic ones
    ]
    
    # Artist name extraction patterns (these come before the song title)
    ARTIST_PATTERNS = [
        r'^(.+?)\s*[-–—]\s*(.+?)$',  # Artist - Song
        r'^(.+?)\s*\|\s*(.+?)$',    # Artist | Song  
        r'^(.+?)\s*:\s*(.+?)$',     # Artist : Song
        r'^(.+?)\s*–\s*(.+?)$',     # Artist – Song (em dash)
        # Improved fallback pattern that handles "And", "&", and common conjunctions
        r'^(.+?(?:\s+(?:[Aa]nd|&|[Ff]eat\.?|[Ww]ith)\s+.+?)*)\s+([A-Z][A-Za-z].{3,})$',  # Artist Song (conjunction-aware)
        r'^([A-Za-z][A-Za-z\s]{1,30}?)\s+([A-Za-z].{3,})$',  # Artist Song (simple fallback)
    ]
    
    @classmethod
    def clean_filename(cls, filename: str) -> str:
        """
        Clean up a filename by removing common junk patterns
        
        Args:
            filename: Raw filename to clean
            
        Returns:
            Cleaned filename
        """
        # Remove file extension for processing
        path_obj = Path(filename)
        name = path_obj.stem
        extension = path_obj.suffix
        
        # Apply cleanup patterns
        for pattern in cls.CLEANUP_PATTERNS:
            if pattern == r'\s+':
                # Replace multiple spaces with single space
                name = re.sub(pattern, ' ', name, flags=re.IGNORECASE)
            elif pattern == r'[^\w\s\-\(\)\[\]&]':
                # Remove unwanted special characters but keep some
                name = re.sub(pattern, '', name)
            else:
                # Remove pattern entirely
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Normalize unicode characters
        name = unicodedata.normalize('NFKD', name)
        
        # Clean up whitespace
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        
        # Remove empty brackets/parentheses
        name = re.sub(r'\[\s*\]', '', name)
        name = re.sub(r'\(\s*\)', '', name)
        
        # Final cleanup
        name = name.strip(' -_|')
        
        return f"{name}{extension}" if name else f"unknown{extension}"
    
    @classmethod
    def extract_artist_and_title(cls, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract artist and song title from filename
        
        Args:
            filename: Cleaned filename
            
        Returns:
            Tuple of (artist, title) or (None, None) if can't parse
        """
        # Remove file extension
        name = Path(filename).stem
        
        # Try different patterns to extract artist and title
        for i, pattern in enumerate(cls.ARTIST_PATTERNS):
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                artist = match.group(1).strip()
                title = match.group(2).strip()
                
                # Clean up extracted parts
                artist = cls._clean_text(artist)
                title = cls._clean_text(title)
                
                # For the fallback patterns, be more selective
                if i >= len(cls.ARTIST_PATTERNS) - 2:  # Last two patterns (fallbacks)
                    # Only use if it looks reasonable (artist should be 1-5 words typically)
                    artist_words = artist.split()
                    
                    # Allow more words if the artist contains conjunctions like "And"
                    max_words = 6 if any(word in artist.lower() for word in ['and', '&', 'feat', 'with']) else 4
                    if len(artist_words) > max_words:  # Too many words, probably not just an artist
                        continue
                    
                    # Title should have some content
                    if len(title.split()) < 2:
                        continue
                
                if artist and title and len(artist) > 1 and len(title) > 1:
                    return artist, title
        
        # If no pattern matches, return None
        return None, None
    
    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Clean up artist/title text"""
        if not text:
            return ""
        
        # Remove common prefixes/suffixes
        text = re.sub(r'^\s*[-–—\|]\s*', '', text)
        text = re.sub(r'\s*[-–—\|]\s*$', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    @classmethod
    def sanitize_folder_name(cls, name: str) -> str:
        """
        Sanitize a name for use as a folder name
        
        Args:
            name: Raw name to sanitize
            
        Returns:
            Safe folder name
        """
        if not name:
            return "Unknown"
        
        # Replace problematic characters with safe alternatives
        replacements = {
            '/': '_',
            '\\': '_',
            ':': ' -',
            '*': '',
            '?': '',
            '"': "'",
            '<': '(',
            '>': ')',
            '|': '-',
        }
        
        sanitized = name
        for char, replacement in replacements.items():
            sanitized = sanitized.replace(char, replacement)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure it's not empty
        if not sanitized:
            return "Unknown"
        
        # Limit length to reasonable size
        if len(sanitized) > 100:
            sanitized = sanitized[:100].strip()
        
        return sanitized
    
    @classmethod
    def generate_clean_filename(cls, artist: str, title: str, extension: str) -> str:
        """
        Generate a clean filename from artist and title
        
        Args:
            artist: Artist name
            title: Song title  
            extension: File extension (with dot)
            
        Returns:
            Clean filename in format "Artist - Title.ext"
        """
        # Clean the components
        clean_artist = cls.sanitize_folder_name(artist)
        clean_title = cls.sanitize_folder_name(title)
        
        # Ensure extension starts with dot
        if not extension.startswith('.'):
            extension = f".{extension}"
        
        return f"{clean_artist} - {clean_title}{extension}"

def test_filename_cleanup():
    """Test the filename cleanup functionality"""
    test_cases = [
        "Taylor Swift - Anti-Hero [Official Music Video] [4K] (2022).mp4",
        "The Weeknd | Blinding Lights (Official Video) [1080p].mkv", 
        "Billie Eilish – bad guy [YouTube Music Video] HD.mp4",
        "[Downloaded 2023-12-01] Ed Sheeran - Shape of You (Official).avi",
        "Dua Lipa: Levitating | Official Music Video [4K UHD].webm",
        "badly_formatted__file---name.mp4"
    ]
    
    for original in test_cases:
        cleaned = FilenameCleanup.clean_filename(original)
        artist, title = FilenameCleanup.extract_artist_and_title(cleaned)
        
        print(f"Original: {original}")
        print(f"Cleaned:  {cleaned}")
        print(f"Artist:   {artist}")
        print(f"Title:    {title}")
        if artist and title:
            new_name = FilenameCleanup.generate_clean_filename(
                artist, title, Path(original).suffix
            )
            print(f"Final:    {new_name}")
        print("-" * 50)

if __name__ == "__main__":
    test_filename_cleanup()