#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for MovieScanner class."""

from pathlib import Path  # pylint: disable=unused-import
from unittest.mock import patch

import pytest

from youtubetrailerscraper.moviescanner import MovieScanner  # pylint: disable=import-error


@pytest.fixture
def temp_movie_structure(tmp_path):
    """Create a temporary movie directory structure for testing.

    Structure:
        movies/
            Movie With Trailer (2020)/
                Movie With Trailer (2020).mp4
                Movie With Trailer (2020)-trailer.mp4
            Movie Missing Preview (2021)/
                Movie Missing Preview (2021).mp4
            Movie With Multiple Videos (2022)/
                Movie With Multiple Videos (2022).mkv
                Movie With Multiple Videos (2022)-deleted.mp4
            Empty Directory/
            just_a_file.txt
    """
    movies_dir = tmp_path / "movies"
    movies_dir.mkdir()

    # Movie with trailer
    movie1 = movies_dir / "Movie With Trailer (2020)"
    movie1.mkdir()
    (movie1 / "Movie With Trailer (2020).mp4").touch()
    (movie1 / "Movie With Trailer (2020)-trailer.mp4").touch()

    # Movie without trailer
    movie2 = movies_dir / "Movie Missing Preview (2021)"
    movie2.mkdir()
    (movie2 / "Movie Missing Preview (2021).mp4").touch()

    # Movie with multiple video files
    movie3 = movies_dir / "Movie With Multiple Videos (2022)"
    movie3.mkdir()
    (movie3 / "Movie With Multiple Videos (2022).mkv").touch()
    (movie3 / "Movie With Multiple Videos (2022)-deleted.mp4").touch()

    # Empty directory (should be ignored)
    empty = movies_dir / "Empty Directory"
    empty.mkdir()

    # File in root (should be ignored)
    (movies_dir / "just_a_file.txt").touch()

    return movies_dir


@pytest.fixture
def multi_disk_structure(tmp_path):
    """Create a multi-disk movie structure for testing.

    Structure:
        disk1/
            Movie A (2020)/
                Movie A (2020).mp4
                Movie A (2020)-trailer.mp4
            Movie B (2021)/
                Movie B (2021).mp4
        disk2/
            Movie C (2022)/
                Movie C (2022).avi
            Movie D (2023)/
                Movie D (2023).m4v
                Movie D (2023)-trailer.mp4
    """
    disk1 = tmp_path / "disk1"
    disk1.mkdir()

    movie_a = disk1 / "Movie A (2020)"
    movie_a.mkdir()
    (movie_a / "Movie A (2020).mp4").touch()
    (movie_a / "Movie A (2020)-trailer.mp4").touch()

    movie_b = disk1 / "Movie B (2021)"
    movie_b.mkdir()
    (movie_b / "Movie B (2021).mp4").touch()

    disk2 = tmp_path / "disk2"
    disk2.mkdir()

    movie_c = disk2 / "Movie C (2022)"
    movie_c.mkdir()
    (movie_c / "Movie C (2022).avi").touch()

    movie_d = disk2 / "Movie D (2023)"
    movie_d.mkdir()
    (movie_d / "Movie D (2023).m4v").touch()
    (movie_d / "Movie D (2023)-trailer.mp4").touch()

    return disk1, disk2


class TestMovieScannerInit:
    """Test MovieScanner initialization."""

    def test_default_initialization(self):
        """Test MovieScanner initializes with default trailer pattern."""
        scanner = MovieScanner()
        assert scanner.trailer_pattern == "*-trailer.mp4"

    def test_custom_pattern_initialization(self):
        """Test MovieScanner initializes with custom trailer pattern."""
        scanner = MovieScanner(trailer_pattern="*-preview.mp4")
        assert scanner.trailer_pattern == "*-preview.mp4"


class TestMovieScannerScan:
    """Test MovieScanner.scan() method."""

    def test_scan_single_directory(
        self, temp_movie_structure
    ):  # pylint: disable=redefined-outer-name
        """Test scanning a single directory for movie folders."""
        scanner = MovieScanner()
        movie_dirs = scanner.scan([temp_movie_structure])

        # Should find 3 movie directories (not the empty directory)
        assert len(movie_dirs) == 3

        movie_names = {d.name for d in movie_dirs}
        assert "Movie With Trailer (2020)" in movie_names
        assert "Movie Missing Preview (2021)" in movie_names
        assert "Movie With Multiple Videos (2022)" in movie_names
        assert "Empty Directory" not in movie_names

    def test_scan_multiple_directories(
        self, multi_disk_structure
    ):  # pylint: disable=redefined-outer-name
        """Test scanning multiple directories for movie folders."""
        disk1, disk2 = multi_disk_structure
        scanner = MovieScanner()
        movie_dirs = scanner.scan([disk1, disk2])

        # Should find 4 movie directories across both disks
        assert len(movie_dirs) == 4

        movie_names = {d.name for d in movie_dirs}
        assert "Movie A (2020)" in movie_names
        assert "Movie B (2021)" in movie_names
        assert "Movie C (2022)" in movie_names
        assert "Movie D (2023)" in movie_names

    def test_scan_empty_paths_list(self):
        """Test scanning with empty paths list raises ValueError."""
        scanner = MovieScanner()
        with pytest.raises(ValueError, match="Paths list cannot be empty"):
            scanner.scan([])

    def test_scan_nonexistent_path(self, tmp_path):
        """Test scanning nonexistent path returns empty list."""
        scanner = MovieScanner()
        nonexistent = tmp_path / "does_not_exist"
        movie_dirs = scanner.scan([nonexistent])

        # Should return empty list and log warning
        assert not movie_dirs

    def test_scan_file_instead_of_directory(self, tmp_path):
        """Test scanning a file instead of directory returns empty list."""
        scanner = MovieScanner()
        test_file = tmp_path / "test.txt"
        test_file.touch()
        movie_dirs = scanner.scan([test_file])

        # Should return empty list and log warning
        assert not movie_dirs

    def test_scan_supports_various_video_extensions(self, tmp_path):
        """Test that scan detects various video file extensions."""
        scanner = MovieScanner()

        # Create movies with different video extensions
        extensions = [".mp4", ".mkv", ".avi", ".m4v", ".mov"]
        for ext in extensions:
            movie_dir = tmp_path / f"Movie{ext}"
            movie_dir.mkdir()
            (movie_dir / f"video{ext}").touch()

        movie_dirs = scanner.scan([tmp_path])
        assert len(movie_dirs) == len(extensions)


class TestMovieScannerFindMissingTrailers:
    """Test MovieScanner.find_missing_trailers() method."""

    def test_find_missing_trailers_single_directory(
        self, temp_movie_structure
    ):  # pylint: disable=redefined-outer-name
        """Test finding movies without trailers in a single directory."""
        scanner = MovieScanner()
        missing = scanner.find_missing_trailers([temp_movie_structure])

        # Should find 2 movies without trailers
        assert len(missing) == 2

        movie_names = {d.name for d in missing}
        assert "Movie Missing Preview (2021)" in movie_names
        assert "Movie With Multiple Videos (2022)" in movie_names
        assert "Movie With Trailer (2020)" not in movie_names

    def test_find_missing_trailers_multiple_directories(
        self, multi_disk_structure
    ):  # pylint: disable=redefined-outer-name
        """Test finding movies without trailers across multiple directories."""
        disk1, disk2 = multi_disk_structure
        scanner = MovieScanner()
        missing = scanner.find_missing_trailers([disk1, disk2])

        # Should find 2 movies without trailers
        assert len(missing) == 2

        movie_names = {d.name for d in missing}
        assert "Movie B (2021)" in movie_names
        assert "Movie C (2022)" in movie_names
        assert "Movie A (2020)" not in movie_names
        assert "Movie D (2023)" not in movie_names

    def test_find_missing_trailers_empty_paths_list(self):
        """Test finding missing trailers with empty paths list raises ValueError."""
        scanner = MovieScanner()
        with pytest.raises(ValueError, match="Paths list cannot be empty"):
            scanner.find_missing_trailers([])

    def test_find_missing_trailers_all_have_trailers(self, tmp_path):
        """Test when all movies have trailers, returns empty list."""
        scanner = MovieScanner()

        # Create movies all with trailers
        for i in range(3):
            movie_dir = tmp_path / f"Movie {i}"
            movie_dir.mkdir()
            (movie_dir / f"Movie {i}.mp4").touch()
            (movie_dir / f"Movie {i}-trailer.mp4").touch()

        missing = scanner.find_missing_trailers([tmp_path])
        assert not missing

    def test_find_missing_trailers_none_have_trailers(self, tmp_path):
        """Test when no movies have trailers, returns all movies."""
        scanner = MovieScanner()

        # Create movies without trailers
        movie_count = 3
        for i in range(movie_count):
            movie_dir = tmp_path / f"Movie {i}"
            movie_dir.mkdir()
            (movie_dir / f"Movie {i}.mp4").touch()

        missing = scanner.find_missing_trailers([tmp_path])
        assert len(missing) == movie_count

    def test_custom_trailer_pattern(self, tmp_path):
        """Test that trailer_pattern parameter is maintained for backward compatibility."""
        scanner = MovieScanner(trailer_pattern="*-preview.mp4")

        # The trailer_pattern is now for backward compatibility only
        # Actual detection uses flexible pattern matching (-trailer keyword)
        movie1 = tmp_path / "Movie 1"
        movie1.mkdir()
        (movie1 / "Movie 1.mp4").touch()
        (movie1 / "Movie 1-trailer.mp4").touch()  # Has -trailer

        movie2 = tmp_path / "Movie 2"
        movie2.mkdir()
        (movie2 / "Movie 2.mp4").touch()

        missing = scanner.find_missing_trailers([tmp_path])

        # Movie 1 has trailer (with -trailer keyword), Movie 2 doesn't
        assert len(missing) == 1
        assert missing[0].name == "Movie 2"

    def test_find_missing_trailers_nonexistent_path(self, tmp_path):
        """Test finding missing trailers in nonexistent path returns empty list."""
        scanner = MovieScanner()
        nonexistent = tmp_path / "does_not_exist"
        missing = scanner.find_missing_trailers([nonexistent])

        # Should return empty list
        assert not missing

    def test_flexible_trailer_detection_various_extensions(self, tmp_path):
        """Test that trailers with various extensions are detected."""
        scanner = MovieScanner()

        # Create movies with trailers using different extensions
        movie1 = tmp_path / "Movie 1"
        movie1.mkdir()
        (movie1 / "Movie 1.mp4").touch()
        (movie1 / "Movie 1-trailer.mkv").touch()  # Different extension

        movie2 = tmp_path / "Movie 2"
        movie2.mkdir()
        (movie2 / "Movie 2.mp4").touch()
        (movie2 / "Movie 2-trailer.avi").touch()  # Different extension

        movie3 = tmp_path / "Movie 3"
        movie3.mkdir()
        (movie3 / "Movie 3.mp4").touch()
        (movie3 / "Movie 3-trailer.webm").touch()  # Different extension

        missing = scanner.find_missing_trailers([tmp_path])
        assert len(missing) == 0  # All have trailers despite different extensions

    def test_flexible_trailer_detection_case_insensitive(self, tmp_path):
        """Test that trailer detection is case-insensitive."""
        scanner = MovieScanner()

        # Create movies with trailers using different case patterns
        movie1 = tmp_path / "Movie 1"
        movie1.mkdir()
        (movie1 / "Movie 1.mp4").touch()
        (movie1 / "Movie 1-TRAILER.mp4").touch()  # Uppercase TRAILER

        movie2 = tmp_path / "Movie 2"
        movie2.mkdir()
        (movie2 / "Movie 2.mp4").touch()
        (movie2 / "Movie 2-Trailer.mp4").touch()  # Mixed case

        movie3 = tmp_path / "Movie 3"
        movie3.mkdir()
        (movie3 / "Movie 3.mp4").touch()
        (movie3 / "MOVIE-TRAILER.mp4").touch()  # All caps with -trailer

        missing = scanner.find_missing_trailers([tmp_path])
        assert len(missing) == 0  # All have trailers despite different case

    def test_flexible_trailer_detection_various_naming_patterns(self, tmp_path):
        """Test that various naming patterns with '-trailer' are detected."""
        scanner = MovieScanner()

        # Create movies with trailers using different naming patterns
        movie1 = tmp_path / "Movie 1"
        movie1.mkdir()
        (movie1 / "Movie 1.mp4").touch()
        (movie1 / "official-trailer.mp4").touch()  # Different prefix

        movie2 = tmp_path / "Movie 2"
        movie2.mkdir()
        (movie2 / "Movie 2.mp4").touch()
        (movie2 / "movie-trailer-1080p.mp4").touch()  # With quality suffix

        movie3 = tmp_path / "Movie 3"
        movie3.mkdir()
        (movie3 / "Movie 3.mp4").touch()
        (movie3 / "the-movie-trailer-eng.mkv").touch()  # Complex pattern

        missing = scanner.find_missing_trailers([tmp_path])
        assert len(missing) == 0  # All have trailers with '-trailer' in name

    def test_flexible_trailer_detection_without_trailer_keyword(self, tmp_path):
        """Test that files without 'trailer' keyword are not considered trailers."""
        scanner = MovieScanner()

        # Create movies with extra files but no actual trailer
        movie1 = tmp_path / "Movie 1"
        movie1.mkdir()
        (movie1 / "Movie 1.mp4").touch()
        (movie1 / "Movie 1-behind-scenes.mp4").touch()  # Not a trailer

        movie2 = tmp_path / "Movie 2"
        movie2.mkdir()
        (movie2 / "Movie 2.mp4").touch()
        (movie2 / "Movie 2-preview.mp4").touch()  # Not a trailer

        missing = scanner.find_missing_trailers([tmp_path])
        assert len(missing) == 2  # Both should be missing trailers

    def test_flexible_trailer_detection_without_dash(self, tmp_path):
        """Test that trailers without dash separator are also detected."""
        scanner = MovieScanner()

        # Create movies with trailers without dash
        movie1 = tmp_path / "Movie 1"
        movie1.mkdir()
        (movie1 / "Movie 1.mp4").touch()
        (movie1 / "MovieTrailer.mp4").touch()  # No dash

        movie2 = tmp_path / "Movie 2"
        movie2.mkdir()
        (movie2 / "Movie 2.mp4").touch()
        (movie2 / "Movie Trailer.mkv").touch()  # Space instead of dash

        movie3 = tmp_path / "Movie 3"
        movie3.mkdir()
        (movie3 / "Movie 3.mp4").touch()
        (movie3 / "trailer.mp4").touch()  # Just "trailer"

        missing = scanner.find_missing_trailers([tmp_path])
        assert len(missing) == 0  # All have trailers despite no dash


class TestMovieScannerHasTrailer:
    """Test MovieScanner.has_trailer() method."""

    def test_has_trailer_true_with_standard_naming(self, tmp_path):
        """Test has_trailer returns True for standard trailer naming."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()
        (movie_dir / "Movie.mp4").touch()
        (movie_dir / "Movie-trailer.mp4").touch()

        assert scanner.has_trailer(movie_dir) is True

    def test_has_trailer_true_case_insensitive(self, tmp_path):
        """Test has_trailer returns True for case-insensitive trailer names."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()
        (movie_dir / "Movie.mp4").touch()
        (movie_dir / "MOVIE-TRAILER.mp4").touch()

        assert scanner.has_trailer(movie_dir) is True

    def test_has_trailer_true_various_extensions(self, tmp_path):
        """Test has_trailer returns True for trailers with various extensions."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()
        (movie_dir / "Movie.mp4").touch()
        (movie_dir / "Movie-trailer.mkv").touch()

        assert scanner.has_trailer(movie_dir) is True

    def test_has_trailer_false_no_trailer(self, tmp_path):
        """Test has_trailer returns False when no trailer exists."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()
        (movie_dir / "Movie.mp4").touch()

        assert scanner.has_trailer(movie_dir) is False

    def test_has_trailer_false_without_trailer_keyword(self, tmp_path):
        """Test has_trailer returns False for files without 'trailer' keyword."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()
        (movie_dir / "Movie.mp4").touch()
        (movie_dir / "Movie-preview.mp4").touch()

        assert scanner.has_trailer(movie_dir) is False

    def test_has_trailer_true_without_dash(self, tmp_path):
        """Test has_trailer returns True for trailers without dash separator."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()
        (movie_dir / "Movie.mp4").touch()
        (movie_dir / "MovieTrailer.mp4").touch()

        assert scanner.has_trailer(movie_dir) is True

    def test_has_trailer_true_just_trailer(self, tmp_path):
        """Test has_trailer returns True for file named just 'trailer'."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()
        (movie_dir / "Movie.mp4").touch()
        (movie_dir / "trailer.mp4").touch()

        assert scanner.has_trailer(movie_dir) is True

    def test_has_trailer_handles_permission_error(self, tmp_path):
        """Test has_trailer handles permission errors gracefully."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()

        # Mock iterdir to raise PermissionError using Path class
        with patch("pathlib.Path.iterdir", side_effect=PermissionError("Access denied")):
            assert scanner.has_trailer(movie_dir) is False
