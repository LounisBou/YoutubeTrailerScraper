#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tmdbsearchengine.py

Description:
    Make TMDB searches and return results

Usage:
    from tmdbsearchengine import TMDBSearchEngine

    # Usage example:

Requirements:

References:

"""

from __future__ import annotations


class TMDBSearchEngine:  # pylint: disable=too-few-public-methods
    """Make video searches via TMDB API and return results"""

    def __init__(self):
        """Initialize TMDBSearchEngine"""

    def search(self, query: str) -> list[str]:  # pylint: disable=unused-argument
        """
        Search for videos trailer from youtube on TMDB API

        Arguments:
            query (str): Search query string
        Returns:
            list[str]: List of youtube videos URLs
        """
        return []
