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
from pathlib import Path
from typing import Callable, List, Optional, Set

from cachetools import TTLCache
from cachetools.keys import hashkey

logger = logging.getLogger(__name__)


def _create_cache_key(paths: List[Path], filter_name: str) -> tuple:
    """Create a hashable cache key from paths and filter function name.

    Args:
        paths: List of Path objects to include in the key.
        filter_name: Name of the filter function being applied.

    Returns:
        Tuple suitable for use as a cache key.
    """
    return hashkey(tuple(str(p) for p in paths), filter_name)


class FileSystemScanner:
    """Generic filesystem scanner with caching and error handling.

    This service class provides reusable filesystem scanning functionality
    with built-in caching, error handling, and logging. It's designed to be
    used by specialized scanner classes through dependency injection.

    Attributes:
        video_extensions: Set of video file extensions to recognize.
        cache_ttl: Time-to-live for cache entries in seconds (default: 86400 = 24 hours).
        cache_maxsize: Maximum number of cache entries (default: 100).

    Note:
        All scan operations use a TTL cache to avoid redundant filesystem scans.
        The cache automatically expires after the specified TTL period.
    """

    def __init__(
        self,
        video_extensions: Optional[Set[str]] = None,
        cache_ttl: int = 86400,
        cache_maxsize: int = 100,
    ):
        """Initialize FileSystemScanner with configuration options.

        Args:
            video_extensions: Set of video file extensions (with dots).
                Defaults to {".mp4", ".mkv", ".avi", ".m4v", ".mov"}.
            cache_ttl: Cache time-to-live in seconds. Defaults to 86400 (24 hours).
            cache_maxsize: Maximum cache entries. Defaults to 100.
        """
        self.video_extensions = video_extensions or {".mp4", ".mkv", ".avi", ".m4v", ".mov"}
        self.cache_ttl = cache_ttl
        self.cache_maxsize = cache_maxsize
        self._scan_cache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
        logger.debug(
            "FileSystemScanner initialized (TTL: %ds, maxsize: %d, extensions: %s)",
            cache_ttl,
            cache_maxsize,
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
    ) -> List[Path]:
        """Scan multiple directory paths and filter results.

        Recursively scans the provided paths to find all subdirectories that
        match the filter function criteria. Results are cached based on the
        paths and filter function name.

        Args:
            paths: List of directory paths to scan.
            filter_func: Function that takes a Path and returns True if it should be included.
            filter_name: Name to identify this filter in cache (for cache key uniqueness).

        Returns:
            List of Path objects that passed the filter function.

        Raises:
            ValueError: If paths is empty or None.

        Example:
            >>> scanner = FileSystemScanner()
            >>> def is_movie(p): return scanner.has_video_files(p)
            >>> results = scanner.scan_directories([Path("/movies")], is_movie, "movie_filter")
        """
        if not paths:
            raise ValueError("Paths list cannot be empty")

        # Check cache
        cache_key = _create_cache_key(paths, filter_name)
        if cache_key in self._scan_cache:
            logger.debug("Cache hit for scan_directories(%s)", filter_name)
            return self._scan_cache[cache_key]

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

            except PermissionError:
                logger.error("Permission denied accessing: %s", base_path)
            except OSError as e:
                logger.error("Error scanning %s: %s", base_path, e)

        logger.info("Found %d matching directories", len(matching_dirs))

        # Store in cache
        self._scan_cache[cache_key] = matching_dirs
        return matching_dirs

    def clear_cache(self) -> None:
        """Clear all cached scan results.

        This can be useful when you know the filesystem has changed and
        want to force a fresh scan.
        """
        self._scan_cache.clear()
        logger.debug("Cache cleared")
