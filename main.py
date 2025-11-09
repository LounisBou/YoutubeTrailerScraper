#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for YoutubeTrailerScraper.

CLI:
  python main.py [options]

"""
from __future__ import annotations

import sys
import traceback

from commandlinehelper import (
    ERROR,
    INFO,
    SUCCESS,
    WARNING,
    check_args,
    format_scan_results,
    parse_args,
    print_message,
    set_default_args_values,
)
from src.youtubetrailerscraper import YoutubeTrailerScraper
from src.youtubetrailerscraper.logger import setup_logger


def _parse_and_validate_args():
    """Parse and validate command-line arguments.

    Returns:
        Parsed and validated arguments.

    Raises:
        SystemExit: If parsing or validation fails (exits with code 2).
    """
    # Parse arguments
    try:
        args = parse_args()
    except SystemExit:
        print_message("Failed to parse arguments.", INFO)
        sys.exit(2)

    # Set default values and validate args
    try:
        args = set_default_args_values(args)
    except ValueError as e:
        print_message(f"Argument error: {e}", WARNING)
        sys.exit(2)

    try:
        check_args(args)
    except (FileNotFoundError, ValueError) as e:
        print_message(f"Argument error: {e}", ERROR)
        sys.exit(2)

    return args


def _load_scraper(verbose: bool, use_smb: bool):
    """Load and initialize the YoutubeTrailerScraper.

    Args:
        verbose: Whether to print verbose output.
        use_smb: Whether to use SMB mount point as prefix for paths.

    Returns:
        Tuple of (YoutubeTrailerScraper instance, logger instance).

    Raises:
        SystemExit: If configuration loading fails (exits with code 2).
    """
    try:
        print_message("Loading environment configuration...", INFO)

        # Set up logger for the scraper
        logger = setup_logger(verbose=verbose)

        # Create scraper with logger
        scraper = YoutubeTrailerScraper(use_smb=use_smb, logger=logger)

        print_message("Configuration loaded successfully.", SUCCESS)

        if verbose:
            smb_status = (
                f"{scraper.smb_mount_point} (enabled)"
                if scraper.use_smb_mount
                else (scraper.smb_mount_point or "Not configured")
            )
            print_message(
                f"Details:\n"
                f"  - TMDB API configured: {bool(scraper.tmdb_api_key)}\n"
                f"  - Movies paths: {len(scraper.movies_paths)}\n"
                f"  - TV shows paths: {len(scraper.tvshows_paths)}\n"
                f"  - SMB mount: {smb_status}",
                INFO,
            )

        return scraper, logger

    except FileNotFoundError as e:
        print_message(f"Configuration error: {e}", ERROR)
        sys.exit(2)
    except ValueError as e:
        print_message(f"Configuration error: {e}", ERROR)
        sys.exit(2)


def _scan_for_missing_trailers(scraper, use_sample: bool = False):
    """Scan for movies and TV shows without trailers.

    Args:
        scraper: YoutubeTrailerScraper instance.
        use_sample: If True, use sample mode (limit to SCAN_SAMPLE_SIZE).

    Returns:
        Tuple of (movies_without_trailers, tvshows_without_trailers).
    """
    # Scan for movies without trailers (logger handles verbose output)
    print_message("Starting movie scan...", INFO)
    movies_without_trailers = scraper.scan_for_movies_without_trailers(use_sample=use_sample)

    # Scan for TV shows without trailers (logger handles verbose output)
    print_message("Starting TV show scan...", INFO)
    tvshows_without_trailers = scraper.scan_for_tvshows_without_trailers(use_sample=use_sample)

    return movies_without_trailers, tvshows_without_trailers


def _display_scan_results(movies_without_trailers, tvshows_without_trailers, verbose: bool):
    """Display scan results and summary.

    Args:
        movies_without_trailers: List of movie directories without trailers.
        tvshows_without_trailers: List of TV show directories without trailers.
        verbose: If True, show full paths in output.
    """
    # Display results
    movies_result = format_scan_results(
        "Movies Without Trailers", movies_without_trailers, verbose=verbose
    )
    print_message(movies_result, INFO)

    tvshows_result = format_scan_results(
        "TV Shows Without Trailers", tvshows_without_trailers, verbose=verbose
    )
    print_message(tvshows_result, INFO)

    # Summary
    total_missing = len(movies_without_trailers) + len(tvshows_without_trailers)
    if total_missing == 0:
        print_message("\n✓ All media have trailers!", SUCCESS)
    else:
        print_message(f"\n⚠ Scan complete: {total_missing} items missing trailers", WARNING)


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

    try:
        # Load scraper configuration
        scraper, _ = _load_scraper(args.verbose, args.use_smb)

        # Clear cache if requested
        if args.clear_cache:
            print_message("Clearing filesystem scan cache...", INFO)
            scraper.clear_cache()
            print_message("Cache cleared successfully.", SUCCESS)

        # Show sample mode message if enabled
        if args.scan_sample:
            if scraper.scan_sample_size:
                print_message(
                    f"Sample mode enabled: scanning up to {scraper.scan_sample_size} "
                    f"movies and {scraper.scan_sample_size} TV shows",
                    INFO,
                )
            else:
                print_message(
                    "Warning: --scan-sample flag used but SCAN_SAMPLE_SIZE not set in .env",
                    WARNING,
                )

        # Scan for missing trailers
        movies_without_trailers, tvshows_without_trailers = _scan_for_missing_trailers(
            scraper, use_sample=args.scan_sample
        )

        # Display results
        _display_scan_results(movies_without_trailers, tvshows_without_trailers, args.verbose)

        # Note: Steps 2-4 (TMDB search, YouTube fallback, download) will be implemented later

    except Exception as e:  # pylint: disable=broad-except
        print_message(f"An error occurred: {e}", ERROR)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    raise SystemExit(_main())
