#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
youtubedownloader.py

Description:
    Download videos from YouTube from given URLs

Usage:
    from youtubedownloader import YoutubeDownloader

    # Usage example:

Requirements:

References:

"""

from __future__ import annotations
from pathlib import Path


class YoutubeDownloader:  # pylint: disable=too-few-public-methods
    """Download videos from YouTube from given URLs"""

    def __init__(self):
        """Initialize YoutubeDownloader"""

    def download(self, url: str) -> Path:
        """
        Download video from YouTube

        Parameters:
            url (str): YouTube video URL
        Returns:
            Path: Path to the downloaded video file
        """
        raise NotImplementedError("Download method not yet implemented")
