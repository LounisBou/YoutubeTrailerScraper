#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=duplicate-code
"""MovieScanner module for scanning movie directories and detecting missing trailers.

This module provides the MovieScanner class which scans Plex movie directories
to identify movies that are missing trailer files. Trailers are detected as any file
containing 'trailer' in the filename (case-insensitive), regardless of file extension.

Example:
    Basic usage of MovieScanner:

        from pathlib import Path
        from moviescanner import MovieScanner

        scanner = MovieScanner()
        movie_dirs = [Path("/movies/disk1"), Path("/movies/disk2")]
        missing = scanner.find_missing_trailers(movie_dirs)

        for movie_path in missing:
            print(f"Missing trailer: {movie_path}")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from pymate import CacheIt

logger = logging.getLogger(__name__)

# Video file extensions to recognize
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".m4v", ".mov"}


class MovieScanner:
    """Scan movie directories to detect missing trailer files.

    This class scans Plex movie directory structures to identify which movies
    are missing trailer files. Each movie is expected to be in its own directory,
    and trailers are detected as any file containing 'trailer' in the filename
    (case-insensitive), regardless of file extension.

    Example directory structure:
        /movies/
            The Matrix (1999)/
                The Matrix (1999).mp4
                The Matrix (1999)-trailer.mp4  # Trailer present
                The Matrix Trailer.mkv         # Also detected as trailer
                MatrixTrailer.avi              # Also detected as trailer
            Inception (2010)/
                Inception (2010).mp4
                # No trailer - this will be detected

    Note:
        All scan operations are cached with 24-hour TTL using CacheIt decorator.
        Cache is persistent across program executions.
    """

    def __init__(self):
        """Initialize MovieScanner."""
        logger.debug("MovieScanner initialized")

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

    @staticmethod
    def has_trailer(movie_dir: Path) -> bool:
        """Check if a movie directory contains any trailer file.

        A trailer file is any file in the directory that contains 'trailer' in its name
        (case-insensitive), regardless of file extension or exact naming pattern.

        Args:
            movie_dir: Path to the movie directory to check.

        Returns:
            True if at least one trailer file is found, False otherwise.
        """
        try:
            for file_path in movie_dir.iterdir():
                if file_path.is_file() and "trailer" in file_path.name.lower():
                    logger.debug("Trailer found in: %s (%s)", movie_dir, file_path.name)
                    return True
            return False
        except (PermissionError, OSError) as e:
            logger.warning("Error checking for trailer in %s: %s", movie_dir, e)
            return False

    @CacheIt(max_duration=86400, backend="diskcache")  # 24 hour cache
    def find_missing_trailers(self, paths: List[Path]) -> List[Path]:
        """Find movie directories that are missing trailer files.

        Scans the provided paths for movie directories and identifies which ones
        do not contain a trailer file. A trailer file is any file containing
        'trailer' in its name (case-insensitive), regardless of file extension.

        Note:
            Results are cached with a 24-hour TTL using CacheIt decorator.
            The complete results list is cached - directory scanning AND
            trailer detection.

        Args:
            paths: List of directory paths to scan for movies with missing trailers.

        Returns:
            List of Path objects representing movie directories without trailers.

        Raises:
            ValueError: If paths is empty or None.

        Example:
            >>> scanner = MovieScanner()
            >>> missing = scanner.find_missing_trailers([Path("/movies")])
            >>> print(f"Found {len(missing)} movies without trailers")
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

                    # Check if it's a movie directory (has video files)
                    if not self._has_video_files(item):
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
            "Found %d movies without trailers",
            len(missing_trailers),
        )
        return missing_trailers
