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
        f.write("USE_SMB_MOUNT=false\n")  # Explicitly disable SMB mount
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
        f.write("USE_SMB_MOUNT=false\n")  # Explicitly disable SMB mount
        f.write("SMB_MOUNT_POINT=\n")  # Explicitly set empty SMB mount point
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


def test_env_loading_string_list_syntax_error():
    """Test that ValueError is raised when string list has syntax error."""
    # Create a temporary .env file with invalid Python syntax
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        f.write("TMDB_LANGUAGES=['en-US',]\n")  # Trailing comma is OK, but use malformed one
        f.write = lambda _: None  # This won't work, but let's try unbalanced brackets
        env_file = f.name

    try:
        # Actually write invalid syntax manually
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("TMDB_API_KEY=test_api_key\n")
            f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
            f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
            f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
            f.write("TMDB_LANGUAGES=['en-US'\n")  # Unbalanced brackets - syntax error

        with pytest.raises(ValueError, match="Invalid list format"):
            YoutubeTrailerScraper(env_file=env_file)
    finally:
        os.unlink(env_file)


def test_env_loading_string_list_not_list():
    """Test that ValueError is raised when string list is not a list type."""
    # Create a temporary .env file with a number instead of list for TMDB_LANGUAGES
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("TMDB_API_KEY=test_api_key\n")
        f.write("TMDB_READ_ACCESS_TOKEN=test_token\n")
        f.write('MOVIES_PATHS=["/path/to/movies/"]\n')
        f.write('TVSHOWS_PATHS=["/path/to/tvshows/"]\n')
        f.write("TMDB_LANGUAGES=123\n")  # Number instead of list
        env_file = f.name

    try:
        with pytest.raises(ValueError, match="Value must be a Python list"):
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
        f.write('TMDB_LANGUAGES=["en-US"]\n')
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
        f.write('TMDB_LANGUAGES=["en-US"]\n')
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
        f.write('TMDB_LANGUAGES=["en-US"]\n')
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
        f.write('TMDB_LANGUAGES=["en-US"]\n')
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
        f.write('TMDB_LANGUAGES=["en-US"]\n')
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
        f.write('TMDB_LANGUAGES=["en-US"]\n')
        f.write("SCAN_SAMPLE_SIZE=not_a_number\n")
        env_file = f.name

    try:
        scraper = YoutubeTrailerScraper(env_file=env_file)
        assert scraper.scan_sample_size is None
    finally:
        os.unlink(env_file)
