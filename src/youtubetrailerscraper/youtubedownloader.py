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

    # Maximum number of trailers to download per movie or TV show
    MAX_TRAILERS_PER_MEDIA = 3

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        cookies_from_browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
    ):
        """Initialize YoutubeDownloader.

        Args:
            logger: Optional logger instance. If None, creates a NullHandler logger.
            cookies_from_browser: Browser name to extract cookies from (e.g., "firefox", "chrome").
                This helps bypass YouTube's bot detection. If provided, takes precedence over
                cookies_file.
            cookies_file: Path to Netscape format cookies file. Used if cookies_from_browser
                is not provided.
        """
        self.logger = logger or logging.getLogger(__name__)
        if not logger:
            self.logger.addHandler(logging.NullHandler())

        self.cookies_from_browser = cookies_from_browser
        self.cookies_file = cookies_file

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

        # Add cookie support to bypass YouTube bot detection
        if self.cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
            self.logger.debug(f"Using cookies from browser: {self.cookies_from_browser}")
        elif self.cookies_file:
            ydl_opts["cookiefile"] = self.cookies_file
            self.logger.debug(f"Using cookies file: {self.cookies_file}")

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

        Downloads up to MAX_TRAILERS_PER_MEDIA trailers to the same directory as the movie file.
        Filenames follow pattern: "{movie_name} - trailer #N -trailer.mp4"

        Args:
            movie_path: Path to the movie directory.
            youtube_urls: List of YouTube URLs for trailers.

        Returns:
            List of Path objects for successfully downloaded trailers.
            Limited to MAX_TRAILERS_PER_MEDIA (3) trailers maximum.

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

        # Limit to MAX_TRAILERS_PER_MEDIA
        urls_to_download = youtube_urls[: self.MAX_TRAILERS_PER_MEDIA]
        if len(youtube_urls) > self.MAX_TRAILERS_PER_MEDIA:
            self.logger.info(
                f"Limiting download to {self.MAX_TRAILERS_PER_MEDIA} trailers "
                f"(found {len(youtube_urls)} available)"
            )

        movie_name = movie_path.name
        downloaded_paths = []

        for idx, url in enumerate(urls_to_download, start=1):
            filename = f"{movie_name} - trailer #{idx} -trailer"
            downloaded_path = self.download(url, movie_path, filename)
            if downloaded_path:
                downloaded_paths.append(downloaded_path)

        self.logger.info(
            f"Downloaded {len(downloaded_paths)}/{len(urls_to_download)} trailers for: {movie_name}"
        )
        return downloaded_paths

    def download_trailers_for_tvshow(
        self, tvshow_path: Path, youtube_urls: list[str]
    ) -> list[Path]:
        """Download trailers for a TV show to its trailers subdirectory.

        Creates a "trailers" subdirectory if it doesn't exist and downloads up to
        MAX_TRAILERS_PER_MEDIA trailers there. Filenames follow pattern: "trailer #N.mp4"

        Args:
            tvshow_path: Path to the TV show directory.
            youtube_urls: List of YouTube URLs for trailers.

        Returns:
            List of Path objects for successfully downloaded trailers.
            Limited to MAX_TRAILERS_PER_MEDIA (3) trailers maximum.

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

        # Limit to MAX_TRAILERS_PER_MEDIA
        urls_to_download = youtube_urls[: self.MAX_TRAILERS_PER_MEDIA]
        if len(youtube_urls) > self.MAX_TRAILERS_PER_MEDIA:
            self.logger.info(
                f"Limiting download to {self.MAX_TRAILERS_PER_MEDIA} trailers "
                f"(found {len(youtube_urls)} available)"
            )

        trailers_dir = tvshow_path / "trailers"
        tvshow_name = tvshow_path.name
        downloaded_paths = []

        for idx, url in enumerate(urls_to_download, start=1):
            filename = f"trailer #{idx}"
            downloaded_path = self.download(url, trailers_dir, filename)
            if downloaded_path:
                downloaded_paths.append(downloaded_path)

        self.logger.info(
            f"Downloaded {len(downloaded_paths)}/{len(urls_to_download)}"
            f" trailers for: {tvshow_name}"
        )
        return downloaded_paths
