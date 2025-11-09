#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Colored logger for YoutubeTrailerScraper.

Provides a colored console logger with support for verbose mode.
Respects NO_COLOR and FORCE_COLOR environment variables.
"""

from __future__ import annotations

import logging
import os
import sys


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output.

    Adds ANSI color codes to log messages based on log level.
    Respects NO_COLOR and FORCE_COLOR environment variables.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, *args, **kwargs):
        """Initialize colored formatter.

        Detects whether colors should be used based on environment variables
        and terminal detection.
        """
        super().__init__(*args, **kwargs)
        self.use_colors = self._should_use_colors()

    def _should_use_colors(self) -> bool:
        """Determine if colors should be used in output.

        Returns:
            True if colors should be used, False otherwise.

        Environment variables:
            NO_COLOR: If set (any value), disables colors
            FORCE_COLOR: If set (any value), forces colors even if not a TTY
        """
        # NO_COLOR takes precedence
        if os.getenv("NO_COLOR"):
            return False

        # FORCE_COLOR forces colors
        if os.getenv("FORCE_COLOR"):
            return True

        # Default: use colors if stdout is a TTY
        return sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record to format.

        Returns:
            Formatted log message with color codes (if colors are enabled).
        """
        if self.use_colors:
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            record.msg = f"{color}{record.msg}{self.RESET}"

        return super().format(record)


def setup_logger(name: str = "youtubetrailerscraper", verbose: bool = False) -> logging.Logger:
    """Set up and configure a logger with colored output.

    Args:
        name: Logger name. Defaults to 'youtubetrailerscraper'.
        verbose: If True, set log level to DEBUG. Otherwise, set to INFO.

    Returns:
        Configured logger instance.

    Example:
        >>> logger = setup_logger(verbose=True)
        >>> logger.debug("Debug message")
        >>> logger.info("Info message")
        >>> logger.warning("Warning message")
        >>> logger.error("Error message")
    """
    logger = logging.getLogger(name)

    # Set log level based on verbose flag
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Create colored formatter
    formatter = ColoredFormatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger
