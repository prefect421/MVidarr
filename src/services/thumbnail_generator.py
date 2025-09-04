"""
MVidarr Concurrent Thumbnail Generator - Phase 2 Week 20
High-performance thumbnail generation with thread pool optimization
"""

import asyncio
import logging
import os
import time
from concurrent.futures import as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass
import hashlib
import json

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from src.services.image_thread_pool import get_image_processing_pool, ThreadPoolConfig
from src.utils.logger import get_logger

logger = get_logger("mvidarr.thumbnail_generator")


@dataclass
class ThumbnailConfig:
    """Configuration for thumbnail generation"""
    width: int
    height: int
    quality: int = 85
    format: str = "JPEG"
    suffix: str = ""
    maintain_aspect: bool = True
    enhance_sharpness: bool = False
    enhance_contrast: bool = False
    
    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)
    
    @property
    def filename_suffix(self) -> str:
        return self.suffix or f"_{self.width}x{self.height}"
    
    def __str__(self) -> str:
        return f"{self.width}x{self.height}_{self.format.lower()}_q{self.quality}"


@dataclass
class ThumbnailResult:
    """Result of thumbnail generation"""
    success: bool
    source_path: str
    thumbnail_path: Optional[str] = None
    config: Optional[ThumbnailConfig] = None
    file_size: Optional[int] = None
    processing_time: float = 0.0
    error: Optional[str] = None
    cached: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "source_path": self.source_path,
            "thumbnail_path": self.thumbnail_path,
            "config": f"{self.config}" if self.config else None,
            "file_size": self.file_size,
            "processing_time": self.processing_time,
            "error": self.error,
            "cached": self.cached
        }


class ThumbnailCache:
    """Cache system for generated thumbnails"""
    
    def __init__(self, cache_dir: Path):
        """Initialize thumbnail cache"""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_index_file = cache_dir / "thumbnail_cache.json"
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict:
        """Load cache index from disk"""
        try:
            if self.cache_index_file.exists():
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Could not load thumbnail cache index: {e}")
        return {}
    
    def _save_cache_index(self):
        """Save cache index to disk"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Could not save thumbnail cache index: {e}")
    
    def _get_cache_key(self, source_path: Path, config: ThumbnailConfig) -> str:
        """Generate cache key for source file and config"""
        # Include file modification time and size for cache invalidation
        try:
            stat = source_path.stat()
            key_data = f"{source_path}:{stat.st_mtime}:{stat.st_size}:{config}"
            return hashlib.md5(key_data.encode()).hexdigest()
        except OSError:
            # File doesn't exist, use path + config only
            key_data = f"{source_path}:{config}"
            return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_thumbnail(self, source_path: Path, config: ThumbnailConfig) -> Optional[Path]:
        """Get cached thumbnail if available and valid"""
        cache_key = self._get_cache_key(source_path, config)
        
        if cache_key in self.cache_index:
            cached_path = Path(self.cache_index[cache_key]["path"])
            if cached_path.exists():
                logger.debug(f"📦 Using cached thumbnail: {cached_path}")
                return cached_path
            else:
                # Remove invalid cache entry
                del self.cache_index[cache_key]
                self._save_cache_index()
        
        return None
    
    def cache_thumbnail(self, source_path: Path, thumbnail_path: Path, config: ThumbnailConfig):
        """Add thumbnail to cache"""
        cache_key = self._get_cache_key(source_path, config)
        
        self.cache_index[cache_key] = {
            "path": str(thumbnail_path),
            "source": str(source_path),
            "config": str(config),
            "created": time.time(),
            "size": thumbnail_path.stat().st_size if thumbnail_path.exists() else 0
        }
        
        self._save_cache_index()
    
    def clear_cache(self) -> int:
        """Clear all cached thumbnails"""
        cleared = 0
        for entry in self.cache_index.values():
            cached_path = Path(entry["path"])
            if cached_path.exists():
                try:
                    cached_path.unlink()
                    cleared += 1
                except OSError as e:
                    logger.warning(f"⚠️ Could not delete cached thumbnail {cached_path}: {e}")
        
        self.cache_index.clear()
        self._save_cache_index()
        
        logger.info(f"🗑️ Cleared {cleared} cached thumbnails")
        return cleared


class ConcurrentThumbnailGenerator:
    """High-performance thumbnail generator with concurrent processing"""
    
    # Predefined thumbnail configurations
    THUMBNAIL_PRESETS = {
        "small": ThumbnailConfig(150, 150, suffix="_thumb_small"),
        "medium": ThumbnailConfig(300, 300, suffix="_thumb_medium"),
        "large": ThumbnailConfig(600, 600, suffix="_thumb_large"),
        "preview": ThumbnailConfig(1200, 800, suffix="_preview"),  # 3:2 aspect ratio
        "square": ThumbnailConfig(400, 400, suffix="_square", maintain_aspect=False),
        "banner": ThumbnailConfig(1200, 300, suffix="_banner", maintain_aspect=False)
    }
    
    def __init__(self, output_dir: Path, cache_dir: Optional[Path] = None,
                 thread_pool_config: Optional[ThreadPoolConfig] = None):
        """
        Initialize concurrent thumbnail generator
        
        Args:
            output_dir: Directory for generated thumbnails
            cache_dir: Directory for thumbnail cache (optional)
            thread_pool_config: Thread pool configuration (optional)
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow not available - required for thumbnail generation")
        
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup caching
        if cache_dir:
            self.cache = ThumbnailCache(cache_dir)
        else:
            self.cache = ThumbnailCache(output_dir / ".thumbnail_cache")
        
        # Setup thread pool
        self.thread_pool_config = thread_pool_config
        self._processing_pool = None
        
        logger.info(f"🖼️ Thumbnail generator initialized: output={output_dir}")
    
    def _generate_single_thumbnail(self, source_path: Path, config: ThumbnailConfig) -> ThumbnailResult:
        """Generate a single thumbnail (thread worker function)"""
        start_time = time.time()
        
        try:
            # Check cache first
            cached_path = self.cache.get_cached_thumbnail(source_path, config)
            if cached_path:
                return ThumbnailResult(
                    success=True,
                    source_path=str(source_path),
                    thumbnail_path=str(cached_path),
                    config=config,
                    file_size=cached_path.stat().st_size,
                    processing_time=time.time() - start_time,
                    cached=True
                )
            
            # Generate thumbnail
            with Image.open(source_path) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                original_size = img.size
                
                # Calculate target size
                if config.maintain_aspect:
                    # Maintain aspect ratio
                    img_ratio = img.width / img.height
                    config_ratio = config.width / config.height
                    
                    if img_ratio > config_ratio:
                        # Image is wider - fit to width
                        new_width = config.width
                        new_height = int(config.width / img_ratio)
                    else:
                        # Image is taller - fit to height
                        new_height = config.height
                        new_width = int(config.height * img_ratio)
                    
                    target_size = (new_width, new_height)
                else:
                    # Force exact dimensions
                    target_size = config.size
                
                # Resize image with high-quality resampling
                thumbnail = img.resize(target_size, Image.Resampling.LANCZOS)
                
                # Apply enhancements if requested
                if config.enhance_sharpness:
                    enhancer = ImageEnhance.Sharpness(thumbnail)
                    thumbnail = enhancer.enhance(1.2)  # 20% sharpness increase
                
                if config.enhance_contrast:
                    enhancer = ImageEnhance.Contrast(thumbnail)
                    thumbnail = enhancer.enhance(1.1)  # 10% contrast increase
                
                # Generate output filename
                output_name = f"{source_path.stem}{config.filename_suffix}.{config.format.lower()}"
                output_path = self.output_dir / output_name
                
                # Save thumbnail
                save_kwargs = {"format": config.format, "optimize": True}
                if config.format.upper() == "JPEG":
                    save_kwargs["quality"] = config.quality
                    save_kwargs["progressive"] = True
                elif config.format.upper() == "PNG":
                    save_kwargs["compress_level"] = 6
                
                thumbnail.save(output_path, **save_kwargs)
                
                # Cache the result
                self.cache.cache_thumbnail(source_path, output_path, config)
                
                processing_time = time.time() - start_time
                
                return ThumbnailResult(
                    success=True,
                    source_path=str(source_path),
                    thumbnail_path=str(output_path),
                    config=config,
                    file_size=output_path.stat().st_size,
                    processing_time=processing_time,
                    cached=False
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Thumbnail generation failed for {source_path}: {e}")
            
            return ThumbnailResult(
                success=False,
                source_path=str(source_path),
                config=config,
                processing_time=processing_time,
                error=str(e)
            )
    
    async def generate_thumbnails_async(self, source_paths: List[Path],
                                      configs: List[ThumbnailConfig],
                                      progress_callback: Optional[Callable] = None) -> List[ThumbnailResult]:
        """
        Generate thumbnails asynchronously using thread pool
        
        Args:
            source_paths: List of source image paths
            configs: List of thumbnail configurations
            progress_callback: Optional progress callback function
            
        Returns:
            List of thumbnail results
        """
        pool = get_image_processing_pool()
        
        if not pool.pool.is_running():
            await pool.start()
        
        # Create all jobs (source + config combinations)
        jobs = []
        for source_path in source_paths:
            if not source_path.exists():
                logger.warning(f"⚠️ Source image not found: {source_path}")
                continue
            
            for config in configs:
                jobs.append((self._generate_single_thumbnail, (source_path, config), {}))
        
        total_jobs = len(jobs)
        results = []
        
        logger.info(f"🖼️ Generating {total_jobs} thumbnails using concurrent processing")
        
        # Execute jobs concurrently
        completed = 0
        with pool.pool.batch_execution(jobs) as batch_futures:
            for future in batch_futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"❌ Thumbnail job failed: {e}")
                    results.append(ThumbnailResult(
                        success=False,
                        source_path="unknown",
                        error=str(e)
                    ))
                
                completed += 1
                
                # Update progress
                if progress_callback:
                    progress_callback(completed, total_jobs)
        
        # Generate summary
        successful = sum(1 for r in results if r.success)
        cached = sum(1 for r in results if r.success and r.cached)
        
        logger.info(f"✅ Thumbnail generation completed: {successful}/{total_jobs} successful, {cached} from cache")
        
        return results
    
    async def generate_preset_thumbnails(self, source_paths: List[Path],
                                       presets: List[str] = None,
                                       progress_callback: Optional[Callable] = None) -> List[ThumbnailResult]:
        """
        Generate thumbnails using predefined presets
        
        Args:
            source_paths: List of source image paths
            presets: List of preset names (default: all presets)
            progress_callback: Optional progress callback function
            
        Returns:
            List of thumbnail results
        """
        if presets is None:
            presets = list(self.THUMBNAIL_PRESETS.keys())
        
        configs = []
        for preset in presets:
            if preset in self.THUMBNAIL_PRESETS:
                configs.append(self.THUMBNAIL_PRESETS[preset])
            else:
                logger.warning(f"⚠️ Unknown thumbnail preset: {preset}")
        
        if not configs:
            logger.error("❌ No valid thumbnail presets specified")
            return []
        
        return await self.generate_thumbnails_async(source_paths, configs, progress_callback)
    
    def generate_thumbnails_sync(self, source_paths: List[Path],
                               configs: List[ThumbnailConfig]) -> List[ThumbnailResult]:
        """
        Generate thumbnails synchronously (blocking)
        
        Args:
            source_paths: List of source image paths
            configs: List of thumbnail configurations
            
        Returns:
            List of thumbnail results
        """
        results = []
        
        for source_path in source_paths:
            if not source_path.exists():
                logger.warning(f"⚠️ Source image not found: {source_path}")
                continue
            
            for config in configs:
                result = self._generate_single_thumbnail(source_path, config)
                results.append(result)
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get thumbnail cache statistics"""
        total_entries = len(self.cache.cache_index)
        total_size = 0
        valid_entries = 0
        
        for entry in self.cache.cache_index.values():
            cached_path = Path(entry["path"])
            if cached_path.exists():
                valid_entries += 1
                total_size += entry.get("size", 0)
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "invalid_entries": total_entries - valid_entries,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_directory": str(self.cache.cache_dir)
        }
    
    def clear_cache(self) -> int:
        """Clear thumbnail cache"""
        return self.cache.clear_cache()


# Convenience functions for common operations
async def generate_video_thumbnails(video_paths: List[Path], 
                                  output_dir: Path,
                                  presets: List[str] = None) -> List[ThumbnailResult]:
    """Generate thumbnails for video files (poster frames)"""
    generator = ConcurrentThumbnailGenerator(output_dir)
    
    # For now, just generate standard thumbnails
    # In a real implementation, you'd extract video frames first
    return await generator.generate_preset_thumbnails(video_paths, presets)


async def generate_bulk_thumbnails(image_paths: List[Path],
                                 output_dir: Path,
                                 config: ThumbnailConfig = None) -> List[ThumbnailResult]:
    """Generate bulk thumbnails with single configuration"""
    if config is None:
        config = ConcurrentThumbnailGenerator.THUMBNAIL_PRESETS["medium"]
    
    generator = ConcurrentThumbnailGenerator(output_dir)
    return await generator.generate_thumbnails_async(image_paths, [config])