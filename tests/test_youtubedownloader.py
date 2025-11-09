#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for YoutubeDownloader class."""

import pytest

from youtubetrailerscraper.youtubedownloader import YoutubeDownloader


class TestYoutubeDownloaderInit:  # pylint: disable=too-few-public-methods
    """Tests for YoutubeDownloader initialization."""

    def test_default_initialization(self):
        """Test YoutubeDownloader initializes correctly."""
        downloader = YoutubeDownloader()
        assert downloader is not None


class TestYoutubeDownloaderDownload:
    """Tests for download method."""

    def test_download_raises_not_implemented(self):
        """Test download raises NotImplementedError (skeleton implementation)."""
        downloader = YoutubeDownloader()
        # Skeleton implementation raises NotImplementedError
        with pytest.raises(NotImplementedError, match="Download method not yet implemented"):
            downloader.download("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_download_with_valid_url(self):
        """Test download with valid YouTube URL raises NotImplementedError."""
        downloader = YoutubeDownloader()
        with pytest.raises(NotImplementedError):
            downloader.download("https://www.youtube.com/watch?v=test123")

    def test_download_with_empty_url(self):
        """Test download with empty URL raises NotImplementedError."""
        downloader = YoutubeDownloader()
        with pytest.raises(NotImplementedError):
            downloader.download("")
