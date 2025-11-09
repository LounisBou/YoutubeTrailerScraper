#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for TMDBSearchEngine class."""

import pytest

from youtubetrailerscraper.tmdbsearchengine import TMDBSearchEngine


class TestTMDBSearchEngineInit:
    """Tests for TMDBSearchEngine initialization."""

    def test_default_initialization(self):
        """Test TMDBSearchEngine initializes correctly."""
        engine = TMDBSearchEngine()
        assert engine is not None


class TestTMDBSearchEngineSearch:
    """Tests for search method."""

    def test_search_returns_empty_list(self):
        """Test search returns empty list (skeleton implementation)."""
        engine = TMDBSearchEngine()
        # Skeleton implementation returns empty list
        results = engine.search("Breaking Bad 2008 trailer")
        assert results == []
        assert isinstance(results, list)

    def test_search_with_movie(self):
        """Test search with movie query (skeleton implementation)."""
        engine = TMDBSearchEngine()
        results = engine.search("The Matrix 1999 trailer")
        assert results == []
        assert isinstance(results, list)

    def test_search_with_empty_string(self):
        """Test search with empty string (skeleton implementation)."""
        engine = TMDBSearchEngine()
        results = engine.search("")
        assert results == []
        assert isinstance(results, list)
