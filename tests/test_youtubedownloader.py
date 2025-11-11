#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for YoutubeDownloader class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from youtubetrailerscraper.youtubedownloader import YoutubeDownloader


class TestYoutubeDownloaderInit:
    """Tests for YoutubeDownloader initialization."""

    def test_default_initialization(self):
        """Test YoutubeDownloader initializes with default logger."""
        downloader = YoutubeDownloader()
        assert downloader is not None
        assert downloader.logger is not None

    def test_initialization_with_logger(self):
        """Test YoutubeDownloader initializes with custom logger."""
        mock_logger = MagicMock()
        downloader = YoutubeDownloader(logger=mock_logger)
        assert downloader.logger is mock_logger


class TestYoutubeDownloaderDownload:
    """Tests for download method."""

    def test_download_with_empty_url(self):
        """Test download with empty URL returns None."""
        downloader = YoutubeDownloader()
        result = downloader.download("", Path("/tmp"), "output")
        assert result is None

    def test_download_with_existing_file(self, tmp_path):
        """Test download skips if file already exists."""
        downloader = YoutubeDownloader()
        output_file = tmp_path / "test-trailer.mp4"
        output_file.write_text("fake video")

        result = downloader.download(
            "https://youtube.com/watch?v=abc123", tmp_path, "test-trailer"
        )

        assert result == output_file
        assert output_file.exists()

    @patch("yt_dlp.YoutubeDL")
    def test_download_successful(self, mock_ytdl, tmp_path):
        """Test successful download."""
        # Setup mock
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance
        mock_instance.download.return_value = None

        downloader = YoutubeDownloader()
        result = downloader.download(
            "https://youtube.com/watch?v=abc123", tmp_path, "test-trailer"
        )

        assert result == tmp_path / "test-trailer.mp4"
        mock_instance.download.assert_called_once_with(["https://youtube.com/watch?v=abc123"])

    @patch("yt_dlp.YoutubeDL")
    def test_download_creates_output_directory(self, mock_ytdl, tmp_path):
        """Test download creates output directory if it doesn't exist."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        output_dir = tmp_path / "nested" / "dir"
        downloader = YoutubeDownloader()
        downloader.download("https://youtube.com/watch?v=abc123", output_dir, "test")

        assert output_dir.exists()

    @patch("yt_dlp.YoutubeDL")
    def test_download_handles_ytdl_error(self, mock_ytdl, tmp_path):
        """Test download handles yt-dlp errors gracefully."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance
        mock_instance.download.side_effect = Exception("Download failed")

        downloader = YoutubeDownloader()
        result = downloader.download(
            "https://youtube.com/watch?v=abc123", tmp_path, "test-trailer"
        )

        assert result is None

    @patch("yt_dlp.YoutubeDL")
    def test_download_configures_ytdl_options_correctly(self, mock_ytdl, tmp_path):
        """Test download configures yt-dlp with correct options."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        downloader = YoutubeDownloader()
        downloader.download("https://youtube.com/watch?v=abc123", tmp_path, "test-trailer")

        # Verify YoutubeDL was called with correct options
        call_args = mock_ytdl.call_args
        opts = call_args[0][0]

        assert "format" in opts
        assert "1080" in opts["format"]
        assert opts["merge_output_format"] == "mp4"
        assert opts["quiet"] is True


class TestYoutubeDownloaderMovieTrailers:
    """Tests for download_trailers_for_movie method."""

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_movie_single_trailer(self, mock_ytdl, tmp_path):
        """Test downloading a single trailer for a movie."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        movie_dir = tmp_path / "Inception (2010)"
        movie_dir.mkdir()

        downloader = YoutubeDownloader()
        urls = ["https://youtube.com/watch?v=abc123"]
        result = downloader.download_trailers_for_movie(movie_dir, urls)

        assert len(result) == 1
        assert result[0].name == "Inception (2010) - trailer #1 -trailer.mp4"
        assert result[0].parent == movie_dir

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_movie_multiple_trailers(self, mock_ytdl, tmp_path):
        """Test downloading multiple trailers for a movie."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        movie_dir = tmp_path / "The Matrix (1999)"
        movie_dir.mkdir()

        downloader = YoutubeDownloader()
        urls = [
            "https://youtube.com/watch?v=abc123",
            "https://youtube.com/watch?v=def456",
            "https://youtube.com/watch?v=ghi789",
        ]
        result = downloader.download_trailers_for_movie(movie_dir, urls)

        assert len(result) == 3
        assert result[0].name == "The Matrix (1999) - trailer #1 -trailer.mp4"
        assert result[1].name == "The Matrix (1999) - trailer #2 -trailer.mp4"
        assert result[2].name == "The Matrix (1999) - trailer #3 -trailer.mp4"

    def test_download_trailers_for_movie_empty_urls(self, tmp_path):
        """Test download_trailers_for_movie with empty URL list."""
        downloader = YoutubeDownloader()
        result = downloader.download_trailers_for_movie(tmp_path, [])
        assert not result

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_movie_handles_failures(self, mock_ytdl, tmp_path):
        """Test download_trailers_for_movie handles individual failures."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance
        # First download succeeds, second fails
        mock_instance.download.side_effect = [None, Exception("Failed")]

        movie_dir = tmp_path / "Test Movie (2020)"
        movie_dir.mkdir()

        downloader = YoutubeDownloader()
        urls = [
            "https://youtube.com/watch?v=abc123",
            "https://youtube.com/watch?v=def456",
        ]
        result = downloader.download_trailers_for_movie(movie_dir, urls)

        # Only first trailer should succeed
        assert len(result) == 1
        assert result[0].name == "Test Movie (2020) - trailer #1 -trailer.mp4"

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_movie_limits_to_max_trailers(self, mock_ytdl, tmp_path):
        """Test download_trailers_for_movie limits downloads to MAX_TRAILERS_PER_MEDIA."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        movie_dir = tmp_path / "Popular Movie (2023)"
        movie_dir.mkdir()

        downloader = YoutubeDownloader()
        # Provide 5 URLs, but only 3 should be downloaded
        urls = [
            "https://youtube.com/watch?v=url1",
            "https://youtube.com/watch?v=url2",
            "https://youtube.com/watch?v=url3",
            "https://youtube.com/watch?v=url4",
            "https://youtube.com/watch?v=url5",
        ]
        result = downloader.download_trailers_for_movie(movie_dir, urls)

        # Should only download first 3 trailers (MAX_TRAILERS_PER_MEDIA = 3)
        assert len(result) == 3
        assert result[0].name == "Popular Movie (2023) - trailer #1 -trailer.mp4"
        assert result[1].name == "Popular Movie (2023) - trailer #2 -trailer.mp4"
        assert result[2].name == "Popular Movie (2023) - trailer #3 -trailer.mp4"

        # Verify only 3 download calls were made
        assert mock_instance.download.call_count == 3


class TestYoutubeDownloaderTVShowTrailers:
    """Tests for download_trailers_for_tvshow method."""

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_tvshow_single_trailer(self, mock_ytdl, tmp_path):
        """Test downloading a single trailer for a TV show."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        tvshow_dir = tmp_path / "Breaking Bad"
        tvshow_dir.mkdir()

        downloader = YoutubeDownloader()
        urls = ["https://youtube.com/watch?v=abc123"]
        result = downloader.download_trailers_for_tvshow(tvshow_dir, urls)

        assert len(result) == 1
        assert result[0].name == "trailer #1.mp4"
        assert result[0].parent.name == "trailers"
        assert result[0].parent.parent == tvshow_dir

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_tvshow_multiple_trailers(self, mock_ytdl, tmp_path):
        """Test downloading multiple trailers for a TV show."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        tvshow_dir = tmp_path / "Stranger Things"
        tvshow_dir.mkdir()

        downloader = YoutubeDownloader()
        urls = [
            "https://youtube.com/watch?v=abc123",
            "https://youtube.com/watch?v=def456",
        ]
        result = downloader.download_trailers_for_tvshow(tvshow_dir, urls)

        assert len(result) == 2
        assert result[0].name == "trailer #1.mp4"
        assert result[1].name == "trailer #2.mp4"
        assert all(p.parent.name == "trailers" for p in result)

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_tvshow_creates_trailers_subdir(self, mock_ytdl, tmp_path):
        """Test that trailers subdirectory is created if it doesn't exist."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        tvshow_dir = tmp_path / "Game of Thrones"
        tvshow_dir.mkdir()

        downloader = YoutubeDownloader()
        urls = ["https://youtube.com/watch?v=abc123"]
        downloader.download_trailers_for_tvshow(tvshow_dir, urls)

        trailers_dir = tvshow_dir / "trailers"
        assert trailers_dir.exists()
        assert trailers_dir.is_dir()

    def test_download_trailers_for_tvshow_empty_urls(self, tmp_path):
        """Test download_trailers_for_tvshow with empty URL list."""
        downloader = YoutubeDownloader()
        result = downloader.download_trailers_for_tvshow(tmp_path, [])
        assert not result

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_tvshow_handles_failures(self, mock_ytdl, tmp_path):
        """Test download_trailers_for_tvshow handles individual failures."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance
        # First two succeed, third fails
        mock_instance.download.side_effect = [None, None, Exception("Failed")]

        tvshow_dir = tmp_path / "The Office"
        tvshow_dir.mkdir()

        downloader = YoutubeDownloader()
        urls = [
            "https://youtube.com/watch?v=abc123",
            "https://youtube.com/watch?v=def456",
            "https://youtube.com/watch?v=ghi789",
        ]
        result = downloader.download_trailers_for_tvshow(tvshow_dir, urls)

        # Only first two trailers should succeed
        assert len(result) == 2
        assert result[0].name == "trailer #1.mp4"
        assert result[1].name == "trailer #2.mp4"

    @patch("yt_dlp.YoutubeDL")
    def test_download_trailers_for_tvshow_limits_to_max_trailers(self, mock_ytdl, tmp_path):
        """Test download_trailers_for_tvshow limits downloads to MAX_TRAILERS_PER_MEDIA."""
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance

        tvshow_dir = tmp_path / "Popular Series"
        tvshow_dir.mkdir()

        downloader = YoutubeDownloader()
        # Provide 6 URLs, but only 3 should be downloaded
        urls = [
            "https://youtube.com/watch?v=url1",
            "https://youtube.com/watch?v=url2",
            "https://youtube.com/watch?v=url3",
            "https://youtube.com/watch?v=url4",
            "https://youtube.com/watch?v=url5",
            "https://youtube.com/watch?v=url6",
        ]
        result = downloader.download_trailers_for_tvshow(tvshow_dir, urls)

        # Should only download first 3 trailers (MAX_TRAILERS_PER_MEDIA = 3)
        assert len(result) == 3
        assert result[0].name == "trailer #1.mp4"
        assert result[1].name == "trailer #2.mp4"
        assert result[2].name == "trailer #3.mp4"

        # Verify only 3 download calls were made
        assert mock_instance.download.call_count == 3
