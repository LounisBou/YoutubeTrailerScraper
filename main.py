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
    try:

        # Set up logger for the scraper using PyMate's LogIt
        if logger is None:
            log_level = logging.DEBUG if verbose else logging.INFO
            logger = LogIt(name="youtubetrailerscraper", level=log_level, console=True, file=False)

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

        # Display results
        _display_scan_results(
            movies_without_trailers, tvshows_without_trailers, args.verbose, logger=logger
        )

        # Note: Steps 2-4 (TMDB search, YouTube fallback, download) will be implemented later

    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"An error occurred: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    raise SystemExit(_main())
