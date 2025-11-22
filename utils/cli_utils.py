"""
Command-line interface utilities for NovelTuner tools
"""

import argparse
import os
from pathlib import Path
from typing import Optional


def add_common_arguments(parser: argparse.ArgumentParser, tool_specific_args: bool = True) -> argparse.ArgumentParser:
    """
    Add common command-line arguments to a parser

    Args:
        parser: ArgumentParser instance
        tool_specific_args: Whether to add tool-specific common arguments

    Returns:
        Updated ArgumentParser
    """
    # Input/Output arguments
    parser.add_argument(
        'input',
        help='Input file or directory path'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file or directory path (optional)'
    )

    # Common processing arguments
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Process subdirectories recursively'
    )

    parser.add_argument(
        '-b', '--backup',
        action='store_true',
        help='Create backup files before processing'
    )

    if tool_specific_args:
        # Add tool-specific common arguments
        parser.add_argument(
            '-f', '--file-extensions',
            help='Comma-separated list of file extensions to process (e.g., txt,md,log)'
        )

        parser.add_argument(
            '--encoding',
            help='Specify file encoding (auto-detect if not specified)'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )

    # Progress and output control
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress non-error output'
    )

    return parser


def validate_input_path(input_path: str) -> bool:
    """
    Validate that input path exists and is accessible

    Args:
        input_path: Path to validate

    Returns:
        True if valid, False otherwise
    """
    path = Path(input_path)

    if not path.exists():
        print(f"Error: Input path '{input_path}' does not exist")
        return False

    if not os.access(input_path, os.R_OK):
        print(f"Error: Input path '{input_path}' is not readable")
        return False

    return True


def validate_output_path(output_path: str, create_dir: bool = True) -> bool:
    """
    Validate that output path can be written to

    Args:
        output_path: Path to validate
        create_dir: Whether to create parent directory if it doesn't exist

    Returns:
        True if valid, False otherwise
    """
    try:
        path = Path(output_path)

        if path.suffix:  # It's a file path
            parent_dir = path.parent
        else:  # It's a directory path
            parent_dir = path

        # Check if parent directory exists or can be created
        if not parent_dir.exists():
            if create_dir:
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    print(f"Error: Cannot create output directory '{parent_dir}': {e}")
                    return False
            else:
                print(f"Error: Output directory '{parent_dir}' does not exist")
                return False

        # Check write permission
        if not os.access(str(parent_dir), os.W_OK):
            print(f"Error: Output directory '{parent_dir}' is not writable")
            return False

        return True

    except Exception as e:
        print(f"Error validating output path '{output_path}': {e}")
        return False


def parse_file_extensions(extensions_str: Optional[str]) -> Optional[set]:
    """
    Parse comma-separated file extensions string into a set

    Args:
        extensions_str: Comma-separated extensions (e.g., "txt,md,log")

    Returns:
        Set of extensions without dots, or None if empty
    """
    if not extensions_str:
        return None

    try:
        extensions = set()
        for ext in extensions_str.split(','):
            ext = ext.strip().lower()
            if ext:
                # Remove leading dot if present
                if ext.startswith('.'):
                    ext = ext[1:]
                extensions.add(ext)
        return extensions if extensions else None
    except Exception:
        return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} TB"


def create_progress_callback(total_files: int, verbose: bool = False):
    """
    Create a progress callback function for file processing

    Args:
        total_files: Total number of files to process
        verbose: Whether to show verbose progress

    Returns:
        Progress callback function
    """
    processed = 0
    failed = 0

    def progress_callback(file_path: str, success: bool, message: str = None):
        nonlocal processed, failed
        processed += 1

        if not success:
            failed += 1

        if verbose or not success:
            status = "[OK]" if success else "[FAIL]"
            if message:
                print(f"{status} [{processed}/{total_files}] {file_path}: {message}")
            else:
                print(f"{status} [{processed}/{total_files}] {file_path}")

        # Show summary when complete
        if processed == total_files:
            if failed == 0:
                print(f"[SUCCESS] All {total_files} files processed successfully")
            else:
                print(f"[COMPLETE] Processed {total_files} files, {failed} failed")

    return progress_callback