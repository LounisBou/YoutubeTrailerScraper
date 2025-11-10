#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=duplicate-code
"""Tests for YoutubeTrailerScraper main functionality (scanning, caching, searching)."""

import os
import tempfile

from youtubetrailerscraper import YoutubeTrailerScraper  # pylint: disable=import-error


def test_scan_for_movies_without_trailers_empty_paths():
    """Test scan_for_movies_without_trailers with empty movies_paths."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write("MOVIES_PATHS=[]\n")
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        f.write('TMDB_LANGUAGES=["en-US"]\n')
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        results = scraper.scan_for_movies_without_trailers()
        assert not results
    finally:
        os.unlink(env_file)


def test_scan_for_movies_with_sample_mode(tmp_path):
    """Test scan_for_movies_without_trailers with sample mode enabled."""
    # Create test movies
    for i in range(5):
        movie = tmp_path / f"Movie{i}"
        movie.mkdir()
        (movie / "movie.mp4").write_text("fake video")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write(f'MOVIES_PATHS=["{str(tmp_path)}/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        f.write('TMDB_LANGUAGES=["en-US"]\n')
        f.write("SCAN_SAMPLE_SIZE=3\n")
        f.write("USE_SMB_MOUNT=false\n")  # Disable SMB mount
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        results = scraper.scan_for_movies_without_trailers(use_sample=True)
        # Sample mode IS supported with CacheIt via sample_size parameter
        assert len(results) == 3
    finally:
        os.unlink(env_file)


def test_scan_for_tvshows_without_trailers_empty_paths():
    """Test scan_for_tvshows_without_trailers with empty tvshows_paths."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write("TVSHOWS_PATHS=[]\n")
        f.write('TMDB_LANGUAGES=["en-US"]\n')
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        results = scraper.scan_for_tvshows_without_trailers()
        assert not results
    finally:
        os.unlink(env_file)


def test_scan_for_tvshows_with_sample_mode(tmp_path):
    """Test scan_for_tvshows_without_trailers with sample mode enabled."""
    # Create test TV shows
    for i in range(5):
        tvshow = tmp_path / f"Show{i}"
        tvshow.mkdir()
        season1 = tvshow / "Season 01"
        season1.mkdir()
        (season1 / "episode.mp4").write_text("fake video")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write(f'TVSHOWS_PATHS=["{str(tmp_path)}/"]\n')
        f.write('TMDB_LANGUAGES=["en-US"]\n')
        f.write("SCAN_SAMPLE_SIZE=3\n")
        f.write("USE_SMB_MOUNT=false\n")  # Disable SMB mount
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        results = scraper.scan_for_tvshows_without_trailers(use_sample=True)
        # Sample mode IS supported with CacheIt via sample_size parameter
        assert len(results) == 3
    finally:
        os.unlink(env_file)


def test_clear_cache():
    """Test the clear_cache method."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        f.write('TMDB_LANGUAGES=["en-US"]\n')
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        # Just verify the method can be called without errors
        scraper.clear_cache()
    finally:
        os.unlink(env_file)


def test_search_for_movie_trailer(mocker):
    """Test the search_for_movie_trailer method with mocked TMDB search engine."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        f.write('TMDB_LANGUAGES=["en-US"]\n')
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)

        # Mock the TMDBSearchEngine.search_movie method
        mock_search = mocker.patch.object(
            scraper.tmdb_search_engine,
            "search_movie",
            return_value=["https://www.youtube.com/watch?v=test123"],
        )

        # Test the method calls TMDBSearchEngine and returns results
        result = scraper.search_for_movie_trailer("Test Movie", 2020)

        # Verify TMDBSearchEngine.search_movie was called
        mock_search.assert_called_once_with("Test Movie", 2020)

        # Verify results
        assert result == ["https://www.youtube.com/watch?v=test123"]
    finally:
        os.unlink(env_file)
