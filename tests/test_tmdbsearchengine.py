#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for TMDBSearchEngine class."""
# pylint: disable=protected-access  # Testing protected methods is legitimate

from unittest.mock import MagicMock, patch

import pytest
import requests

from youtubetrailerscraper.tmdbsearchengine import TMDBSearchEngine


class TestTMDBSearchEngineInit:
    """Test TMDBSearchEngine initialization."""

    def test_init_with_api_key(self):
        """Test initialization with valid API key."""
        engine = TMDBSearchEngine(api_key="test_key")
        assert engine.api_key == "test_key"
        assert engine.base_url == "https://api.themoviedb.org/3"
        assert engine.timeout == 10
        assert engine.max_retries == 3
        assert engine.retry_delay == 1.0

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        engine = TMDBSearchEngine(
            api_key="test_key",
            base_url="https://custom.api.com/v1",
            timeout=20,
            max_retries=5,
            retry_delay=2.0,
        )
        assert engine.api_key == "test_key"
        assert engine.base_url == "https://custom.api.com/v1"
        assert engine.timeout == 20
        assert engine.max_retries == 5
        assert engine.retry_delay == 2.0

    def test_init_strips_trailing_slash_from_base_url(self):
        """Test that trailing slash is stripped from base URL."""
        engine = TMDBSearchEngine(api_key="test_key", base_url="https://api.com/")
        assert engine.base_url == "https://api.com"

    def test_init_with_empty_api_key_raises_error(self):
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="TMDB API key cannot be empty"):
            TMDBSearchEngine(api_key="")

    def test_init_with_none_api_key_raises_error(self):
        """Test that None API key raises ValueError."""
        with pytest.raises(ValueError, match="TMDB API key cannot be empty"):
            TMDBSearchEngine(api_key=None)


class TestTMDBSearchEngineMakeRequest:
    """Test TMDBSearchEngine._make_request method."""

    def test_make_request_successful(self):
        """Test successful API request."""
        engine = TMDBSearchEngine(api_key="test_key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [{"id": 123}]}

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = engine._make_request("/search/movie", {"query": "Inception"})

            assert result == {"results": [{"id": 123}]}
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args.kwargs["params"]["api_key"] == "test_key"
            assert call_args.kwargs["params"]["query"] == "Inception"
            assert call_args.kwargs["timeout"] == 10

    def test_make_request_with_retry_success(self):
        """Test API request that succeeds after retry."""
        engine = TMDBSearchEngine(api_key="test_key", retry_delay=0.01)
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}

        with patch("requests.get") as mock_get:
            # First call fails, second succeeds
            mock_get.side_effect = [
                requests.exceptions.Timeout("Timeout"),
                mock_response,
            ]

            result = engine._make_request("/search/movie")
            assert result == {"results": []}
            assert mock_get.call_count == 2

    def test_make_request_all_retries_fail(self):
        """Test API request that fails after all retries."""
        engine = TMDBSearchEngine(api_key="test_key", max_retries=2, retry_delay=0.01)

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")

            with pytest.raises(requests.exceptions.Timeout):
                engine._make_request("/search/movie")

            assert mock_get.call_count == 2

    def test_make_request_http_error(self):
        """Test API request with HTTP error."""
        engine = TMDBSearchEngine(api_key="test_key", max_retries=1, retry_delay=0.01)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError):
                engine._make_request("/search/movie")


class TestTMDBSearchEngineExtractYoutubeUrls:
    """Test TMDBSearchEngine._extract_youtube_urls method."""

    def test_extract_youtube_urls_single_trailer(self):
        """Test extracting single YouTube trailer URL."""
        engine = TMDBSearchEngine(api_key="test_key")
        videos = [
            {"site": "YouTube", "type": "Trailer", "key": "abc123"},
        ]
        result = engine._extract_youtube_urls(videos)
        assert result == ["https://www.youtube.com/watch?v=abc123"]

    def test_extract_youtube_urls_multiple_trailers(self):
        """Test extracting multiple YouTube trailer URLs."""
        engine = TMDBSearchEngine(api_key="test_key")
        videos = [
            {"site": "YouTube", "type": "Trailer", "key": "abc123"},
            {"site": "YouTube", "type": "Trailer", "key": "def456"},
            {"site": "YouTube", "type": "Trailer", "key": "ghi789"},
        ]
        result = engine._extract_youtube_urls(videos)
        assert result == [
            "https://www.youtube.com/watch?v=abc123",
            "https://www.youtube.com/watch?v=def456",
            "https://www.youtube.com/watch?v=ghi789",
        ]

    def test_extract_youtube_urls_filters_non_trailers(self):
        """Test that non-trailer videos are filtered out."""
        engine = TMDBSearchEngine(api_key="test_key")
        videos = [
            {"site": "YouTube", "type": "Trailer", "key": "abc123"},
            {"site": "YouTube", "type": "Teaser", "key": "teaser"},
            {"site": "YouTube", "type": "Clip", "key": "clip"},
            {"site": "YouTube", "type": "Featurette", "key": "feature"},
        ]
        result = engine._extract_youtube_urls(videos)
        assert result == ["https://www.youtube.com/watch?v=abc123"]

    def test_extract_youtube_urls_filters_non_youtube(self):
        """Test that non-YouTube videos are filtered out."""
        engine = TMDBSearchEngine(api_key="test_key")
        videos = [
            {"site": "YouTube", "type": "Trailer", "key": "abc123"},
            {"site": "Vimeo", "type": "Trailer", "key": "vimeo_key"},
            {"site": "Dailymotion", "type": "Trailer", "key": "daily_key"},
        ]
        result = engine._extract_youtube_urls(videos)
        assert result == ["https://www.youtube.com/watch?v=abc123"]

    def test_extract_youtube_urls_empty_list(self):
        """Test extracting from empty video list."""
        engine = TMDBSearchEngine(api_key="test_key")
        result = engine._extract_youtube_urls([])
        assert not result

    def test_extract_youtube_urls_missing_key(self):
        """Test extracting when video key is missing."""
        engine = TMDBSearchEngine(api_key="test_key")
        videos = [
            {"site": "YouTube", "type": "Trailer", "key": "abc123"},
            {"site": "YouTube", "type": "Trailer"},  # Missing key
            {"site": "YouTube", "type": "Trailer", "key": ""},  # Empty key
        ]
        result = engine._extract_youtube_urls(videos)
        assert result == ["https://www.youtube.com/watch?v=abc123"]


class TestTMDBSearchEngineSearchMovie:
    """Test TMDBSearchEngine.search_movie method."""

    def test_search_movie_with_trailers(self):
        """Test searching for movie that has trailers."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = [
                {"results": [{"id": 123, "title": "Inception"}]},
                {"results": [{"site": "YouTube", "type": "Trailer", "key": "abc123"}]},
            ]

            result = engine.search_movie("Inception", year=2010)

            assert result == ["https://www.youtube.com/watch?v=abc123"]
            assert mock_request.call_count == 2
            mock_request.assert_any_call("/search/movie", {"query": "Inception", "year": 2010})
            mock_request.assert_any_call("/movie/123/videos")

    def test_search_movie_without_year(self):
        """Test searching for movie without year parameter."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = [
                {"results": [{"id": 456}]},
                {"results": [{"site": "YouTube", "type": "Trailer", "key": "xyz789"}]},
            ]

            result = engine.search_movie("Inception")

            assert result == ["https://www.youtube.com/watch?v=xyz789"]
            mock_request.assert_any_call("/search/movie", {"query": "Inception"})

    def test_search_movie_no_results(self):
        """Test searching for movie that returns no results."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.return_value = {"results": []}
            result = engine.search_movie("NonexistentMovie")
            assert not result

    def test_search_movie_no_trailers(self):
        """Test searching for movie that has no trailers."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = [
                {"results": [{"id": 123}]},
                {"results": []},
            ]
            result = engine.search_movie("Inception")
            assert not result

    def test_search_movie_empty_title(self):
        """Test searching with empty title returns empty list."""
        engine = TMDBSearchEngine(api_key="test_key")
        result = engine.search_movie("")
        assert not result

    def test_search_movie_api_error(self):
        """Test handling API errors during movie search."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = requests.exceptions.RequestException("API Error")
            result = engine.search_movie("Inception")
            assert not result

    def test_search_movie_missing_movie_id(self):
        """Test handling missing movie ID in search results."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.return_value = {"results": [{"title": "Inception"}]}  # No id
            result = engine.search_movie("Inception")
            assert not result


class TestTMDBSearchEngineSearchTVShow:
    """Test TMDBSearchEngine.search_tv_show method."""

    def test_search_tv_show_with_trailers(self):
        """Test searching for TV show that has trailers."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = [
                {"results": [{"id": 789, "name": "Breaking Bad"}]},
                {"results": [{"site": "YouTube", "type": "Trailer", "key": "tv123"}]},
            ]

            result = engine.search_tv_show("Breaking Bad", year=2008)

            assert result == ["https://www.youtube.com/watch?v=tv123"]
            assert mock_request.call_count == 2
            mock_request.assert_any_call(
                "/search/tv", {"query": "Breaking Bad", "first_air_date_year": 2008}
            )
            mock_request.assert_any_call("/tv/789/videos")

    def test_search_tv_show_without_year(self):
        """Test searching for TV show without year parameter."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = [
                {"results": [{"id": 999}]},
                {"results": [{"site": "YouTube", "type": "Trailer", "key": "show456"}]},
            ]

            result = engine.search_tv_show("Breaking Bad")

            assert result == ["https://www.youtube.com/watch?v=show456"]
            mock_request.assert_any_call("/search/tv", {"query": "Breaking Bad"})

    def test_search_tv_show_no_results(self):
        """Test searching for TV show that returns no results."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.return_value = {"results": []}
            result = engine.search_tv_show("NonexistentShow")
            assert not result

    def test_search_tv_show_no_trailers(self):
        """Test searching for TV show that has no trailers."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = [
                {"results": [{"id": 789}]},
                {"results": []},
            ]
            result = engine.search_tv_show("Breaking Bad")
            assert not result

    def test_search_tv_show_empty_title(self):
        """Test searching with empty title returns empty list."""
        engine = TMDBSearchEngine(api_key="test_key")
        result = engine.search_tv_show("")
        assert not result

    def test_search_tv_show_api_error(self):
        """Test handling API errors during TV show search."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = requests.exceptions.RequestException("API Error")
            result = engine.search_tv_show("Breaking Bad")
            assert not result

    def test_search_tv_show_missing_tv_id(self):
        """Test handling missing TV ID in search results."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.return_value = {"results": [{"name": "Breaking Bad"}]}  # No id
            result = engine.search_tv_show("Breaking Bad")
            assert not result

    def test_search_tv_show_multiple_trailers(self):
        """Test TV show with multiple trailers."""
        engine = TMDBSearchEngine(api_key="test_key")

        with patch.object(engine, "_make_request") as mock_request:
            mock_request.side_effect = [
                {"results": [{"id": 789}]},
                {
                    "results": [
                        {"site": "YouTube", "type": "Trailer", "key": "trailer1"},
                        {"site": "YouTube", "type": "Trailer", "key": "trailer2"},
                    ]
                },
            ]

            result = engine.search_tv_show("Breaking Bad")
            assert len(result) == 2
            assert "https://www.youtube.com/watch?v=trailer1" in result
            assert "https://www.youtube.com/watch?v=trailer2" in result
