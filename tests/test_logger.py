#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the logger module."""

import logging
import sys

from youtubetrailerscraper.logger import ColoredFormatter, setup_logger


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    def test_formatter_initialization(self):
        """Test ColoredFormatter initializes correctly."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        assert isinstance(formatter, logging.Formatter)
        assert hasattr(formatter, "use_colors")

    def test_should_use_colors_with_no_color_env(self, monkeypatch):
        """Test color detection respects NO_COLOR environment variable."""
        monkeypatch.setenv("NO_COLOR", "1")
        formatter = ColoredFormatter()
        assert formatter.use_colors is False

    def test_should_use_colors_with_force_color_env(self, monkeypatch):
        """Test color detection respects FORCE_COLOR environment variable."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.setenv("FORCE_COLOR", "1")
        formatter = ColoredFormatter()
        assert formatter.use_colors is True

    def test_should_use_colors_no_color_takes_precedence(self, monkeypatch):
        """Test NO_COLOR takes precedence over FORCE_COLOR."""
        monkeypatch.setenv("NO_COLOR", "1")
        monkeypatch.setenv("FORCE_COLOR", "1")
        formatter = ColoredFormatter()
        assert formatter.use_colors is False

    def test_should_use_colors_with_tty(self, monkeypatch):
        """Test color detection with TTY."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)

        # Mock isatty to return True
        original_isatty = sys.stdout.isatty
        sys.stdout.isatty = lambda: True

        try:
            formatter = ColoredFormatter()
            assert formatter.use_colors is True
        finally:
            sys.stdout.isatty = original_isatty

    def test_should_use_colors_without_tty(self, monkeypatch):
        """Test color detection without TTY."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)

        # Mock isatty to return False
        original_isatty = sys.stdout.isatty
        sys.stdout.isatty = lambda: False

        try:
            formatter = ColoredFormatter()
            assert formatter.use_colors is False
        finally:
            sys.stdout.isatty = original_isatty

    def test_format_with_colors_enabled(self, monkeypatch):
        """Test formatting with colors enabled."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        formatter = ColoredFormatter("%(levelname)s: %(message)s")

        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        # Should contain ANSI color codes
        assert "\033[" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted

    def test_format_without_colors(self, monkeypatch):
        """Test formatting with colors disabled."""
        monkeypatch.setenv("NO_COLOR", "1")
        formatter = ColoredFormatter("%(levelname)s: %(message)s")

        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        # Should NOT contain ANSI color codes
        assert "\033[" not in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted

    def test_format_debug_level(self, monkeypatch):
        """Test formatting DEBUG level messages."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        formatter = ColoredFormatter("%(levelname)s: %(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Debug message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        # Cyan color for DEBUG
        assert "\033[36m" in formatted
        assert "DEBUG" in formatted

    def test_format_warning_level(self, monkeypatch):
        """Test formatting WARNING level messages."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        formatter = ColoredFormatter("%(levelname)s: %(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        # Yellow color for WARNING
        assert "\033[33m" in formatted
        assert "WARNING" in formatted

    def test_format_error_level(self, monkeypatch):
        """Test formatting ERROR level messages."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        formatter = ColoredFormatter("%(levelname)s: %(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        # Red color for ERROR
        assert "\033[31m" in formatted
        assert "ERROR" in formatted

    def test_format_critical_level(self, monkeypatch):
        """Test formatting CRITICAL level messages."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        formatter = ColoredFormatter("%(levelname)s: %(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.CRITICAL,
            pathname="test.py",
            lineno=1,
            msg="Critical message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        # Magenta color for CRITICAL
        assert "\033[35m" in formatted
        assert "CRITICAL" in formatted


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_default(self):
        """Test setup_logger with default parameters."""
        logger = setup_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "youtubetrailerscraper"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert logger.propagate is False

    def test_setup_logger_custom_name(self):
        """Test setup_logger with custom name."""
        logger = setup_logger(name="custom_logger")
        assert logger.name == "custom_logger"

    def test_setup_logger_verbose_mode(self):
        """Test setup_logger with verbose mode enabled."""
        logger = setup_logger(verbose=True)
        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_setup_logger_non_verbose_mode(self):
        """Test setup_logger with verbose mode disabled."""
        logger = setup_logger(verbose=False)
        assert logger.level == logging.INFO
        assert logger.handlers[0].level == logging.INFO

    def test_setup_logger_handler_formatter(self):
        """Test setup_logger creates handler with ColoredFormatter."""
        logger = setup_logger()
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, ColoredFormatter)

    def test_setup_logger_clears_existing_handlers(self):
        """Test setup_logger clears existing handlers."""
        # First setup
        logger = setup_logger(name="test_logger_clear")
        assert len(logger.handlers) == 1

        # Second setup with same name - should clear and recreate
        logger = setup_logger(name="test_logger_clear")
        assert len(logger.handlers) == 1

    def test_setup_logger_output_to_stdout(self):
        """Test setup_logger outputs to stdout."""
        logger = setup_logger(name="test_stdout")
        handler = logger.handlers[0]
        assert handler.stream == sys.stdout

    def test_logger_debug_message(self, capsys):
        """Test logger outputs debug messages in verbose mode."""
        logger = setup_logger(name="test_debug", verbose=True)
        logger.debug("Debug test message")

        captured = capsys.readouterr()
        assert "Debug test message" in captured.out

    def test_logger_info_message(self, capsys):
        """Test logger outputs info messages."""
        logger = setup_logger(name="test_info", verbose=False)
        logger.info("Info test message")

        captured = capsys.readouterr()
        assert "Info test message" in captured.out

    def test_logger_warning_message(self, capsys):
        """Test logger outputs warning messages."""
        logger = setup_logger(name="test_warning")
        logger.warning("Warning test message")

        captured = capsys.readouterr()
        assert "Warning test message" in captured.out

    def test_logger_error_message(self, capsys):
        """Test logger outputs error messages."""
        logger = setup_logger(name="test_error")
        logger.error("Error test message")

        captured = capsys.readouterr()
        assert "Error test message" in captured.out

    def test_logger_does_not_propagate(self):
        """Test logger does not propagate to root logger."""
        logger = setup_logger(name="test_no_propagate")
        assert logger.propagate is False
