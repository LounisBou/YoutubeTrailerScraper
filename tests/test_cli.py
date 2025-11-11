"""Minimal CLI sanity tests using the top-level script."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def test_env_file(tmp_path):
    """Create a minimal test .env file with test movie directory."""
    # Create test directories
    movies_dir = tmp_path / "movies"
    movies_dir.mkdir()
    tvshows_dir = tmp_path / "tvshows"
    tvshows_dir.mkdir()

    # Create one fake movie WITHOUT trailer
    movie_without_trailer = movies_dir / "Test Movie (2023)"
    movie_without_trailer.mkdir()
    (movie_without_trailer / "Test Movie (2023).mp4").touch()

    # Create one fake movie WITH trailer
    movie_with_trailer = movies_dir / "Another Movie (2024)"
    movie_with_trailer.mkdir()
    (movie_with_trailer / "Another Movie (2024).mp4").touch()
    (movie_with_trailer / "Another Movie (2024)-trailer.mp4").touch()

    # Create test .env file
    env_file = tmp_path / ".env.test"
    env_content = f"""
TMDB_API_KEY=test_key_12345
TMDB_READ_ACCESS_TOKEN=test_token_67890
TMDB_API_BASE_URL=https://api.themoviedb.org/3
MOVIES_PATHS=["{movies_dir}/"]
TVSHOWS_PATHS=["{tvshows_dir}/"]
SMB_MOUNT_POINT=
USE_SMB_MOUNT=false
"""
    env_file.write_text(env_content)
    return str(env_file)


def run_cli_with_env(env_file: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI with a custom .env file.

    IMPORTANT: This function temporarily replaces .env in the project root.
    It creates a backup and restores it in a finally block to ensure safety.
    """
    # Backup original .env if it exists
    env_backup = None
    original_env = Path(".env")

    if original_env.exists():
        env_backup = Path(".env.backup_test")
        # Use shutil.copy2 to preserve metadata, then delete original
        # This is safer than rename in case of permission issues
        shutil.copy2(original_env, env_backup)
        original_env.unlink()

    try:
        # Copy test env to .env
        shutil.copy(env_file, ".env")

        # Run CLI
        result = subprocess.run(
            [sys.executable, "main.py", *args], text=True, capture_output=True, check=False
        )
        return result
    finally:
        # Always restore original .env, even if test fails
        # Delete test .env first
        if original_env.exists():
            original_env.unlink()

        # Restore backup if it exists
        if env_backup and env_backup.exists():
            shutil.copy2(env_backup, original_env)
            env_backup.unlink()  # Clean up backup file


def test_cli_help() -> None:
    """Test that CLI help option works."""
    result = subprocess.run(
        [sys.executable, "main.py", "-h"], text=True, capture_output=True, check=False
    )
    # Help text should contain usage information
    assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()


def test_cli_runs_default(test_env_file) -> None:  # pylint: disable=redefined-outer-name
    """Test that CLI runs successfully and detects missing trailer."""
    cp = run_cli_with_env(test_env_file)
    assert cp.returncode == 0

    # LogIt outputs to stderr by default
    output_lower = cp.stderr.lower()

    # Should show scan results
    assert "movies without trailers" in output_lower
    assert "tv shows without trailers" in output_lower or "tv without trailers" in output_lower

    # Should detect the one movie without trailer
    assert "found 1 movies without trailers" in output_lower
    assert "test movie (2023)" in output_lower  # Should list "Test Movie (2023)"

    # Should show TV shows section (even if empty)
    assert "found 0 tv" in output_lower or "all items have trailers" in output_lower
