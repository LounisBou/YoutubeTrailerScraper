#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=duplicate-code
"""TVShowScanner module for scanning TV show directories and detecting missing trailers.

This module provides the TVShowScanner class which scans Plex TV show directories
to identify TV shows that are missing trailer files. Trailers are expected to be
located in a "trailers" subdirectory and can be any file containing 'trailer' in
the filename (case-insensitive), regardless of file extension.

Example:
    Basic usage of TVShowScanner:

        from pathlib import Path
        from tvshowscanner import TVShowScanner

        scanner = TVShowScanner()
        tvshow_dirs = [Path("/tvshows/disk1"), Path("/tvshows/disk2")]
        missing = scanner.find_missing_trailers(tvshow_dirs)

        for tvshow_path in missing:
            print(f"Missing trailer: {tvshow_path}")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from pymate import CacheIt

logger = logging.getLogger(__name__)

# Video file extensions to recognize
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".m4v", ".mov"}


class TVShowScanner:
    """Scan TV show directories to detect missing trailer files.

    This class scans Plex TV show directory structures to identify which TV shows
    are missing trailer files. Each TV show is expected to be in its own directory,
    and trailers should be located in a "trailers" subdirectory. Any file containing
    'trailer' in its name (case-insensitive) is considered a trailer, regardless
    of file extension.

    Example directory structure:
        /tvshows/
            Breaking Bad/
                Season 01/
                    episode1.mp4
                trailers/
                    trailer.mp4              # Trailer present
                    breaking bad trailer.mkv # Also detected as trailer
                    BreakingBadTrailer.avi   # Also detected as trailer
            The Wire/
                Season 01/
                    episode1.mp4
                # No trailers directory - this will be detected

    Attributes:
        trailer_subdir: The subdirectory name where trailers are stored (default: "trailers")
        season_pattern: Pattern prefix to identify season directories (default: "season")

    Note:
        All scan operations are cached with 24-hour TTL using CacheIt decorator.
        Cache is persistent across program executions.
    """

    def __init__(self, trailer_subdir: str = "trailers", season_pattern: str = "season"):
        """Initialize TVShowScanner with configuration options.

        Args:
            trailer_subdir: Subdirectory name for trailers. Defaults to "trailers".
            season_pattern: Pattern prefix for season directories (case-insensitive).
                          Defaults to "season".
        """
        self.trailer_subdir = trailer_subdir
        self.season_pattern = season_pattern.lower()
        logger.debug(
            "TVShowScanner initialized (trailer_subdir: %s, season_pattern: %s)",
            trailer_subdir,
            season_pattern,
        )

    @staticmethod
    def _has_video_files(directory: Path) -> bool:
        """Check if a directory contains any video files.

        Args:
            directory: Directory path to check.

        Returns:
            True if directory contains at least one video file, False otherwise.
        """
        try:
            return any(
                f.suffix.lower() in VIDEO_EXTENSIONS for f in directory.iterdir() if f.is_file()
            )
        except (PermissionError, OSError) as e:
            logger.warning("Error checking video files in %s: %s", directory, e)
            return False

    def _has_subdirectories_with_videos(self, directory: Path) -> bool:
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
                if subdir.is_dir() and self._has_video_files(subdir):
                    return True
            return False
        except (PermissionError, OSError) as e:
            logger.warning("Error checking subdirectories in %s: %s", directory, e)
            return False

    def _is_tvshow_directory(self, directory: Path) -> bool:
        """Determine if a directory is a TV show directory.

        A directory is considered a TV show directory if it contains
        subdirectories matching the season_pattern with video files.

        Args:
            directory: Directory path to check.

        Returns:
            True if directory appears to be a TV show directory, False otherwise.
        """
        try:
            for subdir in directory.iterdir():
                if subdir.is_dir() and subdir.name.lower().startswith(self.season_pattern):
                    if self._has_video_files(subdir):
                        return True
            # If we found season directories but no videos, still return False
            return False
        except (PermissionError, OSError) as e:
            logger.warning("Error checking if TV show directory %s: %s", directory, e)
            return False

    def has_trailer(self, tvshow_dir: Path) -> bool:
        """Check if a TV show directory contains any trailer file.

        A trailer file is any file in the trailers subdirectory that contains
        'trailer' in its name (case-insensitive), regardless of file extension.

        Args:
            tvshow_dir: Path to the TV show directory to check.

        Returns:
            True if at least one trailer file is found, False otherwise.
        """
        trailer_dir = tvshow_dir / self.trailer_subdir

        # Check if trailers directory exists
        if not trailer_dir.exists() or not trailer_dir.is_dir():
            return False

        try:
            # Look for any file containing 'trailer' in the trailers directory
            for file_path in trailer_dir.iterdir():
                if file_path.is_file() and "trailer" in file_path.name.lower():
                    logger.debug("Trailer found in: %s (%s)", tvshow_dir, file_path.name)
                    return True
            return False
        except (PermissionError, OSError) as e:
            logger.warning("Error checking for trailer in %s: %s", tvshow_dir, e)
            return False

    @CacheIt(max_duration=86400, backend="diskcache")  # 24 hour cache
    def find_missing_trailers(self, paths: List[Path]) -> List[Path]:
        """Find TV show directories that are missing trailer files.

        Scans the provided paths for TV show directories and identifies which ones
        do not contain a trailer file. A trailer file is any file in the trailers
        subdirectory containing 'trailer' in its name (case-insensitive), regardless
        of file extension.

        Note:
            Results are cached with a 24-hour TTL using CacheIt decorator.
            The complete results list is cached - directory scanning AND
            trailer detection.

        Args:
            paths: List of directory paths to scan for TV shows with missing trailers.

        Returns:
            List of Path objects representing TV show directories without trailers.

        Raises:
            ValueError: If paths is empty or None.

        Example:
            >>> scanner = TVShowScanner()
            >>> missing = scanner.find_missing_trailers([Path("/tvshows")])
            >>> print(f"Found {len(missing)} TV shows without trailers")
        """
        if not paths:
            raise ValueError("Paths list cannot be empty")

        missing_trailers = []

        for base_path in paths:
            if not base_path.exists():
                logger.warning("Path does not exist: %s", base_path)
                continue

            if not base_path.is_dir():
                logger.warning("Path is not a directory: %s", base_path)
                continue

            logger.info("Scanning path: %s", base_path)

            try:
                # Iterate through all subdirectories
                for item in base_path.iterdir():
                    if not item.is_dir():
                        continue

                    # Check if it's a TV show directory
                    if not self._is_tvshow_directory(item):
                        continue

                    # Check if it has a trailer
                    if not self.has_trailer(item):
                        missing_trailers.append(item)
                        logger.debug("Missing trailer in: %s", item)

            except PermissionError:
                logger.error("Permission denied accessing: %s", base_path)
            except OSError as e:
                logger.error("Error scanning %s: %s", base_path, e)

        logger.info(
            "Found %d TV shows without trailers",
            len(missing_trailers),
        )
        return missing_trailers
