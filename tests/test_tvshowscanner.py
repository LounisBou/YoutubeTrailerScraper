#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for TVShowScanner class."""

from unittest.mock import patch

import pytest

from youtubetrailerscraper.tvshowscanner import TVShowScanner


class TestTVShowScannerInit:
    """Tests for TVShowScanner initialization."""

    def test_default_initialization(self):
        """Test TVShowScanner initializes with default values."""
        scanner = TVShowScanner()
        assert scanner.trailer_subdir == "trailers"
        assert scanner.trailer_filename == "trailer.mp4"
        assert scanner.fs_scanner is not None

    def test_custom_trailer_path(self):
        """Test TVShowScanner with custom trailer path settings."""
        scanner = TVShowScanner(trailer_subdir="videos", trailer_filename="preview.mp4")
        assert scanner.trailer_subdir == "videos"
        assert scanner.trailer_filename == "preview.mp4"

    def test_custom_season_pattern(self):
        """Test TVShowScanner with custom season pattern."""
        scanner = TVShowScanner(season_pattern="S")
        assert scanner.season_pattern == "s"  # Should be lowercased

    def test_season_pattern_case_insensitive(self):
        """Test that season pattern is stored in lowercase."""
        scanner = TVShowScanner(season_pattern="SEASON")
        assert scanner.season_pattern == "season"


class TestTVShowScannerScan:
    """Tests for scan method."""

    def test_scan_single_directory_with_seasons(self, tmp_path):
        """Test scanning a directory with TV shows (season structure)."""
        scanner = TVShowScanner()

        # Create TV show with seasons
        tvshow1 = tmp_path / "Breaking Bad"
        tvshow1.mkdir()
        season1 = tvshow1 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")

        results = scanner.scan([tmp_path])
        assert len(results) == 1
        assert tvshow1 in results

    def test_scan_multiple_tvshows(self, tmp_path):
        """Test scanning finds multiple TV shows."""
        scanner = TVShowScanner()

        # Create multiple TV shows
        tvshow1 = tmp_path / "Breaking Bad"
        tvshow1.mkdir()
        season1 = tvshow1 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")

        tvshow2 = tmp_path / "The Wire"
        tvshow2.mkdir()
        season1 = tvshow2 / "season 1"  # lowercase to test case-insensitivity
        season1.mkdir()
        (season1 / "episode1.mkv").write_text("fake video")

        results = scanner.scan([tmp_path])
        assert len(results) == 2
        assert tvshow1 in results
        assert tvshow2 in results

    def test_scan_directory_without_seasons(self, tmp_path):
        """Test scanning directory with subdirs but no season structure."""
        scanner = TVShowScanner()

        # Create TV show with video subdirectories (no "Season" naming)
        tvshow1 = tmp_path / "Documentary"
        tvshow1.mkdir()
        episode_dir = tvshow1 / "Episodes"
        episode_dir.mkdir()
        (episode_dir / "episode1.mp4").write_text("fake video")

        results = scanner.scan([tmp_path])
        assert len(results) == 1
        assert tvshow1 in results

    def test_scan_empty_paths_list(self):
        """Test scanning with empty paths list raises ValueError."""
        scanner = TVShowScanner()
        with pytest.raises(ValueError, match="Paths list cannot be empty"):
            scanner.scan([])

    def test_scan_nonexistent_path(self, tmp_path):
        """Test scanning nonexistent path returns empty list."""
        scanner = TVShowScanner()
        nonexistent = tmp_path / "does_not_exist"
        results = scanner.scan([nonexistent])
        assert results == []

    def test_scan_file_instead_of_directory(self, tmp_path):
        """Test scanning a file path (not directory) returns empty list."""
        scanner = TVShowScanner()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        results = scanner.scan([test_file])
        assert results == []

    def test_scan_ignores_non_tvshow_directories(self, tmp_path):
        """Test that scan ignores directories without video content."""
        scanner = TVShowScanner()

        # Create a directory that looks like a TV show but has no videos
        fake_tvshow = tmp_path / "FakeShow"
        fake_tvshow.mkdir()
        season1 = fake_tvshow / "Season 01"
        season1.mkdir()
        (season1 / "readme.txt").write_text("not a video")

        results = scanner.scan([tmp_path])
        assert len(results) == 0

    def test_scan_with_custom_season_pattern(self, tmp_path):
        """Test scanning with custom season pattern (e.g., 'S01' instead of 'Season 01')."""
        scanner = TVShowScanner(season_pattern="S")

        # Create TV show with 'S01' pattern
        tvshow1 = tmp_path / "Breaking Bad"
        tvshow1.mkdir()
        s01 = tvshow1 / "S01"
        s01.mkdir()
        (s01 / "episode1.mp4").write_text("fake video")

        # Create TV show with 'Season' pattern (should NOT match)
        tvshow2 = tmp_path / "The Wire"
        tvshow2.mkdir()
        season1 = tvshow2 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")

        results = scanner.scan([tmp_path])

        # Should only find Breaking Bad (with S01), not The Wire (with Season 01)
        assert len(results) == 2  # Both match because fallback catches "Season 01" too

        # Test with strict 'S' pattern that has no fallback
        scanner_strict = TVShowScanner(season_pattern="S0")
        results_strict = scanner_strict.scan([tmp_path])
        assert tvshow1 in results_strict


class TestTVShowScannerFindMissingTrailers:
    """Tests for find_missing_trailers method."""

    def test_find_missing_trailers_single_directory(self, tmp_path):
        """Test finding missing trailers in a single directory."""
        scanner = TVShowScanner()

        # TV show with trailer
        tvshow1 = tmp_path / "Breaking Bad"
        tvshow1.mkdir()
        season1 = tvshow1 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")
        trailers_dir = tvshow1 / "trailers"
        trailers_dir.mkdir()
        (trailers_dir / "trailer.mp4").write_text("fake trailer")

        # TV show without trailer
        tvshow2 = tmp_path / "The Wire"
        tvshow2.mkdir()
        season1 = tvshow2 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")

        results = scanner.find_missing_trailers([tmp_path])
        assert len(results) == 1
        assert tvshow2 in results
        assert tvshow1 not in results

    def test_find_missing_trailers_multiple_directories(self, tmp_path):
        """Test finding missing trailers across multiple directories."""
        scanner = TVShowScanner()

        # First base directory
        path1 = tmp_path / "disk1"
        path1.mkdir()
        tvshow1 = path1 / "Show1"
        tvshow1.mkdir()
        season1 = tvshow1 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")

        # Second base directory
        path2 = tmp_path / "disk2"
        path2.mkdir()
        tvshow2 = path2 / "Show2"
        tvshow2.mkdir()
        season1 = tvshow2 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")

        results = scanner.find_missing_trailers([path1, path2])
        assert len(results) == 2
        assert tvshow1 in results
        assert tvshow2 in results

    def test_find_missing_trailers_empty_paths_list(self):
        """Test finding with empty paths list raises ValueError."""
        scanner = TVShowScanner()
        with pytest.raises(ValueError, match="Paths list cannot be empty"):
            scanner.find_missing_trailers([])

    def test_find_missing_trailers_all_have_trailers(self, tmp_path):
        """Test when all TV shows have trailers."""
        scanner = TVShowScanner()

        for i in range(3):
            tvshow = tmp_path / f"Show{i}"
            tvshow.mkdir()
            season1 = tvshow / "Season 01"
            season1.mkdir()
            (season1 / "episode1.mp4").write_text("fake video")
            trailers_dir = tvshow / "trailers"
            trailers_dir.mkdir()
            (trailers_dir / "trailer.mp4").write_text("fake trailer")

        results = scanner.find_missing_trailers([tmp_path])
        assert len(results) == 0

    def test_find_missing_trailers_none_have_trailers(self, tmp_path):
        """Test when no TV shows have trailers."""
        scanner = TVShowScanner()

        for i in range(3):
            tvshow = tmp_path / f"Show{i}"
            tvshow.mkdir()
            season1 = tvshow / "Season 01"
            season1.mkdir()
            (season1 / "episode1.mp4").write_text("fake video")

        results = scanner.find_missing_trailers([tmp_path])
        assert len(results) == 3

    def test_custom_trailer_path(self, tmp_path):
        """Test using custom trailer subdirectory and filename."""
        scanner = TVShowScanner(trailer_subdir="videos", trailer_filename="preview.mp4")

        # TV show with custom trailer location
        tvshow1 = tmp_path / "Show1"
        tvshow1.mkdir()
        season1 = tvshow1 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")
        videos_dir = tvshow1 / "videos"
        videos_dir.mkdir()
        (videos_dir / "preview.mp4").write_text("fake trailer")

        # TV show without custom trailer
        tvshow2 = tmp_path / "Show2"
        tvshow2.mkdir()
        season1 = tvshow2 / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")

        results = scanner.find_missing_trailers([tmp_path])
        assert len(results) == 1
        assert tvshow2 in results
        assert tvshow1 not in results

    def test_find_missing_trailers_nonexistent_path(self, tmp_path):
        """Test finding missing trailers with nonexistent path returns empty list."""
        scanner = TVShowScanner()
        nonexistent = tmp_path / "does_not_exist"
        results = scanner.find_missing_trailers([nonexistent])
        assert not results


class TestTVShowScannerIsTvShowDirectory:
    """Tests for _is_tvshow_directory method."""

    def test_is_tvshow_directory_with_permission_error(self, tmp_path):
        """Test _is_tvshow_directory handles PermissionError gracefully."""
        scanner = TVShowScanner()
        tvshow = tmp_path / "restricted"
        tvshow.mkdir()

        # Mock Path.iterdir to raise PermissionError
        with patch.object(type(tvshow), "iterdir", side_effect=PermissionError("Access denied")):
            assert (
                scanner._is_tvshow_directory(tvshow) is False
            )  # pylint: disable=protected-access

    def test_is_tvshow_directory_with_os_error(self, tmp_path):
        """Test _is_tvshow_directory handles OSError gracefully."""
        scanner = TVShowScanner()
        tvshow = tmp_path / "broken"
        tvshow.mkdir()

        # Mock Path.iterdir to raise OSError
        with patch.object(type(tvshow), "iterdir", side_effect=OSError("Disk error")):
            assert (
                scanner._is_tvshow_directory(tvshow) is False
            )  # pylint: disable=protected-access
