#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for environment variable loading in YoutubeTrailerScraper."""

import os
import tempfile
from pathlib import Path

import pytest

from youtubetrailerscraper import YoutubeTrailerScraper  # pylint: disable=import-error


def test_env_loading_with_valid_file():
    """Test that environment variables are loaded correctly from .env file."""
    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write("TMDB_API_BASE_URL=https://api.themoviedb.org/3\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)

        assert scraper.tmdb_api_key == "test_api_key"
        assert scraper.tmdb_read_access_token == "test_token"
        assert scraper.tmdb_api_base_url == "https://api.themoviedb.org/3"
        assert len(scraper.movies_paths) == 1
        assert scraper.movies_paths[0] == Path("/path/to/movies/")
        assert len(scraper.tvshows_paths) == 1
        assert scraper.tvshows_paths[0] == Path("/path/to/tvshows/")
    finally:
        os.unlink(env_file)


def test_env_loading_missing_required_variable():
    """Test that ValueError is raised when required variable is missing."""
    # Create a temporary .env file without TMDB_API_KEY
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        env_file = f.name

    try:
        # Clear environment variable if it exists
        old_value = os.environ.pop("TMDB_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="TMDB_API_KEY"):
                YoutubeTrailerScraper(env_file=env_file)
        finally:
            # Restore old value
            if old_value is not None:
                os.environ["TMDB_API_KEY"] = old_value
    finally:
        os.unlink(env_file)


def test_env_loading_with_defaults():
    """Test that default values are used when optional variables are missing."""
    # Create a temporary .env file with only required variables
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)

        # Check defaults
        assert scraper.tmdb_api_base_url == "https://api.themoviedb.org/3"
        assert scraper.youtube_search_url == "https://www.youtube.com/results?search_query={query}"
        assert scraper.default_search_query_format == "{title} {year} bande annonce"
        assert scraper.smb_mount_point == ""
    finally:
        os.unlink(env_file)


def test_env_loading_invalid_path_list():
    """Test that ValueError is raised for invalid path list format."""
    # Create a temporary .env file with invalid path list
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write("MOVIES_PATHS=not_a_list\n")
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        env_file = f.name

    try:
        with pytest.raises(ValueError, match="Invalid path list format"):
            YoutubeTrailerScraper(env_file=env_file)
    finally:
        os.unlink(env_file)


def test_env_loading_path_list_not_list_type():
    """Test that ValueError is raised when path list evaluates to non-list type."""
    # Create a temporary .env file with a dict instead of list
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS={"path": "/movies/"}\n')  # Dict instead of list
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        env_file = f.name

    try:
        with pytest.raises(ValueError, match="PATHS must be a Python list"):
            YoutubeTrailerScraper(env_file=env_file)
    finally:
        os.unlink(env_file)


def test_env_loading_missing_file():
    """Test that FileNotFoundError is raised when .env file doesn't exist."""
    with pytest.raises(FileNotFoundError, match="Environment file not found"):
        YoutubeTrailerScraper(env_file="nonexistent.env")


def test_smb_mount_with_env_variable():
    """Test that SMB mount point is prepended when USE_SMB_MOUNT=true in env."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/Volumes/Disk1/medias/films/", "/Volumes/Disk2/medias/films/"]\n')
        f.write('TVSHOWS_PATHS=["/Volumes/Disk1/medias/tvshows/"]\n')
        f.write("SMB_MOUNT_POINT=/Volumes/MediaServer\n")
        f.write("USE_SMB_MOUNT=true\n")
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)

        assert scraper.use_smb_mount is True
        assert scraper.smb_mount_point == "/Volumes/MediaServer"
        assert len(scraper.movies_paths) == 2
        # SMB mount point is prepended to paths as Path objects
        assert scraper.movies_paths[0] == Path("/Volumes/MediaServer/Volumes/Disk1/medias/films")
        assert scraper.movies_paths[1] == Path("/Volumes/MediaServer/Volumes/Disk2/medias/films")
        assert scraper.tvshows_paths[0] == Path(
            "/Volumes/MediaServer/Volumes/Disk1/medias/tvshows"
        )
    finally:
        os.unlink(env_file)


def test_smb_mount_with_constructor_flag():
    """Test that SMB mount point is prepended when use_smb=True in constructor."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/Volumes/Disk1/medias/films/"]\n')
        f.write('TVSHOWS_PATHS=["/Volumes/Disk1/medias/tvshows/"]\n')
        f.write("SMB_MOUNT_POINT=/Volumes/MediaServer\n")
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file, use_smb=True)

        assert scraper.use_smb_mount is True
        # SMB mount point is prepended to paths as Path objects
        assert scraper.movies_paths[0] == Path("/Volumes/MediaServer/Volumes/Disk1/medias/films")
        assert scraper.tvshows_paths[0] == Path(
            "/Volumes/MediaServer/Volumes/Disk1/medias/tvshows"
        )
    finally:
        os.unlink(env_file)


def test_smb_mount_disabled():
    """Test that SMB mount point is NOT prepended when USE_SMB_MOUNT=false."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/Volumes/Disk1/medias/films/"]\n')
        f.write('TVSHOWS_PATHS=["/Volumes/Disk1/medias/tvshows/"]\n')
        f.write("SMB_MOUNT_POINT=/Volumes/MediaServer\n")
        f.write("USE_SMB_MOUNT=false\n")
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)

        assert scraper.use_smb_mount is False
        # Paths are not prefixed when SMB mount is disabled
        assert scraper.movies_paths[0] == Path("/Volumes/Disk1/medias/films/")
        assert scraper.tvshows_paths[0] == Path("/Volumes/Disk1/medias/tvshows/")
    finally:
        os.unlink(env_file)


def test_smb_mount_env_overrides_constructor():
    """Test that USE_SMB_MOUNT env variable overrides constructor parameter."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/Volumes/Disk1/medias/films/"]\n')
        f.write('TVSHOWS_PATHS=["/Volumes/Disk1/medias/tvshows/"]\n')
        f.write("SMB_MOUNT_POINT=/Volumes/MediaServer\n")
        f.write("USE_SMB_MOUNT=true\n")
        env_file = f.name

    try:
        # Pass use_smb=False, but env has USE_SMB_MOUNT=true
        scraper = YoutubeTrailerScraper(env_file=env_file, use_smb=False)

        # Environment variable should override constructor parameter
        assert scraper.use_smb_mount is True
        # SMB mount point is prepended to paths as Path objects
        assert scraper.movies_paths[0] == Path("/Volumes/MediaServer/Volumes/Disk1/medias/films")
    finally:
        os.unlink(env_file)


def test_scan_sample_size_valid():
    """Test that SCAN_SAMPLE_SIZE is loaded correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        f.write("SCAN_SAMPLE_SIZE=100\n")
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        assert scraper.scan_sample_size == 100
    finally:
        os.unlink(env_file)


def test_scan_sample_size_invalid():
    """Test that invalid SCAN_SAMPLE_SIZE is ignored."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        f.write("SCAN_SAMPLE_SIZE=not_a_number\n")
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        assert scraper.scan_sample_size is None
    finally:
        os.unlink(env_file)


def test_scan_for_movies_without_trailers_empty_paths():
    """Test scan_for_movies_without_trailers with empty movies_paths."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write("MOVIES_PATHS=[]\n")
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
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
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        # Just verify the method can be called without errors
        scraper.clear_cache()
    finally:
        os.unlink(env_file)


def test_search_for_movie_trailer():
    """Test the search_for_movie_trailer method."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        # Test the method returns empty list (TODO stub implementation)
        result = scraper.search_for_movie_trailer("Test Movie", 2020)
        assert not result
    finally:
        os.unlink(env_file)
