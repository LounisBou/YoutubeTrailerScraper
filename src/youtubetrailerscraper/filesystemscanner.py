#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FileSystemScanner service for scanning directories with caching.

This module provides a generic filesystem scanning service that can be used
by different scanner classes (MovieScanner, TVShowScanner, etc.). It handles
common operations like directory validation, recursive scanning, caching,
and error handling.

Example:
    Basic usage of FileSystemScanner:

        from pathlib import Path
        from filesystemscanner import FileSystemScanner

        scanner = FileSystemScanner()

        # Define a filter function
        def is_movie_dir(path: Path) -> bool:
            video_exts = {".mp4", ".mkv", ".avi"}
            return any(f.suffix.lower() in video_exts for f in path.iterdir() if f.is_file())

        # Scan directories
        paths = [Path("/movies")]
        movie_dirs = scanner.scan_directories(paths, is_movie_dir)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable, List, Optional, Set

from diskcache import Cache

logger = logging.getLogger(__name__)


def _create_cache_key(paths: List[Path], filter_name: str) -> str:
    """Create a hashable cache key from paths and filter function name.

    Args:
        paths: List of Path objects to include in the key.
        filter_name: Name of the filter function being applied.

    Returns:
        String suitable for use as a cache key.
    """
    # Create a stable string key from paths and filter name
    paths_str = "|".join(sorted(str(p) for p in paths))
    return f"{filter_name}::{paths_str}"


class FileSystemScanner:
    """Generic filesystem scanner with persistent disk-based caching.

    This service class provides reusable filesystem scanning functionality
    with built-in persistent caching, error handling, and logging. It's designed
    to be used by specialized scanner classes through dependency injection.

    Attributes:
        video_extensions: Set of video file extensions to recognize.
        cache_ttl: Time-to-live for cache entries in seconds (default: 86400 = 24 hours).
        cache_dir: Directory path for cache storage (default: .cache/filesystemscanner).

    Note:
        All scan operations use a persistent disk cache to avoid redundant filesystem scans.
        The cache automatically expires after the specified TTL period and persists between
        program executions.
    """

    def __init__(
        self,
        video_extensions: Optional[Set[str]] = None,
        cache_ttl: int = 86400,
        cache_dir: Optional[str] = None,
    ):
        """Initialize FileSystemScanner with configuration options.

        Args:
            video_extensions: Set of video file extensions (with dots).
                Defaults to {".mp4", ".mkv", ".avi", ".m4v", ".mov"}.
            cache_ttl: Cache time-to-live in seconds. Defaults to 86400 (24 hours).
            cache_dir: Directory for cache storage. Defaults to .cache/filesystemscanner.
        """
        self.video_extensions = video_extensions or {".mp4", ".mkv", ".avi", ".m4v", ".mov"}
        self.cache_ttl = cache_ttl
        self.cache_dir = cache_dir or ".cache/filesystemscanner"

        # Initialize persistent disk cache
        self._scan_cache = Cache(self.cache_dir)

        logger.debug(
            "FileSystemScanner initialized (TTL: %ds, cache_dir: %s, extensions: %s)",
            cache_ttl,
            self.cache_dir,
            self.video_extensions,
        )

    def validate_path(self, path: Path) -> bool:
        """Validate that a path exists and is a directory.

        Args:
            path: Path to validate.

        Returns:
            True if path exists and is a directory, False otherwise.
        """
        if not path.exists():
            logger.warning("Path does not exist: %s", path)
            return False

        if not path.is_dir():
            logger.warning("Path is not a directory: %s", path)
            return False

        return True

    def has_video_files(self, directory: Path) -> bool:
        """Check if a directory contains any video files.

        Args:
            directory: Directory path to check.

        Returns:
            True if directory contains at least one video file, False otherwise.
        """
        try:
            return any(
                f.suffix.lower() in self.video_extensions
                for f in directory.iterdir()
                if f.is_file()
            )
        except (PermissionError, OSError) as e:
            logger.warning("Error checking video files in %s: %s", directory, e)
            return False

    def has_subdirectories_with_videos(self, directory: Path) -> bool:
        """Check if a directory has subdirectories containing video files.

        This is useful for detecting TV show directories which typically
        have season subdirectories with video files.

        Args:
            directory: Directory path to check.

        Returns:
            True if any subdirectory contains video files, False otherwise.
        """
        try:
            for subdir in directory.iterdir():
                if subdir.is_dir() and self.has_video_files(subdir):
                    return True
            return False
        except (PermissionError, OSError) as e:
            logger.warning("Error checking subdirectories in %s: %s", directory, e)
            return False

    def scan_directories(
        self,
        paths: List[Path],
        filter_func: Callable[[Path], bool],
        filter_name: str = "custom",
        max_results: Optional[int] = None,
    ) -> List[Path]:
        """Scan multiple directory paths and filter results.

        Recursively scans the provided paths to find all subdirectories that
        match the filter function criteria. Results are cached based on the
        paths and filter function name.

        Args:
            paths: List of directory paths to scan.
            filter_func: Function that takes a Path and returns True if it should be included.
            filter_name: Name to identify this filter in cache (for cache key uniqueness).
            max_results: Maximum number of results to return. If None, returns all results.
                Useful for sampling mode to limit scan time.

        Returns:
            List of Path objects that passed the filter function.

        Raises:
            ValueError: If paths is empty or None.

        Example:
            >>> scanner = FileSystemScanner()
            >>> def is_movie(p): return scanner.has_video_files(p)
            >>> results = scanner.scan_directories([Path("/movies")], is_movie, "movie_filter")
            >>> # Limit to 100 results
            >>> sample = scanner.scan_directories(
            ...     [Path("/movies")], is_movie, "movie_filter", max_results=100
            ... )
        """
        if not paths:
            raise ValueError("Paths list cannot be empty")

        # Check cache with TTL
        cache_key = _create_cache_key(paths, filter_name)
        cached_result = self._scan_cache.get(cache_key)

        if cached_result is not None:
            # Check if cached result has expired
            cached_data, cached_time = cached_result
            if time.time() - cached_time < self.cache_ttl:
                logger.debug("Cache hit for scan_directories(%s)", filter_name)
                return cached_data
            logger.debug("Cache expired for scan_directories(%s)", filter_name)
            # Remove expired entry
            self._scan_cache.delete(cache_key)

        matching_dirs = []

        for base_path in paths:
            if not self.validate_path(base_path):
                continue

            logger.info("Scanning path: %s", base_path)

            try:
                # Iterate through all subdirectories
                for item in base_path.iterdir():
                    if not item.is_dir():
                        continue

                    # Apply the filter function
                    if filter_func(item):
                        matching_dirs.append(item)
                        logger.debug("Found matching directory: %s", item)

                        # Check if we've reached max_results limit
                        if max_results and len(matching_dirs) >= max_results:
                            logger.info(
                                "Reached max_results limit (%d), stopping scan", max_results
                            )
                            break

            except PermissionError:
                logger.error("Permission denied accessing: %s", base_path)
            except OSError as e:
                logger.error("Error scanning %s: %s", base_path, e)

            # Break outer loop if we've reached max_results
            if max_results and len(matching_dirs) >= max_results:
                break

        logger.info("Found %d matching directories", len(matching_dirs))

        # Store in cache with timestamp for TTL management
        self._scan_cache.set(cache_key, (matching_dirs, time.time()))
        logger.debug("Cached scan results for %s", filter_name)

        return matching_dirs

    def clear_cache(self) -> None:
        """Clear all cached scan results.

        This can be useful when you know the filesystem has changed and
        want to force a fresh scan.
        """
        self._scan_cache.clear()
        logger.debug("Cache cleared")
