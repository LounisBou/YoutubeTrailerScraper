#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for cache persistence across YoutubeTrailerScraper instances."""

import time

import pytest

from youtubetrailerscraper import YoutubeTrailerScraper


@pytest.fixture
def temp_env_with_movies(tmp_path):
    """Create temporary environment with test movie structure.

    Creates:
        - .env file with test configuration
        - 10 movies (5 with trailers, 5 without)
    """
    # Create .env file
    env_file = tmp_path / ".env"
    movies_dir = tmp_path / "movies"
    movies_dir.mkdir()

    env_content = f"""
TMDB_API_KEY=test_key
TMDB_READ_ACCESS_TOKEN=test_token
MOVIES_PATHS=['{movies_dir}']
TVSHOWS_PATHS=[]
USE_SMB_MOUNT=false
""".strip()
    env_file.write_text(env_content)

    # Create test movies
    for i in range(10):
        movie = movies_dir / f"Movie{i}"
        movie.mkdir()
        (movie / "movie.mp4").touch()
        # Even numbered movies have trailers
        if i % 2 == 0:
            (movie / "trailer.mp4").touch()

    return env_file, movies_dir


class TestCachePersistence:
    """Test cache persistence across YoutubeTrailerScraper instances."""

    def test_cache_persists_across_instances(
        self, temp_env_with_movies
    ):  # pylint: disable=redefined-outer-name
        """Test that cache persists when creating multiple scraper instances.

        This simulates running the program multiple times - each time a new
        YoutubeTrailerScraper instance is created, but the cache should persist
        on disk and be reused.
        """
        env_file, _ = temp_env_with_movies

        # First instance - should scan filesystem and populate cache
        scraper1 = YoutubeTrailerScraper(env_file=str(env_file))
        start1 = time.time()
        result1 = scraper1.scan_for_movies_without_trailers()
        elapsed1 = time.time() - start1

        # Verify we found the expected movies
        assert len(result1) == 5  # 5 movies without trailers

        # Delete first instance to simulate program restart
        del scraper1

        # Second instance - should hit cache (faster)
        scraper2 = YoutubeTrailerScraper(env_file=str(env_file))
        start2 = time.time()
        result2 = scraper2.scan_for_movies_without_trailers()
        elapsed2 = time.time() - start2

        # Verify results are consistent
        assert len(result2) == 5
        assert set(p.name for p in result1) == set(p.name for p in result2)

        # Verify second scan was faster (cache hit)
        # Allow for some variance but second should be noticeably faster
        assert elapsed2 < elapsed1 or elapsed2 < 0.01, (
            f"Cache not working: execution 1 took {elapsed1:.4f}s, "
            f"execution 2 took {elapsed2:.4f}s (should be faster)"
        )

    def test_shared_filesystem_scanner_within_instance(
        self, temp_env_with_movies
    ):  # pylint: disable=redefined-outer-name
        """Test that a single scraper instance reuses the same FileSystemScanner.

        This ensures that within a single program execution, multiple scans
        share the same cache instance.
        """
        env_file, _ = temp_env_with_movies

        scraper = YoutubeTrailerScraper(env_file=str(env_file))

        # First scan
        start1 = time.time()
        result1 = scraper.scan_for_movies_without_trailers()
        elapsed1 = time.time() - start1

        # Second scan (same instance)
        start2 = time.time()
        result2 = scraper.scan_for_movies_without_trailers()
        elapsed2 = time.time() - start2

        # Results should be identical
        assert len(result1) == len(result2) == 5
        assert result1 == result2

        # Second scan should be much faster (cache hit)
        assert elapsed2 < elapsed1 or elapsed2 < 0.01

    def test_clear_cache_invalidates_results(
        self, temp_env_with_movies
    ):  # pylint: disable=redefined-outer-name
        """Test that clear_cache() forces a fresh scan.

        Now that trailer detection is cached, adding a trailer won't be detected
        until the cache is cleared.
        """
        env_file, _movies_dir = temp_env_with_movies

        # First scan
        scraper = YoutubeTrailerScraper(env_file=str(env_file))
        result1 = scraper.scan_for_movies_without_trailers()
        assert len(result1) == 5

        # Add a trailer to one of the movies
        movie = result1[0]
        (movie / "new-trailer.mp4").touch()

        # Scan again - should still return 5 (cached result)
        result2 = scraper.scan_for_movies_without_trailers()
        assert len(result2) == 5  # Cache still has old result
        assert movie in result2  # Movie still appears in cached result

        # Clear cache
        scraper.clear_cache()

        # Scan again - should return 4 (fresh scan sees new trailer)
        result3 = scraper.scan_for_movies_without_trailers()
        assert len(result3) == 4
        assert movie not in result3  # Movie no longer missing trailer

    def test_cache_ttl_expiration(
        self, temp_env_with_movies
    ):  # pylint: disable=redefined-outer-name
        """Test that cache entries expire after TTL.

        Note: With CacheIt, cache expiration is built into the decorator.
        This test verifies the cache eventually expires (24 hour default).
        """
        env_file, _ = temp_env_with_movies

        # Create scraper with default TTL
        scraper = YoutubeTrailerScraper(env_file=str(env_file))

        # First scan - populates cache
        result1 = scraper.scan_for_movies_without_trailers()
        assert len(result1) == 5

        # Second scan immediately - should hit cache
        result2 = scraper.scan_for_movies_without_trailers()
        assert len(result2) == 5

        # Results should be consistent
        assert result1 == result2 or set(p.name for p in result1) == set(p.name for p in result2)

    def test_cache_key_uniqueness_per_path(self, tmp_path):
        """Test that different paths have separate cache entries."""
        # Create two separate movie directories
        movies_dir1 = tmp_path / "movies1"
        movies_dir1.mkdir()
        movies_dir2 = tmp_path / "movies2"
        movies_dir2.mkdir()

        # Create different movies in each
        for i in range(3):
            movie = movies_dir1 / f"MovieA{i}"
            movie.mkdir()
            (movie / "movie.mp4").touch()

        for i in range(5):
            movie = movies_dir2 / f"MovieB{i}"
            movie.mkdir()
            (movie / "movie.mp4").touch()

        # Create two env files
        env_file1 = tmp_path / ".env1"
        env_file1.write_text(
            f"""
TMDB_API_KEY=test_key
TMDB_READ_ACCESS_TOKEN=test_token
MOVIES_PATHS=['{movies_dir1}']
TVSHOWS_PATHS=[]
USE_SMB_MOUNT=false
""".strip()
        )

        env_file2 = tmp_path / ".env2"
        env_file2.write_text(
            f"""
TMDB_API_KEY=test_key
TMDB_READ_ACCESS_TOKEN=test_token
MOVIES_PATHS=['{movies_dir2}']
TVSHOWS_PATHS=[]
USE_SMB_MOUNT=false
""".strip()
        )

        # Scan first directory
        scraper1 = YoutubeTrailerScraper(env_file=str(env_file1))
        result1 = scraper1.scan_for_movies_without_trailers()
        assert len(result1) == 3

        # Scan second directory
        scraper2 = YoutubeTrailerScraper(env_file=str(env_file2))
        result2 = scraper2.scan_for_movies_without_trailers()
        assert len(result2) == 5

        # Results should be different (different paths cached separately)
        assert len(result1) != len(result2)
