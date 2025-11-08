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
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class YoutubeTrailerScraper:  # pylint: disable=too-many-instance-attributes
    """Scan tvshows and movies folders, download trailer on youtube"""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize YoutubeTrailerScraper

        Parameters:
            env_file (str, optional): Path to .env file. Defaults to .env in current directory.
        """
        # Configuration attributes
        self.tmdb_api_key: str = ""
        self.tmdb_read_access_token: str = ""
        self.tmdb_api_base_url: str = ""
        self.movies_paths: list[Path] = []
        self.tvshows_paths: list[Path] = []
        self.smb_mount_point: str = ""
        self.youtube_search_url: str = ""
        self.default_search_query_format: str = ""

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
        if not Path(env_path).exists():
            raise FileNotFoundError(
                f"Environment file not found: {env_path}. "
                "Please create a .env file based on .env.example"
            )

        # Load the environment file
        load_dotenv(env_path, override=True)

        # Load TMDB API configuration
        self.tmdb_api_key = self._get_env_var("TMDB_API_KEY", required=True)
        self.tmdb_read_access_token = self._get_env_var("TMDB_READ_ACCESS_TOKEN", required=True)
        self.tmdb_api_base_url = self._get_env_var(
            "TMDB_API_BASE_URL", default="https://api.themoviedb.org/3"
        )

        # Load media paths
        self.movies_paths = self._parse_path_list(self._get_env_var("MOVIES_PATHS", required=True))
        self.tvshows_paths = self._parse_path_list(
            self._get_env_var("TVSHOWS_PATHS", required=True)
        )

        # Load optional configurations
        self.smb_mount_point = self._get_env_var("SMB_MOUNT_POINT", default="")
        self.youtube_search_url = self._get_env_var(
            "YOUTUBE_SEARCH_URL",
            default="https://www.youtube.com/results?search_query={query}",
        )
        self.default_search_query_format = self._get_env_var(
            "DEFAULT_SEARCH_QUERY_FORMAT", default="{title} {year} bande annonce"
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

    def scan_for_movies_without_trailers(
        self, path: Path  # pylint: disable=unused-argument
    ) -> list[Path]:
        """
        Scan for movies without trailers in the given path

        Parameters:
            path (Path): Path to scan for movies without trailers
        Returns:
            list[Path]: List of movies without trailers
        """
        # pylint: disable=fixme
        # TODO: Implement in Step 3
        # Retrieve movies folders from environment variable
        # For each movies folders
        # Check if movies folder exists
        # Scan for movies without trailers in the folder
        return []

    def scan_for_tvshows_without_trailers(
        self, path: Path  # pylint: disable=unused-argument
    ) -> list[Path]:
        """
        Scan for tvshows without trailers in the given path

        Parameters:
            path (Path): Path to scan for tvshows without trailers
        Returns:
            list[Path]: List of tvshows without trailers
        """
        # pylint: disable=fixme
        # TODO: Implement in Step 3
        # Retrieve tvshows folders from environment variable
        # For each tvshows folders
        # Check if tvshows folder exists
        # Scan for tvshows without trailers in the folder
        return []

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
