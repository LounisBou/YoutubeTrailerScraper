#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YoutubeTrailerScraper - Scan tvshows and movies folders, download trailer on youtube"""

from ._about import (
    __author__,
    __description__,
    __email__,
    __license__,
    __package_name__,
    __url__,
    __version__,
)

__all__ = ["YoutubeTrailerScraper"]


def __getattr__(name: str):
    """Lazily import heavy modules when needed.

    Import of dependencies which may not yet be installed during package setup.
    Deferring the import keeps the package lightweight at import time.

    Example:
        if name == "YoutubeTrailerScraper":
            from .youtubetrailerscraper import YoutubeTrailerScraper

            return YoutubeTrailerScraper
    """

    
    raise AttributeError(name)
