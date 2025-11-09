#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for FileSystemScanner class."""

import pytest

from youtubetrailerscraper.filesystemscanner import FileSystemScanner


class TestFileSystemScannerInit:
    """Tests for FileSystemScanner initialization."""

    def test_default_initialization(self):
        """Test FileSystemScanner initializes with default values."""
        scanner = FileSystemScanner()
        assert scanner.video_extensions == {".mp4", ".mkv", ".avi", ".m4v", ".mov"}
        assert scanner.cache_ttl == 86400  # 24 hours
        assert scanner.cache_maxsize == 100

    def test_custom_video_extensions(self):
        """Test FileSystemScanner with custom video extensions."""
        custom_exts = {".mp4", ".webm"}
        scanner = FileSystemScanner(video_extensions=custom_exts)
        assert scanner.video_extensions == custom_exts

    def test_custom_cache_settings(self):
        """Test FileSystemScanner with custom cache settings."""
        scanner = FileSystemScanner(cache_ttl=3600, cache_maxsize=50)
        assert scanner.cache_ttl == 3600
        assert scanner.cache_maxsize == 50


class TestFileSystemScannerValidatePath:
    """Tests for validate_path method."""

    def test_validate_existing_directory(self, tmp_path):
        """Test validation of existing directory."""
        scanner = FileSystemScanner()
        assert scanner.validate_path(tmp_path) is True

    def test_validate_nonexistent_path(self, tmp_path):
        """Test validation fails for nonexistent path."""
        scanner = FileSystemScanner()
        nonexistent = tmp_path / "does_not_exist"
        assert scanner.validate_path(nonexistent) is False

    def test_validate_file_instead_of_directory(self, tmp_path):
        """Test validation fails for file path."""
        scanner = FileSystemScanner()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        assert scanner.validate_path(test_file) is False


class TestFileSystemScannerHasVideoFiles:
    """Tests for has_video_files method."""

    def test_directory_with_video_files(self, tmp_path):
        """Test detection of directory with video files."""
        scanner = FileSystemScanner()
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        (video_dir / "movie.mp4").write_text("fake video")
        assert scanner.has_video_files(video_dir) is True

    def test_directory_without_video_files(self, tmp_path):
        """Test directory without video files returns False."""
        scanner = FileSystemScanner()
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        (empty_dir / "readme.txt").write_text("not a video")
        assert scanner.has_video_files(empty_dir) is False

    def test_empty_directory(self, tmp_path):
        """Test empty directory returns False."""
        scanner = FileSystemScanner()
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert scanner.has_video_files(empty_dir) is False

    def test_various_video_extensions(self, tmp_path):
        """Test recognition of various video file extensions."""
        scanner = FileSystemScanner()
        for ext in [".mp4", ".mkv", ".avi", ".m4v", ".mov"]:
            video_dir = tmp_path / f"videos{ext}"
            video_dir.mkdir()
            (video_dir / f"movie{ext}").write_text("fake video")
            assert scanner.has_video_files(video_dir) is True


class TestFileSystemScannerHasSubdirectoriesWithVideos:
    """Tests for has_subdirectories_with_videos method."""

    def test_directory_with_video_subdirectories(self, tmp_path):
        """Test detection of directory with subdirectories containing videos."""
        scanner = FileSystemScanner()
        parent = tmp_path / "tvshow"
        parent.mkdir()
        season1 = parent / "Season 01"
        season1.mkdir()
        (season1 / "episode1.mp4").write_text("fake video")
        assert scanner.has_subdirectories_with_videos(parent) is True

    def test_directory_without_video_subdirectories(self, tmp_path):
        """Test directory without video subdirectories returns False."""
        scanner = FileSystemScanner()
        parent = tmp_path / "tvshow"
        parent.mkdir()
        season1 = parent / "Season 01"
        season1.mkdir()
        (season1 / "readme.txt").write_text("not a video")
        assert scanner.has_subdirectories_with_videos(parent) is False

    def test_directory_with_no_subdirectories(self, tmp_path):
        """Test directory with no subdirectories returns False."""
        scanner = FileSystemScanner()
        parent = tmp_path / "empty"
        parent.mkdir()
        assert scanner.has_subdirectories_with_videos(parent) is False


class TestFileSystemScannerScanDirectories:
    """Tests for scan_directories method."""

    def test_scan_with_simple_filter(self, tmp_path):
        """Test scanning directories with a simple filter function."""
        scanner = FileSystemScanner()

        # Create test structure
        movie1 = tmp_path / "Movie1"
        movie1.mkdir()
        (movie1 / "movie.mp4").write_text("fake video")

        movie2 = tmp_path / "Movie2"
        movie2.mkdir()
        (movie2 / "movie.mkv").write_text("fake video")

        not_movie = tmp_path / "NotMovie"
        not_movie.mkdir()
        (not_movie / "readme.txt").write_text("text")

        # Scan using has_video_files filter
        results = scanner.scan_directories(
            [tmp_path], filter_func=scanner.has_video_files, filter_name="test"
        )

        assert len(results) == 2
        assert movie1 in results
        assert movie2 in results
        assert not_movie not in results

    def test_scan_multiple_paths(self, tmp_path):
        """Test scanning multiple base paths."""
        scanner = FileSystemScanner()

        path1 = tmp_path / "disk1"
        path1.mkdir()
        movie1 = path1 / "Movie1"
        movie1.mkdir()
        (movie1 / "movie.mp4").write_text("fake video")

        path2 = tmp_path / "disk2"
        path2.mkdir()
        movie2 = path2 / "Movie2"
        movie2.mkdir()
        (movie2 / "movie.mkv").write_text("fake video")

        results = scanner.scan_directories(
            [path1, path2], filter_func=scanner.has_video_files, filter_name="test"
        )

        assert len(results) == 2
        assert movie1 in results
        assert movie2 in results

    def test_scan_empty_paths_list(self):
        """Test scanning with empty paths list raises ValueError."""
        scanner = FileSystemScanner()
        with pytest.raises(ValueError, match="Paths list cannot be empty"):
            scanner.scan_directories([], filter_func=lambda x: True, filter_name="test")

    def test_scan_nonexistent_path(self, tmp_path):
        """Test scanning nonexistent path returns empty list."""
        scanner = FileSystemScanner()
        nonexistent = tmp_path / "does_not_exist"
        results = scanner.scan_directories(
            [nonexistent], filter_func=scanner.has_video_files, filter_name="test"
        )
        assert results == []

    def test_scan_uses_cache(self, tmp_path):
        """Test that scan results are cached."""
        scanner = FileSystemScanner()

        movie1 = tmp_path / "Movie1"
        movie1.mkdir()
        (movie1 / "movie.mp4").write_text("fake video")

        # First scan
        results1 = scanner.scan_directories(
            [tmp_path], filter_func=scanner.has_video_files, filter_name="cache_test"
        )

        # Add a new movie after first scan
        movie2 = tmp_path / "Movie2"
        movie2.mkdir()
        (movie2 / "movie.mkv").write_text("fake video")

        # Second scan should return cached results (not including movie2)
        results2 = scanner.scan_directories(
            [tmp_path], filter_func=scanner.has_video_files, filter_name="cache_test"
        )

        assert results1 == results2
        assert len(results2) == 1  # Only movie1, not movie2


class TestFileSystemScannerClearCache:  # pylint: disable=too-few-public-methods
    """Tests for clear_cache method."""

    def test_clear_cache_invalidates_results(self, tmp_path):
        """Test that clearing cache forces fresh scan."""
        scanner = FileSystemScanner()

        movie1 = tmp_path / "Movie1"
        movie1.mkdir()
        (movie1 / "movie.mp4").write_text("fake video")

        # First scan
        results1 = scanner.scan_directories(
            [tmp_path], filter_func=scanner.has_video_files, filter_name="clear_test"
        )
        assert len(results1) == 1

        # Add a new movie
        movie2 = tmp_path / "Movie2"
        movie2.mkdir()
        (movie2 / "movie.mkv").write_text("fake video")

        # Clear cache
        scanner.clear_cache()

        # New scan should pick up movie2
        results2 = scanner.scan_directories(
            [tmp_path], filter_func=scanner.has_video_files, filter_name="clear_test"
        )
        assert len(results2) == 2
        assert movie1 in results2
        assert movie2 in results2
