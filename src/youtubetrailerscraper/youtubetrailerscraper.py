#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
youtubetrailerscraper.py

Description:
    Scan tvshows and movies folders, download trailer on youtube

Usage:
    from youtubetrailerscraper import YoutubeTrailerScraper

    # Usage example:
    scraper = YoutubeTrailerScraper()
    scraper.run()

Requirements:
    - python-dotenv
    - requests
    - yt-dlp

References:

"""

from __future__ import annotations

import ast
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from youtubetrailerscraper.moviescanner import MovieScanner
from youtubetrailerscraper.tvshowscanner import TVShowScanner


class YoutubeTrailerScraper:  # pylint: disable=too-many-instance-attributes
    """Scan tvshows and movies folders, download trailer on youtube"""

    def __init__(
        self,
        env_file: Optional[str] = None,
        use_smb: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize YoutubeTrailerScraper

        Parameters:
            env_file (str, optional): Path to .env file. Defaults to .env in current directory.
            use_smb (bool): Whether to use SMB mount point as prefix for paths. Can be
                overridden by USE_SMB_MOUNT environment variable. Defaults to False.
            logger (logging.Logger, optional): Logger instance for logging. If None, uses a
                NullHandler (no logging output). Pass a configured logger to enable logging.
        """
        # Configuration attributes
        self.tmdb_api_key: str = ""
        self.tmdb_read_access_token: str = ""
        self.tmdb_api_base_url: str = ""
        self.movies_paths: list[Path] = []
        self.tvshows_paths: list[Path] = []
        self.smb_mount_point: str = ""
        self.use_smb_mount: bool = use_smb
        self.youtube_search_url: str = ""
        self.default_search_query_format: str = ""
        self.scan_sample_size: int | None = None

        # Set up logger
        self.logger = logger or logging.getLogger(__name__)
        if not logger:
            # Add NullHandler to prevent "No handler found" warnings
            self.logger.addHandler(logging.NullHandler())

        # Load environment variables
        self._load_environment_variables(env_file)

    def _load_environment_variables(self, env_file: Optional[str] = None) -> None:
        """
        Load environment variables from .env file

        Parameters:
            env_file (str, optional): Path to .env file

        Raises:
            FileNotFoundError: If .env file is not found
            ValueError: If required environment variables are missing
        """
        # Load .env file
        env_path = env_file or ".env"
        self.logger.debug("Loading environment from: %s", env_path)

        if not Path(env_path).exists():
            raise FileNotFoundError(
                f"Environment file not found: {env_path}. "
                "Please create a .env file based on .env.example"
            )

        # Load the environment file
        load_dotenv(env_path, override=True)

        # Load TMDB API configuration
        self.logger.debug("Loading TMDB API configuration...")
        self.tmdb_api_key = self._get_env_var("TMDB_API_KEY", required=True)
        self.tmdb_read_access_token = self._get_env_var("TMDB_READ_ACCESS_TOKEN", required=True)
        self.tmdb_api_base_url = self._get_env_var(
            "TMDB_API_BASE_URL", default="https://api.themoviedb.org/3"
        )

        # Load SMB mount configuration
        self.logger.debug("Loading SMB mount configuration...")
        self.smb_mount_point = self._get_env_var("SMB_MOUNT_POINT", default="")
        use_smb_env = self._get_env_var("USE_SMB_MOUNT", default="false").lower() == "true"
        # Environment variable overrides constructor parameter
        if use_smb_env:
            self.use_smb_mount = True

        # Load media paths
        self.logger.debug("Loading media paths...")
        movies_paths_raw = self._parse_path_list(self._get_env_var("MOVIES_PATHS", required=True))
        tvshows_paths_raw = self._parse_path_list(
            self._get_env_var("TVSHOWS_PATHS", required=True)
        )

        # Apply SMB mount point prefix if enabled
        if self.use_smb_mount and self.smb_mount_point:
            self.logger.debug("Applying SMB mount prefix: %s", self.smb_mount_point)
            self.movies_paths = self._apply_smb_prefix(movies_paths_raw)
            self.tvshows_paths = self._apply_smb_prefix(tvshows_paths_raw)
        else:
            self.movies_paths = movies_paths_raw
            self.tvshows_paths = tvshows_paths_raw

        self.logger.debug("Loaded %d movie paths", len(self.movies_paths))
        self.logger.debug("Loaded %d TV show paths", len(self.tvshows_paths))

        # Load optional configurations
        self.youtube_search_url = self._get_env_var(
            "YOUTUBE_SEARCH_URL",
            default="https://www.youtube.com/results?search_query={query}",
        )
        self.default_search_query_format = self._get_env_var(
            "DEFAULT_SEARCH_QUERY_FORMAT", default="{title} {year} bande annonce"
        )

        # Load scan sample size
        scan_sample_str = self._get_env_var("SCAN_SAMPLE_SIZE", default="")
        if scan_sample_str:
            try:
                self.scan_sample_size = int(scan_sample_str)
                self.logger.debug("Scan sample size set to: %d", self.scan_sample_size)
            except ValueError:
                self.logger.warning(
                    "Invalid SCAN_SAMPLE_SIZE value '%s', ignoring", scan_sample_str
                )
                self.scan_sample_size = None
        else:
            self.scan_sample_size = None

    def _get_env_var(self, key: str, required: bool = False, default: str = "") -> str:
        """
        Get environment variable with error handling

        Parameters:
            key (str): Environment variable key
            required (bool): Whether the variable is required
            default (str): Default value if not found

        Returns:
            str: Environment variable value

        Raises:
            ValueError: If required variable is missing
        """
        value = os.getenv(key, default)
        if required and not value:
            raise ValueError(
                f"Required environment variable '{key}' is not set. "
                "Please check your .env file."
            )
        return value

    def _parse_path_list(self, paths_str: str) -> list[Path]:
        """
        Parse a string representation of a list into Path objects

        Parameters:
            paths_str (str): String representation of paths list (Python list format)

        Returns:
            list[Path]: List of Path objects

        Raises:
            ValueError: If paths_str is not a valid Python list
        """
        try:
            # Use ast.literal_eval to safely parse the string as a Python list
            paths_list = ast.literal_eval(paths_str)
            if not isinstance(paths_list, list):
                raise ValueError("PATHS must be a Python list")
            return [Path(p) for p in paths_list]
        except (ValueError, SyntaxError) as e:
            raise ValueError(
                f"Invalid path list format: {paths_str}. "
                f"Expected Python list format, e.g., ['/path1/', '/path2/']. Error: {e}"
            ) from e

    def _apply_smb_prefix(self, paths: list[Path]) -> list[Path]:
        """Apply SMB mount point as prefix to all paths.

        The SMB mount point should be a local filesystem mount path (e.g., /Volumes/MediaServer).
        This method prepends the mount point to each path.

        Args:
            paths: List of Path objects to prefix.

        Returns:
            List of Path objects with SMB mount point prepended.

        Example:
            >>> paths = [Path("/Volumes/Disk1/medias/movies")]
            >>> smb_mount = "/Volumes/MediaServer"
            >>> prefixed = self._apply_smb_prefix(paths)
            >>> # Result: [Path("/Volumes/MediaServer/Volumes/Disk1/medias/movies")]
        """
        prefixed_paths = []
        smb_prefix = Path(self.smb_mount_point)

        for path in paths:
            # Remove leading slash to avoid double slashes when joining
            path_str = str(path).lstrip("/")
            prefixed_path = smb_prefix / path_str
            prefixed_paths.append(prefixed_path)

        return prefixed_paths

    def scan_for_movies_without_trailers(self, use_sample: bool = False) -> list[Path]:
        """Scan for movies without trailers across all configured movie directories.

        Uses the MovieScanner class to scan all directories specified in the
        MOVIES_PATHS environment variable. Returns a list of movie directories
        that are missing trailer files.

        Args:
            use_sample: If True and SCAN_SAMPLE_SIZE is set, limits scan to sample size.

        Returns:
            List of Path objects representing movie directories without trailers.
            Returns empty list if no movies are missing trailers or if movies_paths is empty.

        Example:
            >>> scraper = YoutubeTrailerScraper()
            >>> missing = scraper.scan_for_movies_without_trailers()
            >>> print(f"Found {len(missing)} movies without trailers")
            >>> # Sample mode
            >>> sample = scraper.scan_for_movies_without_trailers(use_sample=True)
        """
        if not self.movies_paths:
            self.logger.debug("No movie paths configured, skipping movie scan")
            return []

        if use_sample and self.scan_sample_size:
            self.logger.warning(
                "Sample mode requested but not supported with CacheIt. Scanning all movies."
            )

        self.logger.debug("Scanning %d movie directories...", len(self.movies_paths))
        for path in self.movies_paths:
            self.logger.debug("  - %s", path)

        scanner = MovieScanner()
        missing_trailers = scanner.find_missing_trailers(self.movies_paths)

        self.logger.info("Found %d movies without trailers", len(missing_trailers))
        for movie_path in missing_trailers:
            self.logger.debug("  - %s", movie_path)

        return missing_trailers

    def scan_for_tvshows_without_trailers(self, use_sample: bool = False) -> list[Path]:
        """Scan for TV shows without trailers across all configured TV show directories.

        Uses the TVShowScanner class to scan all directories specified in the
        TVSHOWS_PATHS environment variable. Returns a list of TV show directories
        that are missing trailer files.

        Args:
            use_sample: If True and SCAN_SAMPLE_SIZE is set, limits scan to sample size.

        Returns:
            List of Path objects representing TV show directories without trailers.
            Returns empty list if no TV shows are missing trailers or if tvshows_paths is empty.

        Example:
            >>> scraper = YoutubeTrailerScraper()
            >>> missing = scraper.scan_for_tvshows_without_trailers()
            >>> print(f"Found {len(missing)} TV shows without trailers")
            >>> # Sample mode
            >>> sample = scraper.scan_for_tvshows_without_trailers(use_sample=True)
        """
        if not self.tvshows_paths:
            self.logger.debug("No TV show paths configured, skipping TV show scan")
            return []

        if use_sample and self.scan_sample_size:
            self.logger.warning(
                "Sample mode requested but not supported with CacheIt. Scanning all TV shows."
            )

        self.logger.debug("Scanning %d TV show directories...", len(self.tvshows_paths))
        for path in self.tvshows_paths:
            self.logger.debug("  - %s", path)

        scanner = TVShowScanner()
        missing_trailers = scanner.find_missing_trailers(self.tvshows_paths)

        self.logger.info("Found %d TV shows without trailers", len(missing_trailers))
        for tvshow_path in missing_trailers:
            self.logger.debug("  - %s", tvshow_path)

        return missing_trailers

    def search_for_movie_trailer(
        self,
        title: str,  # pylint: disable=unused-argument
        year: int | None,  # pylint: disable=unused-argument
    ) -> list[str]:
        """
        Search for movie trailer on youtube

        Parameters:
            title (str): Movie title
            year (int|None): Movie release year
        Returns:
            list[str]: YouTube video URLs of the trailer
        """
        # pylint: disable=fixme
        # TODO: Implement in Step 4/5
        # Create search query
        return []

    def clear_cache(self) -> None:
        """Clear the cache for all scanners.

        This removes all cached scan results, forcing a fresh scan
        on the next execution. Useful when media libraries have been
        updated and you want to bypass the cache.

        The cache is stored in __cacheit__/ directory.
        """
        self.logger.info("Clearing cache...")
        # Clear cache for both scanners
        MovieScanner().find_missing_trailers.clear_cache()
        TVShowScanner().find_missing_trailers.clear_cache()
        self.logger.info("Cache cleared successfully")
