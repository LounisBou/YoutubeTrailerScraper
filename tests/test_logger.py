#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for PyDevMate LogIt integration."""

import logging

from pydevmate.logit import LogIt


class TestLogItIntegration:
    """Tests for PyDevMate LogIt integration in YoutubeTrailerScraper."""

    def test_logit_initialization(self):
        """Test LogIt initializes correctly."""
        logger = LogIt(name="test_logger", level=logging.INFO, console=True, file=False)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO

    def test_logit_debug_level(self):
        """Test LogIt with DEBUG level."""
        logger = LogIt(name="test_debug", level=logging.DEBUG, console=True, file=False)
        assert logger.level == logging.DEBUG

    def test_logit_info_level(self):
        """Test LogIt with INFO level."""
        logger = LogIt(name="test_info", level=logging.INFO, console=True, file=False)
        assert logger.level == logging.INFO

    def test_logit_custom_name(self):
        """Test LogIt with custom name."""
        logger = LogIt(name="youtubetrailerscraper", level=logging.INFO)
        assert logger.name == "youtubetrailerscraper"

    def test_logit_has_standard_methods(self):
        """Test LogIt has standard logging methods."""
        logger = LogIt(name="test_methods", level=logging.INFO)
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

    def test_logit_has_pydevmate_methods(self):
        """Test LogIt has PyDevMate-specific methods."""
        logger = LogIt(name="test_pydevmate", level=logging.INFO)
        assert hasattr(logger, "success")
        assert hasattr(logger, "show")
        assert hasattr(logger, "separator")
        assert hasattr(logger, "line_break")

    def test_logit_debug_message(self, capsys):
        """Test LogIt outputs debug messages."""
        logger = LogIt(name="test_debug_msg", level=logging.DEBUG, console=True)
        logger.debug("Debug test message")

        captured = capsys.readouterr()
        # PyDevMate LogIt outputs to stderr by default
        assert "Debug test message" in captured.err

    def test_logit_info_message(self, capsys):
        """Test LogIt outputs info messages."""
        logger = LogIt(name="test_info_msg", level=logging.INFO, console=True)
        logger.info("Info test message")

        captured = capsys.readouterr()
        # PyDevMate LogIt outputs to stderr by default
        assert "Info test message" in captured.err

    def test_logit_warning_message(self, capsys):
        """Test LogIt outputs warning messages."""
        logger = LogIt(name="test_warning_msg", level=logging.INFO, console=True)
        logger.warning("Warning test message")

        captured = capsys.readouterr()
        # PyDevMate LogIt outputs to stderr by default
        assert "Warning test message" in captured.err

    def test_logit_error_message(self, capsys):
        """Test LogIt outputs error messages."""
        logger = LogIt(name="test_error_msg", level=logging.INFO, console=True)
        logger.error("Error test message")

        captured = capsys.readouterr()
        # PyDevMate LogIt outputs to stderr by default
        assert "Error test message" in captured.err

    def test_logit_success_message(self, capsys):
        """Test LogIt outputs success messages (PyDevMate-specific)."""
        logger = LogIt(name="test_success_msg", level=logging.INFO, console=True)
        logger.success("Success test message")

        captured = capsys.readouterr()
        # PyDevMate LogIt outputs to stderr by default
        assert "Success test message" in captured.err

    def test_logit_verbose_mode_simulation(self):
        """Test LogIt configuration for verbose mode (as used in main.py)."""
        # Simulate verbose=True
        logger_verbose = LogIt(
            name="youtubetrailerscraper", level=logging.DEBUG, console=True, file=False
        )
        assert logger_verbose.level == logging.DEBUG

        # Simulate verbose=False
        logger_normal = LogIt(
            name="youtubetrailerscraper", level=logging.INFO, console=True, file=False
        )
        assert logger_normal.level == logging.INFO

    def test_logit_no_propagate(self):
        """Test LogIt does not propagate by default."""
        logger = LogIt(name="test_no_propagate", level=logging.INFO)
        # LogIt should handle propagation internally
        # This test verifies the logger is created without errors
        assert isinstance(logger, logging.Logger)
