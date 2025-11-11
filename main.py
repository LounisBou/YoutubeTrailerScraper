#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for YoutubeTrailerScraper.

CLI:
  python main.py [options]

"""
from __future__ import annotations

import argparse
import logging
import sys
import traceback

from pymate.logit import LogIt

from commandlinehelper import (
    check_args,
    format_scan_results,
    parse_args,
    set_default_args_values,
)
from src.youtubetrailerscraper import YoutubeTrailerScraper


def _parse_and_validate_args(logger: LogIt | None = None) -> argparse.Namespace:
    """Parse and validate command-line arguments.

    Args:
        logger: Logger instance for logging messages.

    Returns:
        Parsed and validated arguments.

    Raises:
        SystemExit: If parsing or validation fails (exits with code 2).
    """

    if logger is None:
        logger = LogIt(name="youtubetrailerscraper", level=logging.INFO, console=True, file=False)

    # Parse arguments
    try:
        args = parse_args()
    except SystemExit:
        logger.info("Failed to parse arguments.")
        sys.exit(2)

    # Set default values and validate args
    try:
        args = set_default_args_values(args)
    except ValueError as e:
        logger.warning(f"Argument error: {e}")
        sys.exit(2)

    try:
        check_args(args)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Argument error: {e}")
        sys.exit(2)

    return args


def _load_scraper(verbose: bool, use_smb: bool, logger: LogIt | None = None):
    """Load and initialize the YoutubeTrailerScraper.

    Args:
        verbose: Whether to print verbose output.
        use_smb: Whether to use SMB mount point as prefix for paths.
        logger: Logger instance for logging messages.

    Returns:
        YoutubeTrailerScraper instance.

    Raises:
        SystemExit: If configuration loading fails (exits with code 2).
    """
    # Set up logger for the scraper using PyMate's LogIt
    if logger is None:
        log_level = logging.DEBUG if verbose else logging.INFO
        logger = LogIt(name="youtubetrailerscraper", level=log_level, console=True, file=False)

    try:
        logger.info("Loading environment configuration...")

        # Create scraper with logger
        scraper = YoutubeTrailerScraper(use_smb=use_smb, logger=logger)

        logger.success("Configuration loaded successfully.")

        if verbose:
            smb_status = (
                f"{scraper.smb_mount_point} (enabled)"
                if scraper.use_smb_mount
                else (scraper.smb_mount_point or "Not configured")
            )
            logger.info("Details:\n")
            logger.info(f"  - TMDB API configured: {bool(scraper.tmdb_api_key)}\n")
            logger.info(f"  - Movies paths: {len(scraper.movies_paths)}\n")
            logger.info(f"  - TV shows paths: {len(scraper.tvshows_paths)}\n")
            logger.info(f"  - SMB mount: {smb_status}")

        return scraper

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(2)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(2)


def _scan_for_missing_trailers(scraper, use_sample: bool = False, logger: LogIt | None = None):
    """Scan for movies and TV shows without trailers.

    Args:
        scraper: YoutubeTrailerScraper instance.
        use_sample: If True, use sample mode (limit to SCAN_SAMPLE_SIZE).
        logger: Logger instance for logging messages.

    Returns:
        Tuple of (movies_without_trailers, tvshows_without_trailers).
    """
    if logger is None:
        log_level = logging.DEBUG if use_sample else logging.INFO
        logger = LogIt(name="youtubetrailerscraper", level=log_level, console=True, file=False)

    # Scan for movies without trailers (logger handles verbose output)
    logger.info("Starting movie scan...")
    movies_without_trailers = scraper.scan_for_movies_without_trailers(use_sample=use_sample)

    # Scan for TV shows without trailers (logger handles verbose output)
    logger.info("Starting TV show scan...")
    tvshows_without_trailers = scraper.scan_for_tvshows_without_trailers(use_sample=use_sample)

    return movies_without_trailers, tvshows_without_trailers


def _display_scan_results(
    movies_without_trailers, tvshows_without_trailers, verbose: bool, logger: LogIt | None = None
):
    """Display scan results and summary.

    Args:
        movies_without_trailers: List of movie directories without trailers.
        tvshows_without_trailers: List of TV show directories without trailers.
        verbose: If True, show full paths in output.
        logger: Logger instance for logging messages.
    """

    if logger is None:
        log_level = logging.DEBUG if verbose else logging.INFO
        logger = LogIt(name="youtubetrailerscraper", level=log_level, console=True, file=False)

    # Display results
    movies_result = format_scan_results(
        "Movies Without Trailers", movies_without_trailers, verbose=verbose
    )
    logger.info(movies_result)

    tvshows_result = format_scan_results(
        "TV Shows Without Trailers", tvshows_without_trailers, verbose=verbose
    )
    logger.info(tvshows_result)

    # Summary
    total_missing = len(movies_without_trailers) + len(tvshows_without_trailers)
    if total_missing == 0:
        logger.success("\n✓ All media have trailers!")
    else:
        logger.warning(f"\n⚠ Scan complete: {total_missing} items missing trailers")


def _display_media_search_results(media_type: str, results: dict, verbose: bool, logger: LogIt):
    """Display search results for movies or TV shows.

    Args:
        media_type: Type of media ("Movie" or "TV Show").
        results: Dictionary mapping media paths to YouTube URLs.
        verbose: If True, show full URLs in output.
        logger: Logger instance for logging messages.

    Returns:
        Number of items found.
    """
    logger.info(f"\n{'-' * 44}")
    logger.info(f"{media_type} Search Results:")
    logger.info(f"{'-' * 44}")

    for media_path, youtube_urls in results.items():
        media_name = media_path.name if hasattr(media_path, "name") else str(media_path)
        if youtube_urls:
            logger.success(f"✓ {media_name}")
            for idx, url in enumerate(youtube_urls, 1):
                if verbose:
                    logger.info(f"    {idx}. {url}")
                else:
                    # Extract video ID for shorter display
                    video_id = url.split("=")[-1] if "=" in url else url
                    logger.info(f"    {idx}. youtube.com/watch?v={video_id}")
        else:
            logger.warning(f"✗ {media_name} - No TMDB trailers found")

    items_found = sum(1 for urls in results.values() if urls)
    return items_found


def _search_movies_on_tmdb(scraper, movies_without_trailers, verbose: bool, logger: LogIt):
    """Search TMDB for movie trailers.

    Args:
        scraper: YoutubeTrailerScraper instance.
        movies_without_trailers: List of movie directories without trailers.
        verbose: If True, show full URLs in output.
        logger: Logger instance for logging messages.

    Returns:
        Tuple of (movie_results dict, movies_found count).
    """
    if not movies_without_trailers:
        logger.info("No movies to search (all movies have trailers)")
        return {}, 0

    logger.info("Searching TMDB for movie trailers...")
    movie_results = scraper.search_trailers_for_movies(movies_without_trailers)
    movies_found = _display_media_search_results("Movie", movie_results, verbose, logger)
    logger.info(f"\n  Movies: {movies_found}/{len(movies_without_trailers)} found on TMDB")
    return movie_results, movies_found


def _search_tvshows_on_tmdb(scraper, tvshows_without_trailers, verbose: bool, logger: LogIt):
    """Search TMDB for TV show trailers.

    Args:
        scraper: YoutubeTrailerScraper instance.
        tvshows_without_trailers: List of TV show directories without trailers.
        verbose: If True, show full URLs in output.
        logger: Logger instance for logging messages.

    Returns:
        Tuple of (tvshow_results dict, tvshows_found count).
    """
    if not tvshows_without_trailers:
        logger.info("\nNo TV shows to search (all TV shows have trailers)")
        return {}, 0

    logger.info("\nSearching TMDB for TV show trailers...")
    tvshow_results = scraper.search_trailers_for_tvshows(tvshows_without_trailers)
    tvshows_found = _display_media_search_results("TV Show", tvshow_results, verbose, logger)
    logger.info(f"\n  TV Shows: {tvshows_found}/{len(tvshows_without_trailers)} found on TMDB")
    return tvshow_results, tvshows_found


def _display_media_download_results(media_type: str, results: dict, verbose: bool, logger: LogIt):
    """Display download results for movies or TV shows.

    Args:
        media_type: Type of media ("Movie" or "TV Show").
        results: Dictionary mapping media paths to downloaded file paths.
        verbose: If True, show full file paths in output.
        logger: Logger instance for logging messages.

    Returns:
        Number of items downloaded successfully.
    """
    logger.info(f"\n{'-' * 44}")
    logger.info(f"{media_type} Download Results:")
    logger.info(f"{'-' * 44}")

    for media_path, downloaded_paths in results.items():
        media_name = media_path.name if hasattr(media_path, "name") else str(media_path)
        if downloaded_paths:
            logger.success(f"✓ {media_name} - {len(downloaded_paths)} trailer(s) downloaded")
            if verbose:
                for path in downloaded_paths:
                    logger.info(f"    → {path}")
        else:
            logger.warning(f"✗ {media_name} - Download failed or skipped")

    items_downloaded = sum(1 for paths in results.values() if paths)
    return items_downloaded


def _download_and_display_trailers(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    scraper,
    movie_results: dict,
    tvshow_results: dict,
    total_found: int,
    verbose: bool,
    logger: LogIt,
):
    """Download trailers and display results.

    Args:
        scraper: YoutubeTrailerScraper instance.
        movie_results: Dictionary mapping movie paths to YouTube URLs.
        tvshow_results: Dictionary mapping TV show paths to YouTube URLs.
        total_found: Total number of items with trailers found.
        verbose: If True, show full file paths in output.
        logger: Logger instance for logging messages.
    """
    logger.info(f"\n{'=' * 60}")
    logger.info("Downloading Trailers")
    logger.info(f"{'=' * 60}\n")

    movies_downloaded = 0
    tvshows_downloaded = 0

    # Download movie trailers
    if movie_results:
        movie_downloads = scraper.download_trailers_for_movies(movie_results)
        movies_downloaded = _display_media_download_results(
            "Movie", movie_downloads, verbose, logger
        )
        logger.info(f"\n  Movies: {movies_downloaded}/{len(movie_results)} downloaded")

    # Download TV show trailers
    if tvshow_results:
        tvshow_downloads = scraper.download_trailers_for_tvshows(tvshow_results)
        tvshows_downloaded = _display_media_download_results(
            "TV Show", tvshow_downloads, verbose, logger
        )
        logger.info(f"\n  TV Shows: {tvshows_downloaded}/{len(tvshow_results)} downloaded")

    # Overall download summary
    total_downloads = movies_downloaded + tvshows_downloaded
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Download Summary: {total_downloads}/{total_found} items downloaded")
    logger.info(f"{'=' * 60}")


def _search_and_display_tmdb_results(
    scraper,
    movies_without_trailers,
    tvshows_without_trailers,
    verbose: bool,
    logger: LogIt | None = None,
):
    """Search TMDB for trailers and display results.

    Args:
        scraper: YoutubeTrailerScraper instance.
        movies_without_trailers: List of movie directories without trailers.
        tvshows_without_trailers: List of TV show directories without trailers.
        verbose: If True, show full URLs in output.
        logger: Logger instance for logging messages.

    Returns:
        Tuple of (movie_results, tvshow_results, total_found) where movie_results
        and tvshow_results are dictionaries mapping paths to YouTube URLs.
    """
    if logger is None:
        log_level = logging.DEBUG if verbose else logging.INFO
        logger = LogIt(name="youtubetrailerscraper", level=log_level, console=True, file=False)

    logger.info(f"\n{'=' * 60}")
    logger.info("TMDB Integration Test - Step 4a")
    logger.info(f"{'=' * 60}\n")

    # Search for movie trailers
    movie_results, movies_found = _search_movies_on_tmdb(
        scraper, movies_without_trailers, verbose, logger
    )

    # Search for TV show trailers
    tvshow_results, tvshows_found = _search_tvshows_on_tmdb(
        scraper, tvshows_without_trailers, verbose, logger
    )

    # Overall search summary
    total_searched = len(movies_without_trailers) + len(tvshows_without_trailers)
    total_found = movies_found + tvshows_found

    logger.info(f"\n{'=' * 60}")
    logger.info(f"TMDB Search Summary: {total_found}/{total_searched} items found trailers")
    logger.info(f"{'=' * 60}")

    return movie_results, tvshow_results, total_found


def _main() -> int:
    """Command-line interface main function.

    Exit codes:
        0: Success
        1: General error
        2: Argument error

    Raises:
        SystemExit: On any error.
    """

    # Parse and validate arguments
    args = _parse_and_validate_args()

    # Set up logger for the scraper using PyMate's LogIt
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = LogIt(
        name="youtubetrailerscraper",
        level=log_level,
        console=True,
        file=False,
        format="%(message)s",
    )

    try:
        # Load scraper configuration
        scraper = _load_scraper(args.verbose, args.use_smb, logger=logger)

        # Clear cache if requested
        if args.clear_cache:
            logger.info("Clearing filesystem scan cache...")
            scraper.clear_cache()
            logger.success("Cache cleared successfully.")

        # Show sample mode message if enabled
        if args.scan_sample:
            if scraper.scan_sample_size:
                logger.warning(
                    f"Sample mode enabled: scanning up to {scraper.scan_sample_size} movies "
                    f"and {scraper.scan_sample_size} TV shows"
                )
            else:
                logger.error("Error: --scan-sample flag used but SCAN_SAMPLE_SIZE not set in .env")

        # Scan for missing trailers
        movies_without_trailers, tvshows_without_trailers = _scan_for_missing_trailers(
            scraper, use_sample=args.scan_sample, logger=logger
        )

        # Display scan results
        _display_scan_results(
            movies_without_trailers, tvshows_without_trailers, args.verbose, logger=logger
        )

        # Automatically search TMDB for trailers if there are missing trailers (Step 4a)
        if movies_without_trailers or tvshows_without_trailers:
            movie_results, tvshow_results, total_found = _search_and_display_tmdb_results(
                scraper,
                movies_without_trailers,
                tvshows_without_trailers,
                args.verbose,
                logger=logger,
            )

            # Download trailers if any were found
            if movie_results or tvshow_results:
                _download_and_display_trailers(
                    scraper, movie_results, tvshow_results, total_found, args.verbose, logger
                )
            else:
                logger.info("\nNo trailers found to download.")

    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"An error occurred: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    raise SystemExit(_main())
