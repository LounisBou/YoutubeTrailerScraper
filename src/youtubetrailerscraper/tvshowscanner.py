#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tvshowscanner.py

Description:
    Scan tvshows folders, find missing trailers on pattern :
    /path/to/tvshow/trailers/trailer.mp4

Usage:
    from tvshowscanner import TVShowScanner

    # Usage example:

Requirements:

References:

"""

from __future__ import annotations

from pathlib import Path


class TVShowScanner:
    """Scan tvshows folders, find missing trailers"""

    def __init__(self):
        """Initialize TVShowScanner"""

    def scan(self, path: Path) -> list[Path]:  # pylint: disable=unused-argument
        """
        Scan for tvshows in the given path

        Parameters:
            path (Path): Path to scan for tvshows

        Returns:
            list[Path]: List of found tvshows
        """
        return []

    def find_missing_trailers(self, paths: list[Path]) -> list[Path]:  # pylint: disable=unused-argument
        """
        Find missing trailers in the given paths

        Parameters:
            paths (list[Path]): List of paths to scan for missing trailers

        Returns:
            list[Path]: List of missing trailers
        """
        return []
