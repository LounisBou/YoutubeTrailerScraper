#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temporary investigation script to test TMDB search with French titles.
This file is for debugging only and will not be kept.
"""

import os
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

from src.youtubetrailerscraper.tmdbsearchengine import TMDBSearchEngine


def remove_accents(text: str) -> str:
    """Remove accents from text using Unicode normalization.

    Args:
        text: Text with potential accents

    Returns:
        Text without accents

    Example:
        >>> remove_accents("Guêpe")
        'Guepe'
    """
    # Normalize to NFD (decomposed form) and filter out combining characters
    nfd = unicodedata.normalize("NFD", text)
    return "".join(char for char in nfd if unicodedata.category(char) != "Mn")


def remove_special_chars(text: str) -> str:
    """Remove or replace special characters.

    Args:
        text: Text with potential special characters

    Returns:
        Text with special characters removed/replaced
    """
    # Replace common special characters
    text = text.replace("&", "and")
    text = text.replace(":", "")
    # Remove remaining non-alphanumeric except spaces
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    # Clean up extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def test_search_strategies(engine: TMDBSearchEngine, title: str, year: int):
    """Test different search strategies for a given title.

    Args:
        engine: TMDBSearchEngine instance
        title: Movie title to search
        year: Release year
    """
    print(f"\n{'=' * 80}")
    print(f"Testing: {title} ({year})")
    print(f"{'=' * 80}")

    strategies = [
        ("Original", title),
        ("Without accents", remove_accents(title)),
        ("Without special chars", remove_special_chars(title)),
        ("Without accents + special chars", remove_special_chars(remove_accents(title))),
    ]

    for strategy_name, modified_title in strategies:
        print(f"\n[{strategy_name}]")
        print(f"  Query: '{modified_title}' (year={year})")

        try:
            results = engine.search_movie(modified_title, year)

            if results:
                print(f"  ✓ Found {len(results)} trailer(s)")
                for idx, url in enumerate(results, 1):
                    print(f"    {idx}. {url}")
            else:
                print(f"  ✗ No trailers found")

        except Exception as e:
            print(f"  ✗ Error: {e}")


def main():
    """Main investigation function."""
    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print(f"Error: .env file not found at {env_file}")
        return

    load_dotenv(env_file)

    # Get TMDB API key
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print("Error: TMDB_API_KEY not found in .env")
        return

    print(f"Using TMDB API key: {api_key[:8]}...")

    # Initialize search engine with multi-language support
    # Try French first, then English
    engine = TMDBSearchEngine(api_key=api_key, languages=["fr-FR", "en-US"])

    # Test cases from user
    test_cases = [
        ("Ant-Man et la Guêpe Quantumania", 2023),
        ("Astérix & Obélix Au service de Sa Majesté", 2012),
        ("Astérix & Obélix contre César", 1999),
    ]

    print("\n" + "=" * 80)
    print("TMDB French Title Investigation")
    print("=" * 80)
    print("\nTesting different search strategies:")
    print("  1. Original title (as-is)")
    print("  2. Without accents (é→e, ê→e, etc.)")
    print("  3. Without special chars (&→and, remove :, etc.)")
    print("  4. Without accents + without special chars")

    for title, year in test_cases:
        test_search_strategies(engine, title, year)

    print(f"\n{'=' * 80}")
    print("Investigation complete!")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
