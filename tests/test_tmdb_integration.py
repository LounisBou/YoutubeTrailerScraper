#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for TMDB workflow in YoutubeTrailerScraper."""
# pylint: disable=redefined-outer-name
# pylint: disable=duplicate-code

import os
import tempfile
from pathlib import Path

import pytest

from youtubetrailerscraper import YoutubeTrailerScraper


@pytest.fixture
def env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        env_file_path = f.name

    yield env_file_path

    # Cleanup
    os.unlink(env_file_path)


@pytest.fixture
def scraper(env_file):
    """Create a YoutubeTrailerScraper instance for testing."""
    return YoutubeTrailerScraper(env_file=env_file)


class TestMetadataExtraction:  # pylint: disable=protected-access
    """Test metadata extraction from directory paths."""

    def test_extract_movie_metadata_with_year(self, scraper):
        """Test extracting movie title and year from directory name."""
        movie_path = Path("/movies/Inception (2010)")
        title, year = scraper._extract_movie_metadata(movie_path)

        assert title == "Inception"
        assert year == 2010

    def test_extract_movie_metadata_without_year(self, scraper):
        """Test extracting movie title without year."""
        movie_path = Path("/movies/Inception")
        title, year = scraper._extract_movie_metadata(movie_path)

        assert title == "Inception"
        assert year is None

    def test_extract_movie_metadata_complex_title(self, scraper):
        """Test extracting movie with complex title containing parentheses."""
        movie_path = Path("/movies/Movie Title (Director's Cut) (2020)")
        title, year = scraper._extract_movie_metadata(movie_path)

        assert title == "Movie Title (Director's Cut)"
        assert year == 2020

    def test_extract_movie_metadata_special_characters(self, scraper):
        """Test extracting movie with special characters."""
        movie_path = Path("/movies/Movie: The Subtitle (2020)")
        title, year = scraper._extract_movie_metadata(movie_path)

        assert title == "Movie: The Subtitle"
        assert year == 2020

    def test_extract_tvshow_metadata_with_year(self, scraper):
        """Test extracting TV show title and year from directory name."""
        tvshow_path = Path("/tvshows/Breaking Bad (2008)")
        title, year = scraper._extract_tvshow_metadata(tvshow_path)

        assert title == "Breaking Bad"
        assert year == 2008

    def test_extract_tvshow_metadata_without_year(self, scraper):
        """Test extracting TV show title without year."""
        tvshow_path = Path("/tvshows/The Wire")
        title, year = scraper._extract_tvshow_metadata(tvshow_path)

        assert title == "The Wire"
        assert year is None

    def test_extract_tvshow_metadata_special_characters(self, scraper):
        """Test extracting TV show with special characters."""
        tvshow_path = Path("/tvshows/Show: Subtitle Edition (2020)")
        title, year = scraper._extract_tvshow_metadata(tvshow_path)

        assert title == "Show: Subtitle Edition"
        assert year == 2020


class TestSearchIntegration:
    """Test search integration with TMDBSearchEngine."""

    def test_search_for_movie_trailer_with_results(self, scraper, mocker):
        """Test searching for movie that has trailers on TMDB."""
        mock_urls = [
            "https://www.youtube.com/watch?v=abc123",
            "https://www.youtube.com/watch?v=def456",
        ]
        mocker.patch.object(scraper.tmdb_search_engine, "search_movie", return_value=mock_urls)

        result = scraper.search_for_movie_trailer("Inception", 2010)

        assert result == mock_urls
        scraper.tmdb_search_engine.search_movie.assert_called_once_with("Inception", 2010)

    def test_search_for_movie_trailer_no_results(self, scraper, mocker):
        """Test searching for movie with no trailers on TMDB."""
        mocker.patch.object(scraper.tmdb_search_engine, "search_movie", return_value=[])

        result = scraper.search_for_movie_trailer("Unknown Movie", 2020)

        assert result == []

    def test_search_for_movie_trailer_empty_title(self, scraper, mocker):
        """Test searching with empty title returns empty list."""
        mock_search = mocker.patch.object(scraper.tmdb_search_engine, "search_movie")

        result = scraper.search_for_movie_trailer("", 2020)

        assert result == []
        mock_search.assert_not_called()

    def test_search_for_tvshow_trailer_with_results(self, scraper, mocker):
        """Test searching for TV show that has trailers on TMDB."""
        mock_urls = ["https://www.youtube.com/watch?v=tv123"]
        mocker.patch.object(scraper.tmdb_search_engine, "search_tv_show", return_value=mock_urls)

        result = scraper.search_for_tvshow_trailer("Breaking Bad", 2008)

        assert result == mock_urls
        scraper.tmdb_search_engine.search_tv_show.assert_called_once_with("Breaking Bad", 2008)

    def test_search_for_tvshow_trailer_no_results(self, scraper, mocker):
        """Test searching for TV show with no trailers on TMDB."""
        mocker.patch.object(scraper.tmdb_search_engine, "search_tv_show", return_value=[])

        result = scraper.search_for_tvshow_trailer("Unknown Show", None)

        assert result == []

    def test_search_for_tvshow_trailer_empty_title(self, scraper, mocker):
        """Test searching TV show with empty title returns empty list."""
        mock_search = mocker.patch.object(scraper.tmdb_search_engine, "search_tv_show")

        result = scraper.search_for_tvshow_trailer("", None)

        assert result == []
        mock_search.assert_not_called()


class TestOrchestration:
    """Test orchestration methods for batch searching."""

    def test_search_trailers_for_movies_multiple_paths(self, scraper, mocker):
        """Test batch searching for multiple movies."""
        movie_paths = [
            Path("/movies/Inception (2010)"),
            Path("/movies/The Matrix (1999)"),
            Path("/movies/Unknown Movie"),
        ]

        # Mock search results
        def mock_search_movie(title, year):  # pylint: disable=unused-argument
            if title == "Inception":
                return ["https://www.youtube.com/watch?v=abc123"]
            if title == "The Matrix":
                return ["https://www.youtube.com/watch?v=def456"]
            return []

        mocker.patch.object(
            scraper.tmdb_search_engine, "search_movie", side_effect=mock_search_movie
        )

        results = scraper.search_trailers_for_movies(movie_paths)

        assert len(results) == 3
        assert len(results[movie_paths[0]]) == 1  # Inception found
        assert len(results[movie_paths[1]]) == 1  # The Matrix found
        assert len(results[movie_paths[2]]) == 0  # Unknown Movie not found

    def test_search_trailers_for_movies_empty_list(self, scraper):
        """Test batch searching with empty movie list."""
        results = scraper.search_trailers_for_movies([])

        assert results == {}

    def test_search_trailers_for_movies_extracts_metadata(self, scraper, mocker):
        """Test that metadata is extracted correctly before searching."""
        movie_paths = [Path("/movies/Test Movie (2020)")]

        mock_search = mocker.patch.object(
            scraper.tmdb_search_engine,
            "search_movie",
            return_value=["https://www.youtube.com/watch?v=test"],
        )

        scraper.search_trailers_for_movies(movie_paths)

        # Verify that extracted metadata is used for search
        mock_search.assert_called_once_with("Test Movie", 2020)

    def test_search_trailers_for_tvshows_multiple_paths(self, scraper, mocker):
        """Test batch searching for multiple TV shows."""
        tvshow_paths = [
            Path("/tvshows/Breaking Bad"),
            Path("/tvshows/The Wire (2002)"),
            Path("/tvshows/Unknown Show"),
        ]

        # Mock search results
        def mock_search_tv(title, year):  # pylint: disable=unused-argument
            if title == "Breaking Bad":
                return ["https://www.youtube.com/watch?v=tv1"]
            if title == "The Wire":
                return ["https://www.youtube.com/watch?v=tv2"]
            return []

        mocker.patch.object(
            scraper.tmdb_search_engine, "search_tv_show", side_effect=mock_search_tv
        )

        results = scraper.search_trailers_for_tvshows(tvshow_paths)

        assert len(results) == 3
        assert len(results[tvshow_paths[0]]) == 1  # Breaking Bad found
        assert len(results[tvshow_paths[1]]) == 1  # The Wire found
        assert len(results[tvshow_paths[2]]) == 0  # Unknown Show not found

    def test_search_trailers_for_tvshows_empty_list(self, scraper):
        """Test batch searching with empty TV show list."""
        results = scraper.search_trailers_for_tvshows([])

        assert results == {}

    def test_search_trailers_for_tvshows_extracts_metadata(self, scraper, mocker):
        """Test that TV show metadata is extracted correctly before searching."""
        tvshow_paths = [Path("/tvshows/Test Show (2021)")]

        mock_search = mocker.patch.object(
            scraper.tmdb_search_engine,
            "search_tv_show",
            return_value=["https://www.youtube.com/watch?v=test"],
        )

        scraper.search_trailers_for_tvshows(tvshow_paths)

        # Verify that extracted metadata is used for search
        mock_search.assert_called_once_with("Test Show", 2021)


class TestIntegrationWorkflow:
    """Test end-to-end workflow integration."""

    def test_full_workflow_scan_and_search_movies(self, tmp_path, mocker):
        """Test full workflow: scan for movies, then search TMDB."""
        # Create test movies without trailers
        movie1 = tmp_path / "Inception (2010)"
        movie1.mkdir()
        (movie1 / "movie.mp4").write_text("fake video")

        movie2 = tmp_path / "The Matrix (1999)"
        movie2.mkdir()
        (movie2 / "movie.mp4").write_text("fake video")

        # Create .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TMDB_API_KEY=test_api_key\n")
            f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
            f.write(f'MOVIES_PATHS=["{str(tmp_path)}/"]\n')
            f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
            f.write("USE_SMB_MOUNT=false\n")
            env_file = f.name

        try:
            scraper = YoutubeTrailerScraper(env_file=env_file)

            # Mock TMDB search
            mocker.patch.object(
                scraper.tmdb_search_engine,
                "search_movie",
                return_value=["https://www.youtube.com/watch?v=test"],
            )

            # Step 1: Scan for movies without trailers
            movies_without_trailers = scraper.scan_for_movies_without_trailers()
            assert len(movies_without_trailers) == 2

            # Step 2: Search TMDB for trailers
            results = scraper.search_trailers_for_movies(movies_without_trailers)

            # Verify results
            assert len(results) == 2
            for movie_path in movies_without_trailers:
                assert movie_path in results
                assert results[movie_path] == ["https://www.youtube.com/watch?v=test"]

        finally:
            os.unlink(env_file)

    def test_workflow_with_mixed_results(self, tmp_path, mocker):
        """Test workflow where some movies have trailers on TMDB and some don't."""
        # Create test movies
        movie1 = tmp_path / "Found Movie (2020)"
        movie1.mkdir()
        (movie1 / "movie.mp4").write_text("fake video")

        movie2 = tmp_path / "Not Found Movie (2020)"
        movie2.mkdir()
        (movie2 / "movie.mp4").write_text("fake video")

        # Create .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TMDB_API_KEY=test_api_key\n")
            f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
            f.write(f'MOVIES_PATHS=["{str(tmp_path)}/"]\n')
            f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
            f.write("USE_SMB_MOUNT=false\n")
            env_file = f.name

        try:
            scraper = YoutubeTrailerScraper(env_file=env_file)

            # Mock TMDB search with mixed results
            def mock_search(title, year):  # pylint: disable=unused-argument
                if title == "Found Movie":
                    return ["https://www.youtube.com/watch?v=found"]
                return []

            mocker.patch.object(
                scraper.tmdb_search_engine, "search_movie", side_effect=mock_search
            )

            # Scan and search
            movies_without_trailers = scraper.scan_for_movies_without_trailers()
            results = scraper.search_trailers_for_movies(movies_without_trailers)

            # Verify mixed results
            assert len(results) == 2
            assert len(results[movie1]) == 1  # Found on TMDB
            assert len(results[movie2]) == 0  # Not found on TMDB

        finally:
            os.unlink(env_file)
