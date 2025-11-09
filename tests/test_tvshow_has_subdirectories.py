#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=duplicate-code
"""Test to cover line 121 in tvshowscanner.py - _has_subdirectories_with_videos returning False."""

from youtubetrailerscraper.tvshowscanner import (  # pylint: disable=import-error
    TVShowScanner,
)


def test_has_subdirectories_with_videos_no_videos_found(tmp_path):
    """Test _has_subdirectories_with_videos returns False when no videos found."""
    scanner = TVShowScanner()
    tvshow_dir = tmp_path / "Show"
    tvshow_dir.mkdir()

    # Create subdirectories without video files
    season1 = tvshow_dir / "Season 01"
    season1.mkdir()
    (season1 / "readme.txt").touch()  # Not a video file

    season2 = tvshow_dir / "Season 02"
    season2.mkdir()
    (season2 / "info.nfo").touch()  # Not a video file

    # pylint: disable=protected-access
    result = scanner._has_subdirectories_with_videos(tvshow_dir)
    assert result is False
