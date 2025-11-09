#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from typing import List, Optional

from .filesystemscanner import FileSystemScanner

logger = logging.getLogger(__name__)


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
        trailer_subdir: The subdirectory name where trailers are stored
                       (default: "trailers")
        trailer_filename: The expected trailer filename for backward compatibility
                         (default: "trailer.mp4"). Note: Actual detection now uses
                         flexible pattern matching.
        season_pattern: Pattern prefix to identify season directories (default: "season")
        fs_scanner: FileSystemScanner instance for filesystem operations (injected dependency)

    Note:
        Uses FileSystemScanner service with 24-hour TTL cache to avoid
        redundant filesystem scans. The cache automatically expires after 24 hours.
    """

    def __init__(
        self,
        trailer_subdir: str = "trailers",
        trailer_filename: str = "trailer.mp4",
        season_pattern: str = "season",
        fs_scanner: Optional[FileSystemScanner] = None,
    ):
        """Initialize TVShowScanner with trailer detection settings.

        Args:
            trailer_subdir: Subdirectory name where trailers are stored. Defaults to "trailers".
            trailer_filename: Expected trailer filename. Defaults to "trailer.mp4".
            season_pattern: Pattern prefix to match season directories (case-insensitive).
                Defaults to "season". Examples: "season", "s", "saison".
            fs_scanner: FileSystemScanner instance for dependency injection.
                If None, creates a new instance with default settings.
        """
        self.trailer_subdir = trailer_subdir
        self.trailer_filename = trailer_filename
        self.season_pattern = season_pattern.lower()
        self.fs_scanner = fs_scanner or FileSystemScanner()
        logger.debug(
            "TVShowScanner initialized with trailer path: %s/%s, season pattern: %s",
            trailer_subdir,
            trailer_filename,
            season_pattern,
        )

    def _is_tvshow_directory(self, directory: Path) -> bool:
        """Check if a directory is a TV show directory.

        A directory is considered a TV show directory if it contains:
        - Subdirectories matching season_pattern that contain video files, OR
        - Any subdirectories with video files

        Args:
            directory: Directory path to check.

        Returns:
            True if directory appears to be a TV show directory, False otherwise.
        """
        try:
            # Check for season subdirectories with videos using the configured pattern
            for subdir in directory.iterdir():
                if subdir.is_dir() and subdir.name.lower().startswith(self.season_pattern):
                    if self.fs_scanner.has_video_files(subdir):
                        return True

            # Alternative: check for any subdirectories with video files
            return self.fs_scanner.has_subdirectories_with_videos(directory)

        except (PermissionError, OSError) as e:
            logger.warning("Error checking if %s is a TV show directory: %s", directory, e)
            return False

    def scan(self, paths: List[Path], max_results: Optional[int] = None) -> List[Path]:
        """Scan multiple directory paths for TV show folders.

        Recursively scans the provided paths to find all TV show directories.
        A directory is considered a TV show directory if it contains season subdirectories
        (directories starting with "Season") or subdirectories containing video files.

        Note:
            Results are cached with a 24-hour TTL to improve performance on repeated scans.
            Uses FileSystemScanner service for actual filesystem operations.

        Args:
            paths: List of directory paths to scan for TV shows. Can be Path objects or strings.
            max_results: Maximum number of results to return. If None, returns all results.

        Returns:
            List of Path objects representing TV show directories found.

        Raises:
            ValueError: If paths is empty or None.
        """
        # Delegate to FileSystemScanner with TV show-specific filter
        return self.fs_scanner.scan_directories(
            paths,
            filter_func=self._is_tvshow_directory,
            filter_name="tvshow_scan",
            max_results=max_results,
        )

    def has_trailer(self, tvshow_dir: Path) -> bool:
        """Check if a TV show directory contains any trailer file.

        A trailer file is any file in the trailers subdirectory that contains
        'trailer' in its name (case-insensitive), regardless of file extension.

        Args:
            tvshow_dir: Path to the TV show directory to check.

        Returns:
            True if at least one trailer file is found, False otherwise.

        Example:
            >>> scanner = TVShowScanner()
            >>> scanner.has_trailer(Path("/tvshows/Breaking Bad"))
            True
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

    def find_missing_trailers(
        self, paths: List[Path], max_results: Optional[int] = None
    ) -> List[Path]:
        """Find TV show directories that are missing trailer files.

        Scans the provided paths for TV show directories and identifies which ones
        do not contain a trailer file. A trailer file is any file in the trailers
        subdirectory containing 'trailer' in its name (case-insensitive), regardless
        of file extension.

        Note:
            Results are cached with a 24-hour TTL to improve performance on repeated scans.

        Args:
            paths: List of directory paths to scan for TV shows with missing trailers.
            max_results: Maximum number of TV show directories to scan. If None, scans all.

        Returns:
            List of Path objects representing TV show directories without trailers.

        Raises:
            ValueError: If paths is empty or None.

        Example:
            >>> scanner = TVShowScanner()
            >>> missing = scanner.find_missing_trailers([Path("/tvshows")])
            >>> print(f"Found {len(missing)} TV shows without trailers")
            >>> # Sample mode - scan only first 100 TV shows
            >>> sample = scanner.find_missing_trailers([Path("/tvshows")], max_results=100)
        """
        if not paths:
            raise ValueError("Paths list cannot be empty")

        # First, find all TV show directories using FileSystemScanner
        tvshow_dirs = self.scan(paths, max_results=max_results)

        missing_trailers = []

        for tvshow_dir in tvshow_dirs:
            # Check if any trailer exists (any file containing '-trailer' in trailers subdir)
            if not self.has_trailer(tvshow_dir):
                missing_trailers.append(tvshow_dir)
                logger.debug("Missing trailer in: %s", tvshow_dir)

        logger.info(
            "Found %d TV shows without trailers out of %d total TV shows",
            len(missing_trailers),
            len(tvshow_dirs),
        )
        return missing_trailers
