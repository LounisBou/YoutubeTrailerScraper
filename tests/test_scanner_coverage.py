#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Additional tests to achieve 100% code coverage for scanner classes."""

from unittest.mock import patch

from youtubetrailerscraper.moviescanner import (  # pylint: disable=import-error
    MovieScanner,
)
from youtubetrailerscraper.tvshowscanner import (  # pylint: disable=import-error
    TVShowScanner,
)


class TestMovieScannerCoverage:
    """Tests to cover remaining lines in MovieScanner."""

    def test_has_video_files_permission_error(self, tmp_path):
        """Test _has_video_files handles PermissionError gracefully."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()

        # Mock iterdir to raise PermissionError
        with patch.object(
            type(movie_dir), "iterdir", side_effect=PermissionError("Access denied")
        ):
            # pylint: disable=protected-access
            assert scanner._has_video_files(movie_dir) is False

    def test_has_video_files_os_error(self, tmp_path):
        """Test _has_video_files handles OSError gracefully."""
        scanner = MovieScanner()
        movie_dir = tmp_path / "Movie"
        movie_dir.mkdir()

        # Mock iterdir to raise OSError
        with patch.object(type(movie_dir), "iterdir", side_effect=OSError("Disk error")):
            # pylint: disable=protected-access
            assert scanner._has_video_files(movie_dir) is False

    def test_find_missing_trailers_path_not_exists(self, tmp_path):
        """Test find_missing_trailers handles non-existent path."""
        scanner = MovieScanner()
        non_existent = tmp_path / "does_not_exist"
        results = scanner.find_missing_trailers([non_existent])
        assert not results

    def test_find_missing_trailers_path_is_file(self, tmp_path):
        """Test find_missing_trailers handles path that is a file, not directory."""
        scanner = MovieScanner()
        file_path = tmp_path / "file.txt"
        file_path.touch()
        results = scanner.find_missing_trailers([file_path])
        assert not results

    def test_find_missing_trailers_progress_logging(self, tmp_path):
        """Test find_missing_trailers with many folders (triggers progress logging)."""
        scanner = MovieScanner()
        movies_dir = tmp_path / "movies"
        movies_dir.mkdir()

        # Create 101 movie folders to trigger progress logging at 100
        for i in range(101):
            movie = movies_dir / f"Movie{i:03d}"
            movie.mkdir()
            (movie / "movie.mp4").touch()

        results = scanner.find_missing_trailers([movies_dir])
        # All should be missing trailers
        assert len(results) == 101

    def test_find_missing_trailers_permission_error(self, tmp_path):
        """Test find_missing_trailers handles PermissionError on directory scan."""
        scanner = MovieScanner()
        movies_dir = tmp_path / "movies"
        movies_dir.mkdir()

        # Mock iterdir to raise PermissionError
        with patch.object(
            type(movies_dir), "iterdir", side_effect=PermissionError("Access denied")
        ):
            results = scanner.find_missing_trailers([movies_dir])
            assert not results

    def test_find_missing_trailers_os_error(self, tmp_path):
        """Test find_missing_trailers handles OSError on directory scan."""
        scanner = MovieScanner()
        movies_dir = tmp_path / "movies"
        movies_dir.mkdir()

        # Mock iterdir to raise OSError
        with patch.object(type(movies_dir), "iterdir", side_effect=OSError("Disk error")):
            results = scanner.find_missing_trailers([movies_dir])
            assert not results


class TestTVShowScannerCoverage:
    """Tests to cover remaining lines in TVShowScanner."""

    def test_has_video_files_permission_error(self, tmp_path):
        """Test _has_video_files handles PermissionError gracefully."""
        scanner = TVShowScanner()
        tvshow_dir = tmp_path / "Show"
        tvshow_dir.mkdir()

        # Mock iterdir to raise PermissionError
        with patch.object(
            type(tvshow_dir), "iterdir", side_effect=PermissionError("Access denied")
        ):
            # pylint: disable=protected-access
            assert scanner._has_video_files(tvshow_dir) is False

    def test_has_video_files_os_error(self, tmp_path):
        """Test _has_video_files handles OSError gracefully."""
        scanner = TVShowScanner()
        tvshow_dir = tmp_path / "Show"
        tvshow_dir.mkdir()

        # Mock iterdir to raise OSError
        with patch.object(type(tvshow_dir), "iterdir", side_effect=OSError("Disk error")):
            # pylint: disable=protected-access
            assert scanner._has_video_files(tvshow_dir) is False

    def test_has_subdirectories_with_videos_permission_error(self, tmp_path):
        """Test _has_subdirectories_with_videos handles PermissionError gracefully."""
        scanner = TVShowScanner()
        tvshow_dir = tmp_path / "Show"
        tvshow_dir.mkdir()

        # Mock iterdir to raise PermissionError
        with patch.object(
            type(tvshow_dir), "iterdir", side_effect=PermissionError("Access denied")
        ):
            # pylint: disable=protected-access
            assert scanner._has_subdirectories_with_videos(tvshow_dir) is False

    def test_has_subdirectories_with_videos_os_error(self, tmp_path):
        """Test _has_subdirectories_with_videos handles OSError gracefully."""
        scanner = TVShowScanner()
        tvshow_dir = tmp_path / "Show"
        tvshow_dir.mkdir()

        # Mock iterdir to raise OSError
        with patch.object(type(tvshow_dir), "iterdir", side_effect=OSError("Disk error")):
            # pylint: disable=protected-access
            assert scanner._has_subdirectories_with_videos(tvshow_dir) is False

    def test_has_subdirectories_with_videos_found(self, tmp_path):
        """Test _has_subdirectories_with_videos returns True when video found."""
        scanner = TVShowScanner()
        tvshow_dir = tmp_path / "Show"
        tvshow_dir.mkdir()

        # Create a subdirectory with video files
        season = tvshow_dir / "Season 01"
        season.mkdir()
        (season / "episode.mp4").touch()

        # pylint: disable=protected-access
        assert scanner._has_subdirectories_with_videos(tvshow_dir) is True

    def test_is_tvshow_directory_with_file(self, tmp_path):
        """Test _is_tvshow_directory skips files (not directories)."""
        scanner = TVShowScanner()
        tvshow_dir = tmp_path / "Show"
        tvshow_dir.mkdir()
        (tvshow_dir / "file.txt").touch()

        # pylint: disable=protected-access
        assert scanner._is_tvshow_directory(tvshow_dir) is False

    def test_is_tvshow_directory_season_without_videos(self, tmp_path):
        """Test _is_tvshow_directory with season directory but no videos."""
        scanner = TVShowScanner()
        tvshow_dir = tmp_path / "Show"
        tvshow_dir.mkdir()

        # Create a season directory but with no videos
        season_dir = tvshow_dir / "Season 01"
        season_dir.mkdir()

        # pylint: disable=protected-access
        result = scanner._is_tvshow_directory(tvshow_dir)
        assert result is False

    def test_is_tvshow_directory_no_matching_subdirs(self, tmp_path):
        """Test _is_tvshow_directory with no subdirs matching season pattern."""
        scanner = TVShowScanner()
        tvshow_dir = tmp_path / "Show"
        tvshow_dir.mkdir()

        # Create a non-season directory
        (tvshow_dir / "Extras").mkdir()

        # pylint: disable=protected-access
        result = scanner._is_tvshow_directory(tvshow_dir)
        assert result is False

    def test_find_missing_trailers_path_not_exists(self, tmp_path):
        """Test find_missing_trailers handles non-existent path."""
        scanner = TVShowScanner()
        non_existent = tmp_path / "does_not_exist"
        results = scanner.find_missing_trailers([non_existent])
        assert not results

    def test_find_missing_trailers_path_is_file(self, tmp_path):
        """Test find_missing_trailers handles path that is a file, not directory."""
        scanner = TVShowScanner()
        file_path = tmp_path / "file.txt"
        file_path.touch()
        results = scanner.find_missing_trailers([file_path])
        assert not results

    def test_find_missing_trailers_skips_files(self, tmp_path):
        """Test find_missing_trailers skips files in directory."""
        scanner = TVShowScanner()
        tvshows_dir = tmp_path / "tvshows"
        tvshows_dir.mkdir()

        # Create a file in the directory (should be skipped)
        (tvshows_dir / "README.txt").touch()

        results = scanner.find_missing_trailers([tvshows_dir])
        assert not results

    def test_find_missing_trailers_progress_logging(self, tmp_path):
        """Test find_missing_trailers with many folders (triggers progress logging)."""
        scanner = TVShowScanner()
        tvshows_dir = tmp_path / "tvshows"
        tvshows_dir.mkdir()

        # Create 101 TV show folders to trigger progress logging at 100
        for i in range(101):
            tvshow = tvshows_dir / f"Show{i:03d}"
            tvshow.mkdir()
            season = tvshow / "Season 01"
            season.mkdir()
            (season / "episode.mp4").touch()

        results = scanner.find_missing_trailers([tvshows_dir])
        # All should be missing trailers
        assert len(results) == 101

    def test_find_missing_trailers_skips_non_tvshow(self, tmp_path):
        """Test find_missing_trailers skips non-TV-show directories."""
        scanner = TVShowScanner()
        tvshows_dir = tmp_path / "tvshows"
        tvshows_dir.mkdir()

        # Create a directory that's not a TV show (no season subdirs)
        not_tvshow = tvshows_dir / "NotATVShow"
        not_tvshow.mkdir()
        (not_tvshow / "file.mp4").touch()

        results = scanner.find_missing_trailers([tvshows_dir])
        assert not results

    def test_find_missing_trailers_permission_error(self, tmp_path):
        """Test find_missing_trailers handles PermissionError on directory scan."""
        scanner = TVShowScanner()
        tvshows_dir = tmp_path / "tvshows"
        tvshows_dir.mkdir()

        # Mock iterdir to raise PermissionError
        with patch.object(
            type(tvshows_dir), "iterdir", side_effect=PermissionError("Access denied")
        ):
            results = scanner.find_missing_trailers([tvshows_dir])
            assert not results

    def test_find_missing_trailers_os_error(self, tmp_path):
        """Test find_missing_trailers handles OSError on directory scan."""
        scanner = TVShowScanner()
        tvshows_dir = tmp_path / "tvshows"
        tvshows_dir.mkdir()

        # Mock iterdir to raise OSError
        with patch.object(type(tvshows_dir), "iterdir", side_effect=OSError("Disk error")):
            results = scanner.find_missing_trailers([tvshows_dir])
            assert not results
