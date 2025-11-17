#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for fix_trailer_extensions.py utility script."""

import sys
from pathlib import Path

# Import the utility functions
sys.path.insert(0, str(Path(__file__).parent.parent))
# pylint: disable=wrong-import-position,import-error
from fix_trailer_extensions import (
    find_trailers_without_extension,
    is_movie_directory,
    scan_directories,
    setup_logging,
)


class TestIsMovieDirectory:
    """Tests for is_movie_directory function."""

    def test_directory_with_video_files(self, tmp_path):
        """Test that directory with video files is recognized."""
        (tmp_path / "movie.mp4").touch()
        assert is_movie_directory(tmp_path) is True

    def test_directory_with_mkv_files(self, tmp_path):
        """Test that directory with MKV files is recognized."""
        (tmp_path / "movie.mkv").touch()
        assert is_movie_directory(tmp_path) is True

    def test_directory_without_video_files(self, tmp_path):
        """Test that directory without video files is not recognized."""
        (tmp_path / "readme.txt").touch()
        assert is_movie_directory(tmp_path) is False

    def test_empty_directory(self, tmp_path):
        """Test that empty directory is not recognized."""
        assert is_movie_directory(tmp_path) is False


class TestFindTrailersWithoutExtension:
    """Tests for find_trailers_without_extension function."""

    def test_finds_trailer_without_extension(self, tmp_path):
        """Test that trailers without .mp4 extension are found."""
        (tmp_path / "Movie (2020).mp4").touch()
        trailer = tmp_path / "Movie (2020) - trailer #1 -trailer"
        trailer.touch()

        result = find_trailers_without_extension(tmp_path)
        assert len(result) == 1
        assert result[0] == trailer

    def test_ignores_trailer_with_mp4_extension(self, tmp_path):
        """Test that trailers with .mp4 extension are ignored."""
        (tmp_path / "Movie (2020).mp4").touch()
        (tmp_path / "Movie (2020) - trailer #1 -trailer.mp4").touch()

        result = find_trailers_without_extension(tmp_path)
        assert len(result) == 0

    def test_finds_multiple_trailers_without_extension(self, tmp_path):
        """Test that multiple trailers without extension are found."""
        (tmp_path / "Movie (2020).mp4").touch()
        (tmp_path / "Movie (2020) - trailer #1 -trailer").touch()
        (tmp_path / "Movie (2020) - trailer #2 -trailer").touch()
        (tmp_path / "Movie (2020) - trailer #3 -trailer.mp4").touch()  # This one has .mp4

        result = find_trailers_without_extension(tmp_path)
        assert len(result) == 2

    def test_case_insensitive_trailer_detection(self, tmp_path):
        """Test that trailer detection is case-insensitive."""
        (tmp_path / "Movie (2020).mp4").touch()
        (tmp_path / "Movie (2020) - TRAILER #1").touch()
        (tmp_path / "Movie (2020) - Trailer #2").touch()

        result = find_trailers_without_extension(tmp_path)
        assert len(result) == 2

    def test_ignores_non_trailer_files(self, tmp_path):
        """Test that non-trailer files are ignored."""
        (tmp_path / "Movie (2020).mp4").touch()
        (tmp_path / "Movie (2020).srt").touch()
        (tmp_path / "poster.jpg").touch()

        result = find_trailers_without_extension(tmp_path)
        assert len(result) == 0

    def test_ignores_directories(self, tmp_path):
        """Test that directories are ignored."""
        (tmp_path / "Movie (2020).mp4").touch()
        (tmp_path / "trailer").mkdir()

        result = find_trailers_without_extension(tmp_path)
        assert len(result) == 0


class TestScanDirectories:
    """Tests for scan_directories function."""

    def test_scans_single_movie_directory(self, tmp_path):
        """Test scanning a single movie directory."""
        movie_dir = tmp_path / "Movie (2020)"
        movie_dir.mkdir()
        (movie_dir / "Movie (2020).mp4").touch()
        (movie_dir / "Movie (2020) - trailer #1 -trailer").touch()

        logger = setup_logging(verbose=False)
        result = scan_directories([tmp_path], logger)

        assert len(result) == 1
        old_path, new_path = result[0]
        assert old_path.name == "Movie (2020) - trailer #1 -trailer"
        assert new_path.name == "Movie (2020) - trailer #1 -trailer.mp4"

    def test_scans_multiple_movie_directories(self, tmp_path):
        """Test scanning multiple movie directories."""
        # Create first movie directory
        movie1 = tmp_path / "Movie1 (2020)"
        movie1.mkdir()
        (movie1 / "Movie1 (2020).mp4").touch()
        (movie1 / "Movie1 (2020) - trailer").touch()

        # Create second movie directory
        movie2 = tmp_path / "Movie2 (2021)"
        movie2.mkdir()
        (movie2 / "Movie2 (2021).mkv").touch()
        (movie2 / "Movie2 (2021) - trailer").touch()

        logger = setup_logging(verbose=False)
        result = scan_directories([tmp_path], logger)

        assert len(result) == 2

    def test_skips_non_movie_directories(self, tmp_path):
        """Test that non-movie directories are skipped."""
        # Create directory without video files
        non_movie_dir = tmp_path / "Not a Movie"
        non_movie_dir.mkdir()
        (non_movie_dir / "readme.txt").touch()
        (non_movie_dir / "trailer").touch()

        logger = setup_logging(verbose=False)
        result = scan_directories([tmp_path], logger)

        assert len(result) == 0

    def test_handles_nonexistent_path(self, tmp_path):
        """Test that nonexistent paths are handled gracefully."""
        nonexistent = tmp_path / "does_not_exist"

        logger = setup_logging(verbose=False)
        result = scan_directories([nonexistent], logger)

        assert len(result) == 0

    def test_handles_file_as_path(self, tmp_path):
        """Test that files passed as paths are handled gracefully."""
        file_path = tmp_path / "file.txt"
        file_path.touch()

        logger = setup_logging(verbose=False)
        result = scan_directories([file_path], logger)

        assert len(result) == 0


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test that logging can be set up with default settings."""
        logger = setup_logging(verbose=False)
        assert logger.level == 20  # INFO level

    def test_setup_logging_verbose(self):
        """Test that logging can be set up with verbose settings."""
        logger = setup_logging(verbose=True)
        assert logger.level == 10  # DEBUG level
