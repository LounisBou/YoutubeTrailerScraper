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
from .moviescanner import MovieScanner
from .tmdbsearchengine import TMDBSearchEngine
from .tvshowscanner import TVShowScanner
from .youtubedownloader import YoutubeDownloader
from .youtubesearchengine import YoutubeSearchEngine
from .youtubetrailerscraper import YoutubeTrailerScraper

__all__ = [
    "YoutubeTrailerScraper",
    "TMDBSearchEngine",
    "YoutubeSearchEngine",
    "YoutubeDownloader",
    "MovieScanner",
    "TVShowScanner",
]
