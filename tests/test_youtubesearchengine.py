#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for YoutubeSearchEngine class."""

import pytest

from youtubetrailerscraper.youtubesearchengine import YoutubeSearchEngine


class TestYoutubeSearchEngineInit:
    """Tests for YoutubeSearchEngine initialization."""

    def test_default_initialization(self):
        """Test YoutubeSearchEngine initializes correctly."""
        engine = YoutubeSearchEngine()
        assert engine is not None


class TestYoutubeSearchEngineSearch:
    """Tests for search method."""

    def test_search_returns_empty_list(self):
        """Test search returns empty list (skeleton implementation)."""
        engine = YoutubeSearchEngine()
        # Skeleton implementation returns empty list
        results = engine.search("Breaking Bad 2008 trailer")
        assert results == []
        assert isinstance(results, list)

    def test_search_with_movie_query(self):
        """Test search with movie query (skeleton implementation)."""
        engine = YoutubeSearchEngine()
        results = engine.search("The Matrix 1999 bande annonce")
        assert results == []
        assert isinstance(results, list)


class TestYoutubeSearchEngineGetVideoInfo:
    """Tests for get_video_info method."""

    def test_get_video_info_returns_empty_dict(self):
        """Test get_video_info returns empty dict (skeleton implementation)."""
        engine = YoutubeSearchEngine()
        # Skeleton implementation returns empty dict
        result = engine.get_video_info("dQw4w9WgXcQ")
        assert result == {}
        assert isinstance(result, dict)

    def test_get_video_info_with_valid_id(self):
        """Test get_video_info with valid video ID (skeleton implementation)."""
        engine = YoutubeSearchEngine()
        result = engine.get_video_info("test123")
        assert result == {}
        assert isinstance(result, dict)
