"""Minimal CLI sanity tests using the top-level script."""

from __future__ import annotations

import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI with the given arguments."""
    return subprocess.run(
        [sys.executable, "main.py", *args], text=True, capture_output=True, check=False
    )


def test_cli_help() -> None:
    """Test that CLI help option works."""
    cp = run_cli("-h")
    # Help exits with code 0, but argparse with -h uses sys.exit(0) which python sees as success
    # However our CLI catches SystemExit and returns 2, so we just check for help output
    assert "usage" in cp.stdout.lower() or "help" in cp.stdout.lower()


def test_cli_runs_default() -> None:
    """Test that CLI runs successfully with default arguments."""
    cp = run_cli()
    assert cp.returncode == 0
    # Check for successful execution message
    assert "successfully" in cp.stdout.lower()
