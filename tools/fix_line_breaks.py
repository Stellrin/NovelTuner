#!/usr/bin/env python3
"""
Fix Line Breaks Tool for NovelTuner
修复中文文本中的异常换行问题

This tool detects and merges lines where Chinese characters are incorrectly split,
handling continuous multi-line merging while respecting punctuation marks.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional, Set

# Import utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    get_files_to_process, ensure_output_dir, safe_write_file,
    detect_encoding, read_file_with_encoding, create_backup, should_create_backup,
    add_common_arguments, validate_input_path, parse_file_extensions, create_progress_callback
)


def get_description() -> str:
    """Return tool description"""
    return "Fix abnormal line breaks in Chinese text"


def get_parser() -> argparse.ArgumentParser:
    """Return configured ArgumentParser for this tool"""
    parser = argparse.ArgumentParser(
        prog="fix_line_breaks",
        description=get_description(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python novel_tuner.py fix_line_breaks input.txt
  python novel_tuner.py fix_line_breaks input.txt -o output.txt
  python novel_tuner.py fix_line_breaks novel_dir -r -f txt,md
  python novel_tuner.py fix_line_breaks input.txt -b -v
        """
    )

    # Add common arguments
    add_common_arguments(parser, tool_specific_args=False)

    # Tool-specific arguments
    parser.add_argument(
        '-f', '--file-extensions',
        default='txt,md,log',
        help='File extensions to process (default: txt,md,log)'
    )

    parser.add_argument(
        '--punctuation',
        help='Custom punctuation marks to respect (default: Chinese punctuation)'
    )

    return parser


def fix_line_breaks_in_text(text: str, custom_punctuation: Optional[str] = None) -> str:
    """
    Fix line breaks in Chinese text

    Args:
        text: Input text with potential line break issues
        custom_punctuation: Custom punctuation marks to respect

    Returns:
        Text with fixed line breaks
    """
    # Default Chinese punctuation that indicates sentence endings
    default_punctuation = '。！？：；」』】）\"\"'''
    punctuation = custom_punctuation or default_punctuation

    # Split text into lines
    lines = text.split('\n')
    fixed_lines = []
    current_paragraph = ""

    for i, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines
        if not line:
            if current_paragraph:
                fixed_lines.append(current_paragraph)
                current_paragraph = ""
            fixed_lines.append("")
            continue

        # Check if line ends with punctuation
        ends_with_punctuation = line and line[-1] in punctuation

        # Check if next line starts with lowercase (indicating continuation)
        next_line_starts_lowercase = False
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and next_line[0].islower():
                next_line_starts_lowercase = True

        # Check if current line is very short (likely broken)
        is_short_line = len(line) < 10  # Threshold for "short" line

        # Decision logic for merging
        if ends_with_punctuation:
            # Line ends with punctuation, finish current paragraph
            if current_paragraph:
                current_paragraph += line
                fixed_lines.append(current_paragraph)
                current_paragraph = ""
            else:
                fixed_lines.append(line)
        elif is_short_line and not next_line_starts_lowercase:
            # Short line that's likely broken, merge with next
            current_paragraph += line
        else:
            # Regular line, add to current paragraph
            if current_paragraph:
                current_paragraph += line
            else:
                current_paragraph = line

    # Handle any remaining paragraph
    if current_paragraph:
        fixed_lines.append(current_paragraph)

    # Join lines back together
    return '\n'.join(fixed_lines)


def process_file(file_path: str, output_path: str, args: argparse.Namespace) -> bool:
    """
    Process a single file

    Args:
        file_path: Input file path
        output_path: Output file path
        args: Command line arguments

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read file with encoding detection
        content, encoding = read_file_with_encoding(file_path, getattr(args, 'encoding', None))

        if args.verbose:
            print(f"Processing {file_path} (encoding: {encoding})")

        # Create backup if requested
        if should_create_backup(args.backup, file_path):
            backup_path = create_backup(file_path)
            if not backup_path:
                print(f"Warning: Failed to create backup for {file_path}")

        # Fix line breaks
        fixed_content = fix_line_breaks_in_text(content, args.punctuation)

        # Write output
        safe_write_file(output_path, fixed_content, encoding)

        if args.verbose:
            print(f"Fixed line breaks: {file_path} -> {output_path}")

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main(args: argparse.Namespace) -> int:
    """
    Main function for fix_line_breaks tool

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Validate input path
    if not validate_input_path(args.input):
        return 1

    # Parse file extensions
    file_extensions = parse_file_extensions(args.file_extensions)

    # Get files to process
    try:
        files_to_process = list(get_files_to_process(args.input, args.recursive, file_extensions))
    except Exception as e:
        print(f"Error getting files to process: {e}")
        return 1

    if not files_to_process:
        print("No files found to process.")
        return 1

    if not args.quiet:
        print(f"Found {len(files_to_process)} files to process")

    # Ensure output directory
    if args.output:
        ensure_output_dir(args.output)

    # Process files
    success_count = 0
    failed_count = 0

    progress_callback = create_progress_callback(len(files_to_process), args.verbose)

    for file_path in files_to_process:
        try:
            # Determine output path
            if args.output:
                if Path(args.output).is_dir():
                    # Output is directory, preserve filename
                    output_file = str(Path(args.output) / file_path.name)
                else:
                    # Output is specific file
                    output_file = args.output
            else:
                # No output specified, overwrite input
                output_file = str(file_path)

            # Process the file
            success = process_file(str(file_path), output_file, args)

            if success:
                success_count += 1
                progress_callback(str(file_path), True)
            else:
                failed_count += 1
                progress_callback(str(file_path), False, "Processing failed")

        except Exception as e:
            failed_count += 1
            progress_callback(str(file_path), False, f"Exception: {e}")

    # Final summary
    if not args.quiet:
        print(f"\nProcessing complete: {success_count} successful, {failed_count} failed")

    return 0 if failed_count == 0 else 1


# For standalone execution
if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    sys.exit(main(args))