"""Minimal import sanity tests for the generated package."""

import importlib


def test_package_imports() -> None:
    """Test that the package can be imported and has version attribute."""
    mod = importlib.import_module("youtubetrailerscraper")
    assert hasattr(mod, "__version__")
