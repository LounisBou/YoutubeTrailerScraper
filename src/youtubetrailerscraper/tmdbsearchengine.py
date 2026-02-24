#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TMDB Search Engine - Query TMDB API for trailer YouTube URLs.

This module provides the TMDBSearchEngine class which searches The Movie Database
(TMDB) API for official trailer information. It returns YouTube URLs for trailers
found in TMDB's video database.

Usage:
    from youtubetrailerscraper.tmdbsearchengine import TMDBSearchEngine

    engine = TMDBSearchEngine(api_key="your_api_key")
    movie_trailers = engine.search_movie("Inception", year=2010)
    tv_trailers = engine.search_tv_show("Breaking Bad", year=2008)

Requirements:
    - requests library for HTTP API calls
    - Valid TMDB API key from https://www.themoviedb.org/settings/api

References:
    - TMDB API: https://developers.themoviedb.org/3
    - Search Movies: https://developers.themoviedb.org/3/search/search-movies
    - Search TV Shows: https://developers.themoviedb.org/3/search/search-tv-shows
    - Get Videos: https://developers.themoviedb.org/3/movies/get-movie-videos
"""

from __future__ import annotations

import time
import unicodedata
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from pydevmate import CacheIt


class TMDBSearchEngine:
    """Query TMDB API for official trailer YouTube URLs.

    This class provides methods to search for movies and TV shows on TMDB
    and retrieve their official trailer YouTube URLs. It handles API
    authentication, rate limiting, and error handling.

    Attributes:
        api_key: TMDB API key for authentication.
        base_url: Base URL for TMDB API (default: https://api.themoviedb.org/3).
        timeout: HTTP request timeout in seconds (default: 10).
        max_retries: Maximum number of retry attempts for failed requests (default: 3).
        retry_delay: Delay between retry attempts in seconds (default: 1).
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        api_key: str,
        base_url: str = "https://api.themoviedb.org/3",
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        languages: Optional[list[str]] = None,
    ):
        """Initialize TMDBSearchEngine with API credentials.

        Args:
            api_key: TMDB API key for authentication.
            base_url: Base URL for TMDB API endpoints.
            timeout: HTTP request timeout in seconds.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_delay: Delay between retry attempts in seconds.
            languages: List of TMDB language codes to try in order (e.g., ["fr-FR", "en-US"]).
                      Defaults to ["en-US"] if not provided.

        Raises:
            ValueError: If api_key is empty or None.
        """
        if not api_key:
            raise ValueError("TMDB API key cannot be empty")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.languages = languages if languages else ["en-US"]

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normalize title by removing accents and replacing special characters.

        This helps improve TMDB search matching for titles with special characters
        and accents (e.g., "Astérix" → "Asterix", "& " → "and ").

        Args:
            title: Original title string to normalize.

        Returns:
            Normalized title with accents removed and special characters replaced.

        Example:
            >>> TMDBSearchEngine._normalize_title("Astérix & Obélix")
            'Asterix and Obelix'
        """
        # Remove accents using Unicode normalization
        # NFD = Canonical Decomposition (separates base char from accent)
        nfd_form = unicodedata.normalize("NFD", title)
        # Keep only non-combining characters (removes accents)
        without_accents = "".join(char for char in nfd_form if unicodedata.category(char) != "Mn")

        # Replace common special characters
        normalized = without_accents.replace("&", "and")

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def _make_request(
        self, endpoint: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Make HTTP GET request to TMDB API with retry logic.

        Args:
            endpoint: API endpoint path (e.g., "/search/movie").
            params: Query parameters for the request.

        Returns:
            JSON response as dictionary.

        Raises:
            requests.exceptions.RequestException: If request fails after all retries.
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        request_params = {"api_key": self.api_key}
        if params:
            request_params.update(params)

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=request_params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)

        return {}  # pragma: no cover - Should never reach here due to raise above

    def _extract_youtube_urls(self, videos: list[dict]) -> list[str]:
        """Extract YouTube URLs from TMDB video results.

        Args:
            videos: List of video dictionaries from TMDB API.

        Returns:
            List of YouTube URLs for trailers found.
        """
        youtube_urls = []
        for video in videos:
            if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                video_key = video.get("key")
                if video_key:
                    youtube_urls.append(f"https://www.youtube.com/watch?v={video_key}")
        return youtube_urls

    def _search_movie_with_language(
        self, title: str, year: Optional[int], language: str
    ) -> tuple[Optional[int], list[dict]]:
        """Search for movie with a specific language setting.

        Tries searching with the original title first. If no results are found,
        attempts a second search with normalized title (accents removed, special
        characters replaced) to improve matching.

        Args:
            title: Movie title to search for.
            year: Optional release year.
            language: TMDB language code (e.g., "fr-FR", "en-US").

        Returns:
            Tuple of (movie_id, videos_list). Returns (None, []) if no results found.
        """
        search_params: dict[str, Any] = {"query": title, "language": language}
        if year:
            search_params["year"] = year

        search_results = self._make_request("/search/movie", search_params)
        results = search_results.get("results", [])

        # If no results with original title, try with normalized title
        if not results:
            normalized_title = self._normalize_title(title)
            # Only retry if normalized title is different from original
            if normalized_title != title:
                search_params["query"] = normalized_title
                search_results = self._make_request("/search/movie", search_params)
                results = search_results.get("results", [])

        if not results:
            return None, []

        # Get videos for the first (most relevant) result
        movie_id = results[0].get("id")
        if not movie_id:
            return None, []

        videos_response = self._make_request(f"/movie/{movie_id}/videos")
        videos = videos_response.get("results", [])

        return movie_id, videos

    def _search_tv_show_with_language(
        self, title: str, year: Optional[int], language: str
    ) -> tuple[Optional[int], list[dict]]:
        """Search for TV show with a specific language setting.

        Tries searching with the original title first. If no results are found,
        attempts a second search with normalized title (accents removed, special
        characters replaced) to improve matching.

        Args:
            title: TV show title to search for.
            year: Optional first air year.
            language: TMDB language code (e.g., "fr-FR", "en-US").

        Returns:
            Tuple of (tv_show_id, videos_list). Returns (None, []) if no results found.
        """
        search_params: dict[str, Any] = {"query": title, "language": language}
        if year:
            search_params["first_air_date_year"] = year

        search_results = self._make_request("/search/tv", search_params)
        results = search_results.get("results", [])

        # If no results with original title, try with normalized title
        if not results:
            normalized_title = self._normalize_title(title)
            # Only retry if normalized title is different from original
            if normalized_title != title:
                search_params["query"] = normalized_title
                search_results = self._make_request("/search/tv", search_params)
                results = search_results.get("results", [])

        if not results:
            return None, []

        # Get videos for the first (most relevant) result
        tv_id = results[0].get("id")
        if not tv_id:
            return None, []

        videos_response = self._make_request(f"/tv/{tv_id}/videos")
        videos = videos_response.get("results", [])

        return tv_id, videos

    @CacheIt(max_duration=86400, backend="diskcache")  # 24 hour cache
    def search_movie(self, title: str, year: Optional[int] = None) -> list[str]:
        """Search for movie trailers on TMDB with multi-language fallback.

        Tries searching with each configured language in order until results are found.

        Args:
            title: Movie title to search for.
            year: Optional release year to refine search results.

        Returns:
            List of YouTube URLs for movie trailers found on TMDB.
            Empty list if no trailers found or if search fails.

        Example:
            >>> engine = TMDBSearchEngine(api_key="your_key", languages=["fr-FR", "en-US"])
            >>> urls = engine.search_movie("Ant-Man et la Guêpe Quantumania", year=2023)
            >>> print(urls)
            ['https://www.youtube.com/watch?v=5WfTEZJnv_8']
        """
        if not title:
            return []

        try:
            # Try each language in order until we find results
            for language in self.languages:
                movie_id, videos = self._search_movie_with_language(title, year, language)

                if movie_id and videos:
                    youtube_urls = self._extract_youtube_urls(videos)
                    if youtube_urls:
                        return youtube_urls

            # No results found with any language
            return []

        except requests.exceptions.RequestException:
            return []

    @CacheIt(max_duration=86400, backend="diskcache")  # 24 hour cache
    def search_tv_show(self, title: str, year: Optional[int] = None) -> list[str]:
        """Search for TV show trailers on TMDB with multi-language fallback.

        Tries searching with each configured language in order until results are found.

        Args:
            title: TV show title to search for.
            year: Optional first air year to refine search results.

        Returns:
            List of YouTube URLs for TV show trailers found on TMDB.
            Empty list if no trailers found or if search fails.

        Example:
            >>> engine = TMDBSearchEngine(api_key="your_key", languages=["fr-FR", "en-US"])
            >>> urls = engine.search_tv_show("Breaking Bad", year=2008)
            >>> print(urls)
            ['https://www.youtube.com/watch?v=HhesaQXLuRY']
        """
        if not title:
            return []

        try:
            # Try each language in order until we find results
            for language in self.languages:
                tv_id, videos = self._search_tv_show_with_language(title, year, language)

                if tv_id and videos:
                    youtube_urls = self._extract_youtube_urls(videos)
                    if youtube_urls:
                        return youtube_urls

            # No results found with any language
            return []

        except requests.exceptions.RequestException:
            return []
