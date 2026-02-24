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
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from youtubetrailerscraper.moviescanner import MovieScanner
from youtubetrailerscraper.tmdbsearchengine import TMDBSearchEngine
from youtubetrailerscraper.tvshowscanner import TVShowScanner
from youtubetrailerscraper.youtubedownloader import YoutubeDownloader


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
        self.youtube_cookies_from_browser: str = ""
        self.youtube_cookies_file: str = ""

        # Set up logger
        self.logger = logger or logging.getLogger(__name__)
        if not logger:
            # Add NullHandler to prevent "No handler found" warnings
            self.logger.addHandler(logging.NullHandler())

        # Load environment variables first
        self._load_environment_variables(env_file)

        # Initialize TMDB search engine
        self.tmdb_search_engine = TMDBSearchEngine(
            api_key=self.tmdb_api_key,
            base_url=self.tmdb_api_base_url,
            languages=self.tmdb_languages,
        )

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
        self.logger.debug(f"Loading environment from: {env_path}")

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

        # Load TMDB languages for multi-language search
        tmdb_languages_raw = self._get_env_var("TMDB_LANGUAGES", default='["en-US"]')
        self.tmdb_languages = self._parse_string_list(tmdb_languages_raw)

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
            # pylint: disable=logging-fstring-interpolation
            # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
            self.logger.debug(f"Applying SMB mount prefix: {self.smb_mount_point}")
            self.movies_paths = self._apply_smb_prefix(movies_paths_raw)
            self.tvshows_paths = self._apply_smb_prefix(tvshows_paths_raw)
        else:
            self.movies_paths = movies_paths_raw
            self.tvshows_paths = tvshows_paths_raw

        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.debug(f"Loaded {len(self.movies_paths)} movie paths")
        self.logger.debug(f"Loaded {len(self.tvshows_paths)} TV show paths")

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
                # pylint: disable=logging-fstring-interpolation
                # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
                self.logger.debug(f"Scan sample size set to: {self.scan_sample_size}")
            except ValueError:
                # pylint: disable=logging-fstring-interpolation
                # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
                self.logger.warning(
                    f"Invalid SCAN_SAMPLE_SIZE value '{scan_sample_str}', ignoring"
                )
                self.scan_sample_size = None

        # Load TV show season pattern
        season_pattern_raw = self._get_env_var(
            "TVSHOWS_SEASON_SUBDIR_PATTERN", default="Season {season_number}"
        )
        # Extract prefix before {season_number} (e.g., "Saison" from "Saison {season_number}")
        self.tvshow_season_pattern = season_pattern_raw.split("{")[0].strip()
        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.debug(f"TV show season pattern set to: {self.tvshow_season_pattern}")

        # Load YouTube cookie configuration for bypassing bot detection
        self.youtube_cookies_from_browser = self._get_env_var(
            "YOUTUBE_COOKIES_FROM_BROWSER", default=""
        )
        self.youtube_cookies_file = self._get_env_var("YOUTUBE_COOKIES_FILE", default="")

        # Initialize YouTube downloader with cookie configuration
        self.youtube_downloader = YoutubeDownloader(
            logger=self.logger,
            cookies_from_browser=self.youtube_cookies_from_browser or None,
            cookies_file=self.youtube_cookies_file or None,
        )

        if self.youtube_cookies_from_browser:  # pragma: no cover
            # pylint: disable=logging-fstring-interpolation
            self.logger.debug(
                f"YouTube downloader configured with cookies from:"
                f" {self.youtube_cookies_from_browser}"
            )
        elif self.youtube_cookies_file:  # pragma: no cover
            # pylint: disable=logging-fstring-interpolation
            self.logger.debug(
                f"YouTube downloader configured with cookies file:" f" {self.youtube_cookies_file}"
            )

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

    def _parse_string_list(self, list_str: str) -> list[str]:
        """
        Parse a string representation of a list into a list of strings

        Parameters:
            list_str (str): String representation of string list (Python list format)

        Returns:
            list[str]: List of strings

        Raises:
            ValueError: If list_str is not a valid Python list
        """
        try:
            # Use ast.literal_eval to safely parse the string as a Python list
            result_list = ast.literal_eval(list_str)
            if not isinstance(result_list, list):
                raise ValueError("Value must be a Python list")
            return [str(item) for item in result_list]
        except (ValueError, SyntaxError) as e:
            raise ValueError(
                f"Invalid list format: {list_str}. "
                f"Expected Python list format, e.g., ['item1', 'item2']. Error: {e}"
            ) from e

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

        # Determine sample size to use (0 = no sampling, all results)
        sample_size = self.scan_sample_size if use_sample and self.scan_sample_size else 0

        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.debug(f"Scanning {len(self.movies_paths)} movie directories...")
        for path in self.movies_paths:
            self.logger.debug(f"  - {path}")

        scanner = MovieScanner()
        missing_trailers = scanner.find_missing_trailers(self.movies_paths, sample_size)

        self.logger.info(f"Found {len(missing_trailers)} movies without trailers")
        for movie_path in missing_trailers:
            self.logger.debug(f"  - {movie_path}")

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

        # Determine sample size to use (0 = no sampling, all results)
        sample_size = self.scan_sample_size if use_sample and self.scan_sample_size else 0

        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.debug(f"Scanning {len(self.tvshows_paths)} TV show directories...")
        for path in self.tvshows_paths:
            self.logger.debug(f"  - {path}")

        scanner = TVShowScanner(season_pattern=self.tvshow_season_pattern)
        missing_trailers = scanner.find_missing_trailers(self.tvshows_paths, sample_size)

        self.logger.info(f"Found {len(missing_trailers)} TV shows without trailers")
        for tvshow_path in missing_trailers:
            self.logger.debug(f"  - {tvshow_path}")

        return missing_trailers

    def _extract_movie_metadata(self, movie_path: Path) -> tuple[str, int | None]:
        """Extract movie title and year from directory name.

        Parses movie directory names in common formats:
        - "Movie Title (Year)" → ("Movie Title", Year)
        - "Movie Title" → ("Movie Title", None)
        - "Movie Title (Director's Cut) (Year)" → ("Movie Title (Director's Cut)", Year)

        Args:
            movie_path: Path to movie directory.

        Returns:
            Tuple of (title, year). Year is None if not found.

        Example:
            >>> path = Path("/movies/Inception (2010)")
            >>> self._extract_movie_metadata(path)
            ('Inception', 2010)
        """
        dir_name = movie_path.name

        # Match year in parentheses at end: (YYYY)
        year_pattern = r"\((\d{4})\)\s*$"
        year_match = re.search(year_pattern, dir_name)

        if year_match:
            year = int(year_match.group(1))
            # Remove year from title
            title = dir_name[: year_match.start()].strip()
        else:
            year = None
            title = dir_name

        return title, year

    def _extract_tvshow_metadata(self, tvshow_path: Path) -> tuple[str, int | None]:
        """Extract TV show title and first air year from directory name.

        Parses TV show directory names in common formats:
        - "Show Title (Year)" → ("Show Title", Year)
        - "Show Title" → ("Show Title", None)

        Args:
            tvshow_path: Path to TV show directory.

        Returns:
            Tuple of (title, year). Year is None if not found.

        Example:
            >>> path = Path("/tvshows/Breaking Bad")
            >>> self._extract_tvshow_metadata(path)
            ('Breaking Bad', None)
        """
        dir_name = tvshow_path.name

        # Match year in parentheses at end: (YYYY)
        year_pattern = r"\((\d{4})\)\s*$"
        year_match = re.search(year_pattern, dir_name)

        if year_match:
            year = int(year_match.group(1))
            # Remove year from title
            title = dir_name[: year_match.start()].strip()
        else:
            year = None
            title = dir_name

        return title, year

    def search_for_movie_trailer(self, title: str, year: int | None) -> list[str]:
        """Search for movie trailer on TMDB.

        Uses TMDBSearchEngine to query the TMDB API for official trailer YouTube URLs.
        This is the primary method for finding trailers before falling back to direct
        YouTube search.

        Args:
            title: Movie title to search for.
            year: Optional movie release year to refine search results.

        Returns:
            List of YouTube URLs for trailers found on TMDB.
            Empty list if no trailers found or search fails.

        Example:
            >>> scraper = YoutubeTrailerScraper()
            >>> urls = scraper.search_for_movie_trailer("Inception", 2010)
            >>> print(urls)
            ['https://www.youtube.com/watch?v=YoHD9XEInc0']
        """
        if not title:
            self.logger.warning("Empty title provided for movie trailer search")
            return []

        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.debug(f"Searching TMDB for movie: {title} ({year})")

        youtube_urls = self.tmdb_search_engine.search_movie(title, year)

        if youtube_urls:
            # pylint: disable=logging-fstring-interpolation
            # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
            self.logger.info(f"Found {len(youtube_urls)} trailer(s) on TMDB for: {title}")
            for url in youtube_urls:
                self.logger.debug(f"  - {url}")
        else:
            # pylint: disable=logging-fstring-interpolation
            # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
            self.logger.debug(f"No TMDB trailers found for: {title}")

        return youtube_urls

    def search_for_tvshow_trailer(self, title: str, year: int | None) -> list[str]:
        """Search for TV show trailer on TMDB.

        Uses TMDBSearchEngine to query the TMDB API for official trailer YouTube URLs.
        This is the primary method for finding TV show trailers before falling back to
        direct YouTube search.

        Args:
            title: TV show title to search for.
            year: Optional first air year to refine search results.

        Returns:
            List of YouTube URLs for trailers found on TMDB.
            Empty list if no trailers found or search fails.

        Example:
            >>> scraper = YoutubeTrailerScraper()
            >>> urls = scraper.search_for_tvshow_trailer("Breaking Bad", 2008)
            >>> print(urls)
            ['https://www.youtube.com/watch?v=HhesaQXLuRY']
        """
        if not title:
            self.logger.warning("Empty title provided for TV show trailer search")
            return []

        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.debug(f"Searching TMDB for TV show: {title} ({year})")

        youtube_urls = self.tmdb_search_engine.search_tv_show(title, year)

        if youtube_urls:
            # pylint: disable=logging-fstring-interpolation
            # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
            self.logger.info(f"Found {len(youtube_urls)} trailer(s) on TMDB for: {title}")
            for url in youtube_urls:
                self.logger.debug(f"  - {url}")
        else:
            # pylint: disable=logging-fstring-interpolation
            # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
            self.logger.debug(f"No TMDB trailers found for: {title}")

        return youtube_urls

    def search_trailers_for_movies(self, movie_paths: list[Path]) -> dict[Path, list[str]]:
        """Search TMDB for trailers for multiple movies.

        Extracts metadata from each movie directory path and searches TMDB for trailers.
        This is a batch operation that processes multiple movies efficiently.

        Args:
            movie_paths: List of movie directory paths without trailers.

        Returns:
            Dictionary mapping movie path to list of YouTube URLs.
            Paths with no trailers found map to empty list.

        Example:
            >>> scraper = YoutubeTrailerScraper()
            >>> paths = [Path("/movies/Inception (2010)"), Path("/movies/The Matrix (1999)")]
            >>> results = scraper.search_trailers_for_movies(paths)
            >>> for path, urls in results.items():
            ...     print(f"{path.name}: {len(urls)} trailers")
        """
        results = {}

        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.info(f"Searching TMDB for {len(movie_paths)} movies...")

        for movie_path in movie_paths:
            # Extract metadata from directory name
            title, year = self._extract_movie_metadata(movie_path)

            # Search TMDB for trailers
            youtube_urls = self.search_for_movie_trailer(title, year)

            # Store results
            results[movie_path] = youtube_urls

        # Summary statistics
        found_count = sum(1 for urls in results.values() if urls)
        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.info(
            f"TMDB search complete: {found_count}/{len(movie_paths)} movies have trailers"
        )

        return results

    def search_trailers_for_tvshows(self, tvshow_paths: list[Path]) -> dict[Path, list[str]]:
        """Search TMDB for trailers for multiple TV shows.

        Extracts metadata from each TV show directory path and searches TMDB for trailers.
        This is a batch operation that processes multiple TV shows efficiently.

        Args:
            tvshow_paths: List of TV show directory paths without trailers.

        Returns:
            Dictionary mapping TV show path to list of YouTube URLs.
            Paths with no trailers found map to empty list.

        Example:
            >>> scraper = YoutubeTrailerScraper()
            >>> paths = [Path("/tvshows/Breaking Bad"), Path("/tvshows/The Wire (2002)")]
            >>> results = scraper.search_trailers_for_tvshows(paths)
            >>> for path, urls in results.items():
            ...     print(f"{path.name}: {len(urls)} trailers")
        """
        results = {}

        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.info(f"Searching TMDB for {len(tvshow_paths)} TV shows...")

        for tvshow_path in tvshow_paths:
            # Extract metadata from directory name
            title, year = self._extract_tvshow_metadata(tvshow_path)

            # Search TMDB for trailers
            youtube_urls = self.search_for_tvshow_trailer(title, year)

            # Store results
            results[tvshow_path] = youtube_urls

        # Summary statistics
        found_count = sum(1 for urls in results.values() if urls)
        # pylint: disable=logging-fstring-interpolation
        # LogIt from PyDevMate requires f-strings, doesn't support lazy % formatting
        self.logger.info(
            f"TMDB search complete: {found_count}/{len(tvshow_paths)} TV shows have trailers"
        )

        return results

    def download_trailers_for_movies(
        self, trailer_results: dict[Path, list[str]]
    ) -> dict[Path, list[Path]]:
        """Download trailers for multiple movies.

        Takes the results from search_trailers_for_movies and downloads each trailer
        to the corresponding movie directory.

        Args:
            trailer_results: Dictionary mapping movie paths to lists of YouTube URLs.

        Returns:
            Dictionary mapping movie paths to lists of downloaded file paths.
            Paths with no successful downloads map to empty list.

        Example:
            >>> scraper = YoutubeTrailerScraper()
            >>> search_results = scraper.search_trailers_for_movies(movie_paths)
            >>> downloads = scraper.download_trailers_for_movies(search_results)
            >>> for path, files in downloads.items():
            ...     print(f"{path.name}: {len(files)} trailers downloaded")
        """
        download_results: dict[Path, list[Path]] = {}
        total_urls = sum(len(urls) for urls in trailer_results.values())

        # pylint: disable=logging-fstring-interpolation
        self.logger.info(f"Downloading {total_urls} trailers for {len(trailer_results)} movies...")

        for movie_path, youtube_urls in trailer_results.items():
            if not youtube_urls:
                download_results[movie_path] = []
                continue

            downloaded_paths = self.youtube_downloader.download_trailers_for_movie(
                movie_path, youtube_urls
            )
            download_results[movie_path] = downloaded_paths

        # Summary statistics
        total_downloaded = sum(len(paths) for paths in download_results.values())
        # pylint: disable=logging-fstring-interpolation
        self.logger.info(f"Download complete: {total_downloaded}/{total_urls} trailers downloaded")

        return download_results

    def download_trailers_for_tvshows(
        self, trailer_results: dict[Path, list[str]]
    ) -> dict[Path, list[Path]]:
        """Download trailers for multiple TV shows.

        Takes the results from search_trailers_for_tvshows and downloads each trailer
        to the corresponding TV show's trailers subdirectory.

        Args:
            trailer_results: Dictionary mapping TV show paths to lists of YouTube URLs.

        Returns:
            Dictionary mapping TV show paths to lists of downloaded file paths.
            Paths with no successful downloads map to empty list.

        Example:
            >>> scraper = YoutubeTrailerScraper()
            >>> search_results = scraper.search_trailers_for_tvshows(tvshow_paths)
            >>> downloads = scraper.download_trailers_for_tvshows(search_results)
            >>> for path, files in downloads.items():
            ...     print(f"{path.name}: {len(files)} trailers downloaded")
        """
        download_results: dict[Path, list[Path]] = {}
        total_urls = sum(len(urls) for urls in trailer_results.values())

        # pylint: disable=logging-fstring-interpolation
        self.logger.info(
            f"Downloading {total_urls} trailers for {len(trailer_results)} TV shows..."
        )

        for tvshow_path, youtube_urls in trailer_results.items():
            if not youtube_urls:
                download_results[tvshow_path] = []
                continue

            downloaded_paths = self.youtube_downloader.download_trailers_for_tvshow(
                tvshow_path, youtube_urls
            )
            download_results[tvshow_path] = downloaded_paths

        # Summary statistics
        total_downloaded = sum(len(paths) for paths in download_results.values())
        # pylint: disable=logging-fstring-interpolation
        self.logger.info(f"Download complete: {total_downloaded}/{total_urls} trailers downloaded")

        return download_results

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
        tvshow_scanner = TVShowScanner(season_pattern=self.tvshow_season_pattern)
        tvshow_scanner.find_missing_trailers.clear_cache()
        self.logger.info("Cache cleared successfully")
