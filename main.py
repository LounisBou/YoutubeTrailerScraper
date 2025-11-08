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
    parse_args,
    print_message,
    set_default_args_values,
)

from src.youtubetrailerscraper import YoutubeTrailerScraper


def _main() -> int:
    """
    Command-line interface main function.
    Exit code:
        0: Success
        1: General error
        2: Argument error
    Raises:
        SystemExit: If argument parsing fails.
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

    # Set default values and validate args
    try:
        check_args(args)
    except (FileNotFoundError, ValueError) as e:
        print_message(f"Argument error: {e}", ERROR)
        sys.exit(2)

    try:
        # Instantiate the scraper (loads .env file)
        if args.verbose:
            print_message("Loading configuration from .env file...", INFO)

        scraper = YoutubeTrailerScraper()

        if args.verbose:
            print_message(
                f"Configuration loaded successfully:\n"
                f"  - TMDB API configured: {bool(scraper.tmdb_api_key)}\n"
                f"  - Movies paths: {len(scraper.movies_paths)}\n"
                f"  - TV shows paths: {len(scraper.tvshows_paths)}\n"
                f"  - SMB mount: {scraper.smb_mount_point or 'Not configured'}",
                INFO,
            )

        # pylint: disable=fixme
        # TODO: Implement workflow
        # 1. Scan for movies/TV shows without trailers
        # 2. Search TMDB for trailers
        # 3. Fallback to YouTube search if needed
        # 4. Download trailers

        print_message("YoutubeTrailerScraper executed successfully.", SUCCESS)

    except FileNotFoundError as e:
        print_message(f"Configuration error: {e}", ERROR)
        sys.exit(2)
    except ValueError as e:
        print_message(f"Configuration error: {e}", ERROR)
        sys.exit(2)
    except Exception as e:  # pylint: disable=broad-except
        print_message(f"An error occurred: {e}", ERROR)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    raise SystemExit(_main())
