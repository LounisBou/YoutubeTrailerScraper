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
from typing import Any, Optional
from urllib.parse import urljoin

import requests


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
    ):
        """Initialize TMDBSearchEngine with API credentials.

        Args:
            api_key: TMDB API key for authentication.
            base_url: Base URL for TMDB API endpoints.
            timeout: HTTP request timeout in seconds.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_delay: Delay between retry attempts in seconds.

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

        return {}  # Should never reach here due to raise above

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

    def search_movie(self, title: str, year: Optional[int] = None) -> list[str]:
        """Search for movie trailers on TMDB.

        Args:
            title: Movie title to search for.
            year: Optional release year to refine search results.

        Returns:
            List of YouTube URLs for movie trailers found on TMDB.
            Empty list if no trailers found or if search fails.

        Example:
            >>> engine = TMDBSearchEngine(api_key="your_key")
            >>> urls = engine.search_movie("Inception", year=2010)
            >>> print(urls)
            ['https://www.youtube.com/watch?v=YoHD9XEInc0']
        """
        if not title:
            return []

        try:
            # Search for the movie
            search_params: dict[str, Any] = {"query": title}
            if year:
                search_params["year"] = year

            search_results = self._make_request("/search/movie", search_params)
            results = search_results.get("results", [])

            if not results:
                return []

            # Get videos for the first (most relevant) result
            movie_id = results[0].get("id")
            if not movie_id:
                return []

            videos_response = self._make_request(f"/movie/{movie_id}/videos")
            videos = videos_response.get("results", [])

            return self._extract_youtube_urls(videos)

        except requests.exceptions.RequestException:
            return []

    def search_tv_show(self, title: str, year: Optional[int] = None) -> list[str]:
        """Search for TV show trailers on TMDB.

        Args:
            title: TV show title to search for.
            year: Optional first air year to refine search results.

        Returns:
            List of YouTube URLs for TV show trailers found on TMDB.
            Empty list if no trailers found or if search fails.

        Example:
            >>> engine = TMDBSearchEngine(api_key="your_key")
            >>> urls = engine.search_tv_show("Breaking Bad", year=2008)
            >>> print(urls)
            ['https://www.youtube.com/watch?v=HhesaQXLuRY']
        """
        if not title:
            return []

        try:
            # Search for the TV show
            search_params: dict[str, Any] = {"query": title}
            if year:
                search_params["first_air_date_year"] = year

            search_results = self._make_request("/search/tv", search_params)
            results = search_results.get("results", [])

            if not results:
                return []

            # Get videos for the first (most relevant) result
            tv_id = results[0].get("id")
            if not tv_id:
                return []

            videos_response = self._make_request(f"/tv/{tv_id}/videos")
            videos = videos_response.get("results", [])

            return self._extract_youtube_urls(videos)

        except requests.exceptions.RequestException:
            return []
