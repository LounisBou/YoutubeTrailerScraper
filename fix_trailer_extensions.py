#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility script to fix movie trailers missing .mp4 extension.

This script scans movie directories for trailer files that are missing the .mp4
extension and renames them to add it. Supports dry-run mode to preview changes.

Usage:
    # Dry-run mode (preview changes without applying)
    python fix_trailer_extensions.py /path/to/movies --dry-run

    # Apply changes
    python fix_trailer_extensions.py /path/to/movies

    # Multiple directories
    python fix_trailer_extensions.py /path/to/movies1 /path/to/movies2

    # Verbose output
    python fix_trailer_extensions.py /path/to/movies --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Tuple


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose (DEBUG) logging if True, otherwise INFO level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger


def is_movie_directory(directory: Path) -> bool:
    """Check if a directory appears to be a movie directory.

    A movie directory should contain at least one video file.

    Args:
        directory: Path to check.

    Returns:
        True if directory contains video files, False otherwise.
    """
    video_extensions = {".mp4", ".mkv", ".avi", ".m4v", ".mov"}
    try:
        return any(
            f.suffix.lower() in video_extensions for f in directory.iterdir() if f.is_file()
        )
    except (PermissionError, OSError):
        return False


def find_trailers_without_extension(movie_dir: Path) -> List[Path]:
    """Find trailer files in a movie directory that are missing .mp4 extension.

    Args:
        movie_dir: Path to the movie directory.

    Returns:
        List of Path objects for trailers missing .mp4 extension.
    """
    trailers_without_extension = []
    try:
        for file_path in movie_dir.iterdir():
            if not file_path.is_file():
                continue

            # Check if filename contains "trailer" (case-insensitive)
            if "trailer" in file_path.name.lower():
                # Check if it's missing .mp4 extension
                if file_path.suffix.lower() != ".mp4":
                    trailers_without_extension.append(file_path)
    except (PermissionError, OSError):
        pass

    return trailers_without_extension


def scan_directories(paths: List[Path], logger: logging.Logger) -> List[Tuple[Path, Path]]:
    """Scan directories for trailers missing .mp4 extension.

    Args:
        paths: List of base directory paths to scan.
        logger: Logger instance.

    Returns:
        List of tuples (old_path, new_path) for files that need renaming.
    """
    files_to_rename = []

    for base_path in paths:
        if not base_path.exists():
            logger.warning(f"Path does not exist: {base_path}")
            continue

        if not base_path.is_dir():
            logger.warning(f"Path is not a directory: {base_path}")
            continue

        logger.info(f"Scanning: {base_path}")

        try:
            # Iterate through subdirectories (movie folders)
            for item in base_path.iterdir():
                if not item.is_dir():
                    continue

                # Check if it's a movie directory
                if not is_movie_directory(item):
                    logger.debug(f"Skipping non-movie directory: {item.name}")
                    continue

                # Find trailers without .mp4 extension
                trailers = find_trailers_without_extension(item)
                for trailer_path in trailers:
                    new_path = trailer_path.with_suffix(".mp4")
                    files_to_rename.append((trailer_path, new_path))
                    logger.debug(f"Found: {trailer_path} -> {new_path}")

        except (PermissionError, OSError) as e:
            logger.error(f"Error scanning {base_path}: {e}")

    return files_to_rename


def rename_files(
    files_to_rename: List[Tuple[Path, Path]], dry_run: bool, logger: logging.Logger
) -> int:
    """Rename trailer files to add .mp4 extension.

    Args:
        files_to_rename: List of tuples (old_path, new_path).
        dry_run: If True, only preview changes without applying them.
        logger: Logger instance.

    Returns:
        Number of files successfully renamed (or would be renamed in dry-run mode).
    """
    renamed_count = 0

    for old_path, new_path in files_to_rename:
        if dry_run:
            logger.info(f"[DRY-RUN] Would rename: {old_path} -> {new_path.name}")
            renamed_count += 1
        else:
            try:
                old_path.rename(new_path)
                logger.info(f"Renamed: {old_path} -> {new_path.name}")
                renamed_count += 1
            except (PermissionError, OSError) as e:
                logger.error(f"Failed to rename {old_path}: {e}")

    return renamed_count


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fix movie trailers missing .mp4 extension",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes (dry-run mode)
  python fix_trailer_extensions.py /movies/disk1 --dry-run

  # Apply changes
  python fix_trailer_extensions.py /movies/disk1

  # Multiple directories with verbose output
  python fix_trailer_extensions.py /movies/disk1 /movies/disk2 --verbose
        """,
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Movie directory paths to scan")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()
    logger = setup_logging(args.verbose)

    # Scan for trailers without .mp4 extension
    logger.info("=" * 60)
    if args.dry_run:
        logger.info("DRY-RUN MODE: No files will be modified")
    logger.info("=" * 60)

    files_to_rename = scan_directories(args.paths, logger)

    if not files_to_rename:
        logger.info("No trailers found missing .mp4 extension")
        return 0

    # Display summary
    logger.info("=" * 60)
    logger.info(f"Found {len(files_to_rename)} trailer(s) to rename")
    logger.info("=" * 60)

    # Rename files
    renamed_count = rename_files(files_to_rename, args.dry_run, logger)

    # Final summary
    logger.info("=" * 60)
    if args.dry_run:
        logger.info(f"[DRY-RUN] Would rename {renamed_count} file(s)")
        logger.info("Run without --dry-run to apply changes")
    else:
        logger.info(f"Successfully renamed {renamed_count} file(s)")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
