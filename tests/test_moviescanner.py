#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for MovieScanner class."""

from pathlib import Path  # pylint: disable=unused-import

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
            Movie Without Trailer (2021)/
                Movie Without Trailer (2021).mp4
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
    movie2 = movies_dir / "Movie Without Trailer (2021)"
    movie2.mkdir()
    (movie2 / "Movie Without Trailer (2021).mp4").touch()

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

    def test_scan_single_directory(self, temp_movie_structure):  # pylint: disable=redefined-outer-name
        """Test scanning a single directory for movie folders."""
        scanner = MovieScanner()
        movie_dirs = scanner.scan([temp_movie_structure])

        # Should find 3 movie directories (not the empty directory)
        assert len(movie_dirs) == 3

        movie_names = {d.name for d in movie_dirs}
        assert "Movie With Trailer (2020)" in movie_names
        assert "Movie Without Trailer (2021)" in movie_names
        assert "Movie With Multiple Videos (2022)" in movie_names
        assert "Empty Directory" not in movie_names

    def test_scan_multiple_directories(self, multi_disk_structure):  # pylint: disable=redefined-outer-name
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

    def test_find_missing_trailers_single_directory(self, temp_movie_structure):  # pylint: disable=redefined-outer-name
        """Test finding movies without trailers in a single directory."""
        scanner = MovieScanner()
        missing = scanner.find_missing_trailers([temp_movie_structure])

        # Should find 2 movies without trailers
        assert len(missing) == 2

        movie_names = {d.name for d in missing}
        assert "Movie Without Trailer (2021)" in movie_names
        assert "Movie With Multiple Videos (2022)" in movie_names
        assert "Movie With Trailer (2020)" not in movie_names

    def test_find_missing_trailers_multiple_directories(self, multi_disk_structure):  # pylint: disable=redefined-outer-name
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
        """Test finding missing trailers with custom pattern."""
        scanner = MovieScanner(trailer_pattern="*-preview.mp4")

        # Create movies with -preview.mp4 trailers
        movie1 = tmp_path / "Movie 1"
        movie1.mkdir()
        (movie1 / "Movie 1.mp4").touch()
        (movie1 / "Movie 1-preview.mp4").touch()

        movie2 = tmp_path / "Movie 2"
        movie2.mkdir()
        (movie2 / "Movie 2.mp4").touch()

        missing = scanner.find_missing_trailers([tmp_path])

        # Should only find Movie 2 missing (since it lacks -preview.mp4)
        assert len(missing) == 1
        assert missing[0].name == "Movie 2"

    def test_find_missing_trailers_nonexistent_path(self, tmp_path):
        """Test finding missing trailers in nonexistent path returns empty list."""
        scanner = MovieScanner()
        nonexistent = tmp_path / "does_not_exist"
        missing = scanner.find_missing_trailers([nonexistent])

        # Should return empty list
        assert not missing
