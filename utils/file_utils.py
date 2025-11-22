"""
File operation utilities for NovelTuner tools
"""

import os
import shutil
from pathlib import Path
from typing import List, Iterator, Optional, Set


def get_files_to_process(
    input_path: str,
    recursive: bool = False,
    file_extensions: Optional[Set[str]] = None
) -> Iterator[Path]:
    """
    Get list of files to process based on input path and criteria

    Args:
        input_path: Path to file or directory
        recursive: Whether to process subdirectories recursively
        file_extensions: Set of file extensions to include (without dots)

    Yields:
        Path objects for files to process
    """
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if path.is_file():
        # Single file
        if file_extensions is None or path.suffix.lower()[1:] in file_extensions:
            yield path
    elif path.is_dir():
        # Directory
        if recursive:
            # Walk through all subdirectories
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    if file_extensions is None or file_path.suffix.lower()[1:] in file_extensions:
                        yield file_path
        else:
            # Only top-level files
            for file_path in path.iterdir():
                if file_path.is_file():
                    if file_extensions is None or file_path.suffix.lower()[1:] in file_extensions:
                        yield file_path


def ensure_output_dir(output_path: str, input_path: str = None) -> str:
    """
    Ensure output directory exists and return appropriate output path

    Args:
        output_path: Desired output path (file or directory)
        input_path: Original input path for context

    Returns:
        Resolved output path
    """
    if output_path:
        output_path_obj = Path(output_path)
        if output_path_obj.suffix:  # It's a file path
            # Ensure parent directory exists
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        else:  # It's a directory path
            output_path_obj.mkdir(parents=True, exist_ok=True)
        return str(output_path_obj)
    else:
        # If no output specified, use input path (overwrite)
        return input_path


def safe_write_file(file_path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    Safely write content to file with proper error handling

    Args:
        file_path: Path to write to
        content: Content to write
        encoding: File encoding
    """
    try:
        # Ensure parent directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(file_path, 'w', encoding=encoding, newline='') as f:
            f.write(content)

    except Exception as e:
        raise IOError(f"Failed to write file {file_path}: {e}")


def get_output_file_path(
    input_file: Path,
    output_dir: Optional[str] = None,
    suffix: Optional[str] = None
) -> str:
    """
    Generate output file path based on input file and parameters

    Args:
        input_file: Input file path
        output_dir: Output directory (if None, use input file's directory)
        suffix: Optional suffix to add to filename before extension

    Returns:
        Generated output file path
    """
    if output_dir:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        output_name = input_file.name
    else:
        output_name = input_file.name
        output_dir_path = input_file.parent

    # Add suffix if provided
    if suffix:
        stem = input_file.stem
        extension = input_file.suffix
        output_name = f"{stem}{suffix}{extension}"

    return str(output_dir_path / output_name)


def copy_file_preserving_metadata(src: str, dst: str) -> None:
    """
    Copy file preserving metadata (timestamps, permissions)

    Args:
        src: Source file path
        dst: Destination file path
    """
    shutil.copy2(src, dst)


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes

    Args:
        file_path: Path to file

    Returns:
        File size in bytes
    """
    return Path(file_path).stat().st_size


def is_text_file(file_path: str, max_bytes: int = 8192) -> bool:
    """
    Check if file appears to be a text file

    Args:
        file_path: Path to file
        max_bytes: Maximum bytes to check

    Returns:
        True if file appears to be text
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(max_bytes)
            # Check for null bytes (common in binary files)
            return b'\x00' not in chunk
    except Exception:
        return False