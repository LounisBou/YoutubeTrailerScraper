#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MovieScanner module for scanning movie directories and detecting missing trailers.

This module provides the MovieScanner class which scans Plex movie directories
to identify movies that are missing trailer files. Trailers are detected as any file
containing '-trailer' in the filename (case-insensitive), regardless of file extension

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
    and trailers are detected as any file containing '-trailer' in the filename
    (case-insensitive), regardless of file extension.

    Example directory structure:
        /movies/
            The Matrix (1999)/
                The Matrix (1999).mp4
                The Matrix (1999)-trailer.mp4  # Trailer present
                The Matrix-Trailer.mkv         # Also detected as trailer
            Inception (2010)/
                Inception (2010).mp4
                # No trailer - this will be detected

    Attributes:
        trailer_pattern: The glob pattern used for backward compatibility
                        (default: "*-trailer.mp4"). Note: Actual detection now uses
                        flexible pattern matching.
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

    def scan(self, paths: List[Path], max_results: Optional[int] = None) -> List[Path]:
        """Scan multiple directory paths for movie folders.

        Recursively scans the provided paths to find all movie directories.
        A directory is considered a movie directory if it contains video files
        (files with video extensions like .mp4, .mkv, .avi).

        Note:
            Results are cached with a 24-hour TTL to improve performance on repeated scans.
            Uses FileSystemScanner service for actual filesystem operations.

        Args:
            paths: List of directory paths to scan for movies. Can be Path objects or strings.
            max_results: Maximum number of results to return. If None, returns all results.

        Returns:
            List of Path objects representing movie directories found.

        Raises:
            ValueError: If paths is empty or None.
        """
        # Delegate to FileSystemScanner with movie-specific filter
        return self.fs_scanner.scan_directories(
            paths,
            filter_func=self.fs_scanner.has_video_files,
            filter_name="movie_scan",
            max_results=max_results,
        )

    def has_trailer(self, movie_dir: Path) -> bool:
        """Check if a movie directory contains any trailer file.

        A trailer file is any file in the directory that contains '-trailer' in its name,
        regardless of file extension or exact naming pattern.

        Args:
            movie_dir: Path to the movie directory to check.

        Returns:
            True if at least one trailer file is found, False otherwise.

        Example:
            >>> scanner = MovieScanner()
            >>> scanner.has_trailer(Path("/movies/The Matrix (1999)"))
            True
        """
        try:
            for file_path in movie_dir.iterdir():
                if file_path.is_file() and "-trailer" in file_path.name.lower():
                    logger.debug("Trailer found in: %s (%s)", movie_dir, file_path.name)
                    return True
            return False
        except (PermissionError, OSError) as e:
            logger.warning("Error checking for trailer in %s: %s", movie_dir, e)
            return False

    def find_missing_trailers(
        self, paths: List[Path], max_results: Optional[int] = None
    ) -> List[Path]:
        """Find movie directories that are missing trailer files.

        Scans the provided paths for movie directories and identifies which ones
        do not contain a trailer file. A trailer file is any file containing
        '-trailer' in its name (case-insensitive), regardless of file extension.

        Note:
            Results are cached with a 24-hour TTL to improve performance on repeated scans.

        Args:
            paths: List of directory paths to scan for movies with missing trailers.
            max_results: Maximum number of movie directories to scan. If None, scans all.

        Returns:
            List of Path objects representing movie directories without trailers.

        Raises:
            ValueError: If paths is empty or None.

        Example:
            >>> scanner = MovieScanner()
            >>> missing = scanner.find_missing_trailers([Path("/movies")])
            >>> print(f"Found {len(missing)} movies without trailers")
            >>> # Sample mode - scan only first 100 movies
            >>> sample = scanner.find_missing_trailers([Path("/movies")], max_results=100)
        """
        if not paths:
            raise ValueError("Paths list cannot be empty")

        # First, find all movie directories using FileSystemScanner
        movie_dirs = self.scan(paths, max_results=max_results)

        missing_trailers = []

        for movie_dir in movie_dirs:
            # Check if any trailer exists (any file containing '-trailer' in name)
            if not self.has_trailer(movie_dir):
                missing_trailers.append(movie_dir)
                logger.debug("Missing trailer in: %s", movie_dir)

        logger.info(
            "Found %d movies without trailers out of %d total movies",
            len(missing_trailers),
            len(movie_dirs),
        )
        return missing_trailers
