#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MovieScanner module for scanning movie directories and detecting missing trailers.

This module provides the MovieScanner class which scans Plex movie directories
to identify movies that are missing trailer files. Trailers are expected to follow
the naming pattern: <movie-name>-trailer.mp4

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
from typing import List, Optional

from .filesystemscanner import FileSystemScanner

logger = logging.getLogger(__name__)


class MovieScanner:
    """Scan movie directories to detect missing trailer files.

    This class scans Plex movie directory structures to identify which movies
    are missing trailer files. Each movie is expected to be in its own directory,
    and trailers should be named with the pattern: *-trailer.mp4

    Example directory structure:
        /movies/
            The Matrix (1999)/
                The Matrix (1999).mp4
                The Matrix (1999)-trailer.mp4  # Trailer present
            Inception (2010)/
                Inception (2010).mp4
                # No trailer - this will be detected

    Attributes:
        trailer_pattern: The glob pattern used to detect trailer files (default: "*-trailer.mp4")
        fs_scanner: FileSystemScanner instance for filesystem operations (injected dependency)

    Note:
        Uses FileSystemScanner service with 24-hour TTL cache to avoid
        redundant filesystem scans. The cache automatically expires after 24 hours.
    """

    def __init__(
        self,
        trailer_pattern: str = "*-trailer.mp4",
        fs_scanner: Optional[FileSystemScanner] = None,
    ):
        """Initialize MovieScanner with trailer detection pattern.

        Args:
            trailer_pattern: Glob pattern to match trailer files. Defaults to "*-trailer.mp4".
            fs_scanner: FileSystemScanner instance for dependency injection.
                If None, creates a new instance with default settings.
        """
        self.trailer_pattern = trailer_pattern
        self.fs_scanner = fs_scanner or FileSystemScanner()
        logger.debug("MovieScanner initialized with pattern: %s", trailer_pattern)

    def scan(self, paths: List[Path]) -> List[Path]:
        """Scan multiple directory paths for movie folders.

        Recursively scans the provided paths to find all movie directories.
        A directory is considered a movie directory if it contains video files
        (files with video extensions like .mp4, .mkv, .avi).

        Note:
            Results are cached with a 24-hour TTL to improve performance on repeated scans.
            Uses FileSystemScanner service for actual filesystem operations.

        Args:
            paths: List of directory paths to scan for movies. Can be Path objects or strings.

        Returns:
            List of Path objects representing movie directories found.

        Raises:
            ValueError: If paths is empty or None.
        """
        # Delegate to FileSystemScanner with movie-specific filter
        return self.fs_scanner.scan_directories(
            paths, filter_func=self.fs_scanner.has_video_files, filter_name="movie_scan"
        )

    def find_missing_trailers(self, paths: List[Path]) -> List[Path]:
        """Find movie directories that are missing trailer files.

        Scans the provided paths for movie directories and identifies which ones
        do not contain a trailer file matching the trailer_pattern.

        Note:
            Results are cached with a 24-hour TTL to improve performance on repeated scans.

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

        # First, find all movie directories using FileSystemScanner
        movie_dirs = self.scan(paths)

        missing_trailers = []

        for movie_dir in movie_dirs:
            # Check if trailer exists using the pattern
            trailer_files = list(movie_dir.glob(self.trailer_pattern))

            if not trailer_files:
                missing_trailers.append(movie_dir)
                logger.debug("Missing trailer in: %s", movie_dir)
            else:
                logger.debug("Trailer found in: %s (%s)", movie_dir, trailer_files[0].name)

        logger.info(
            "Found %d movies without trailers out of %d total movies",
            len(missing_trailers),
            len(movie_dirs),
        )
        return missing_trailers
