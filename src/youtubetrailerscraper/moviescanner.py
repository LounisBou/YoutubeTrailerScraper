#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
moviescanner.py

Description:
    Scan movies folders, find missing trailers on pattern :
    /path/to/movie/movie-trailer.mp4

Usage:
    from moviescanner import MovieScanner

Requirements:

References:

"""

from __future__ import annotations
from pathlib import Path


class MovieScanner:
    """Scan movies folders, find missing trailers"""

    def __init__(self):
        """Initialize MovieScanner"""

    def scan(self, path: Path) -> list[Path]:  # pylint: disable=unused-argument
        """
        Scan for movies in the given path

        Parameters:
        path (Path): Path to scan for movies
        Returns:
            list[Path]: List of found movies
        """
        return []

    def find_missing_trailers(
        self, path: Path  # pylint: disable=unused-argument
    ) -> list[Path]:
        """
        Find missing trailers in the given path

        Parameters:
            path (Path): Path to scan for missing trailers

        Returns:
            list[Path]: List of missing trailers
        """
        return []
