#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
youtubedownloader.py

Description:
    Download videos from YouTube from given URLs using yt-dlp

Usage:
    from youtubedownloader import YoutubeDownloader

    downloader = YoutubeDownloader()
    path = downloader.download("https://youtube.com/watch?v=...", Path("/output/dir"), "video")

Requirements:
    - yt-dlp

References:
    - yt-dlp documentation: https://github.com/yt-dlp/yt-dlp

"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yt_dlp


class YoutubeDownloader:
    """Download videos from YouTube from given URLs using yt-dlp."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize YoutubeDownloader.

        Args:
            logger: Optional logger instance. If None, creates a NullHandler logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        if not logger:
            self.logger.addHandler(logging.NullHandler())

    def download(self, url: str, output_dir: Path, output_filename: str) -> Optional[Path]:
        """Download video from YouTube using yt-dlp.

        Downloads YouTube video in MP4 format (max 1080p) to the specified directory
        with the given filename. Skips download if file already exists.

        Args:
            url: YouTube video URL (e.g., "https://youtube.com/watch?v=abc123").
            output_dir: Directory where the video should be saved.
            output_filename: Filename for the downloaded video (without extension).

        Returns:
            Path to the downloaded video file if successful, None if failed or skipped.

        Example:
            >>> downloader = YoutubeDownloader()
            >>> path = downloader.download(
            ...     "https://youtube.com/watch?v=abc123",
            ...     Path("/movies/Inception (2010)"),
            ...     "Inception (2010) - trailer #1 -trailer"
            ... )
            >>> print(path)
            /movies/Inception (2010)/Inception (2010) - trailer #1 -trailer.mp4
        """
        if not url:
            self.logger.warning("Empty URL provided, skipping download")
            return None

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Full output path with .mp4 extension
        output_path = output_dir / f"{output_filename}.mp4"

        # Skip if file already exists
        if output_path.exists():
            self.logger.info(f"File already exists, skipping: {output_path}")
            return output_path

        # Configure yt-dlp options
        ydl_opts = {
            "format": (
                "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/"
                "best[ext=mp4][height<=1080]/best"
            ),
            "outtmpl": str(output_path.with_suffix("")),  # yt-dlp adds extension
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.logger.info(f"Downloading: {url} -> {output_path}")
                ydl.download([url])
            self.logger.info(f"Successfully downloaded: {output_path}")
            return output_path
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error(f"Failed to download {url}: {e}")
            return None

    def download_trailers_for_movie(self, movie_path: Path, youtube_urls: list[str]) -> list[Path]:
        """Download trailers for a movie to its directory.

        Downloads all trailers to the same directory as the movie file.
        Filenames follow pattern: "{movie_name} - trailer #N -trailer.mp4"

        Args:
            movie_path: Path to the movie directory.
            youtube_urls: List of YouTube URLs for trailers.

        Returns:
            List of Path objects for successfully downloaded trailers.

        Example:
            >>> downloader = YoutubeDownloader()
            >>> paths = downloader.download_trailers_for_movie(
            ...     Path("/movies/Inception (2010)"),
            ...     ["https://youtube.com/watch?v=abc123", "https://youtube.com/watch?v=xyz789"]
            ... )
            >>> # Results in:
            >>> # /movies/Inception (2010)/Inception (2010) - trailer #1 -trailer.mp4
            >>> # /movies/Inception (2010)/Inception (2010) - trailer #2 -trailer.mp4
        """
        if not youtube_urls:
            return []

        movie_name = movie_path.name
        downloaded_paths = []

        for idx, url in enumerate(youtube_urls, start=1):
            filename = f"{movie_name} - trailer #{idx} -trailer"
            downloaded_path = self.download(url, movie_path, filename)
            if downloaded_path:
                downloaded_paths.append(downloaded_path)

        self.logger.info(
            f"Downloaded {len(downloaded_paths)}/{len(youtube_urls)} trailers for: {movie_name}"
        )
        return downloaded_paths

    def download_trailers_for_tvshow(
        self, tvshow_path: Path, youtube_urls: list[str]
    ) -> list[Path]:
        """Download trailers for a TV show to its trailers subdirectory.

        Creates a "trailers" subdirectory if it doesn't exist and downloads all
        trailers there. Filenames follow pattern: "trailer #N.mp4"

        Args:
            tvshow_path: Path to the TV show directory.
            youtube_urls: List of YouTube URLs for trailers.

        Returns:
            List of Path objects for successfully downloaded trailers.

        Example:
            >>> downloader = YoutubeDownloader()
            >>> paths = downloader.download_trailers_for_tvshow(
            ...     Path("/tvshows/Breaking Bad"),
            ...     ["https://youtube.com/watch?v=abc123"]
            ... )
            >>> # Results in:
            >>> # /tvshows/Breaking Bad/trailers/trailer #1.mp4
        """
        if not youtube_urls:
            return []

        trailers_dir = tvshow_path / "trailers"
        tvshow_name = tvshow_path.name
        downloaded_paths = []

        for idx, url in enumerate(youtube_urls, start=1):
            filename = f"trailer #{idx}"
            downloaded_path = self.download(url, trailers_dir, filename)
            if downloaded_path:
                downloaded_paths.append(downloaded_path)

        self.logger.info(
            f"Downloaded {len(downloaded_paths)}/{len(youtube_urls)} trailers for: {tvshow_name}"
        )
        return downloaded_paths
