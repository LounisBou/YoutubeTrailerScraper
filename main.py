#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for YoutubeTrailerScraper.

CLI:
  python main.py [options]
    
"""
from __future__ import annotations
import sys

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

    # Main functionality placeholder
    print_message("This is a placeholder for the main functionality.", SUCCESS)
    sys.exit(0)

if __name__ == "__main__":
    raise SystemExit(_main())
