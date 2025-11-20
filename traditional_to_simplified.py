#!/usr/bin/env python3
"""
Traditional Chinese to Simplified Chinese Converter
Command-line tool that converts traditional Chinese characters to simplified Chinese in text files
"""

import argparse
import sys
import os
from pathlib import Path

try:
    import opencc
except ImportError:
    print("Error: opencc-python-reimplemented library is required")
    print("Please install it with: pip install opencc-python-reimplemented")
    sys.exit(1)


def convert_traditional_to_simplified(text):
    """Convert traditional Chinese characters to simplified Chinese"""
    converter = opencc.OpenCC('t2s')  # traditional to simplified
    return converter.convert(text)


def process_file(input_file, output_file=None, backup=True):
    """Process a single file"""
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: File {input_file} does not exist")
        return False

    # Read input file
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error: Failed to read file {input_file} - {e}")
        return False

    # Convert content
    converted_content = convert_traditional_to_simplified(content)

    # If no output file specified, overwrite the original file
    if output_file is None:
        output_path = input_path

        # Create backup if requested
        if backup:
            backup_path = input_path.with_suffix(input_path.suffix + '.backup')
            try:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Backup created: {backup_path}")
            except Exception as e:
                print(f"Warning: Failed to create backup file - {e}")
    else:
        output_path = Path(output_file)

    # Write converted content
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        print(f"Conversion completed: {input_file} -> {output_path}")
        return True
    except Exception as e:
        print(f"Error: Failed to write file {output_path} - {e}")
        return False


def process_directory(input_dir, output_dir=None, recursive=False, backup=True):
    """Process all txt files in directory"""
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: Directory {input_dir} does not exist")
        return False

    if not input_path.is_dir():
        print(f"Error: {input_dir} is not a directory")
        return False

    # Get all txt files
    if recursive:
        txt_files = list(input_path.rglob('*.txt'))
    else:
        txt_files = list(input_path.glob('*.txt'))

    if not txt_files:
        print(f"No txt files found in {input_dir}")
        return False

    print(f"Found {len(txt_files)} txt files")

    success_count = 0
    for txt_file in txt_files:
        if output_dir:
            # Calculate output file path
            relative_path = txt_file.relative_to(input_path)
            output_file = Path(output_dir) / relative_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_file = None

        if process_file(txt_file, output_file, backup):
            success_count += 1

    print(f"Processing completed: Successfully converted {success_count}/{len(txt_files)} files")
    return success_count > 0


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Traditional Chinese to Simplified Chinese Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.txt                    # Convert single file, overwrite original
  %(prog)s input.txt -o output.txt      # Convert to specified file
  %(prog)s input_dir/ -r                # Recursively convert all txt files in directory
  %(prog)s input_dir/ -o output_dir/    # Convert directory to specified output directory
        """
    )

    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-o', '--output', help='Output file or directory path')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Recursively process subdirectories (valid for directory input only)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Do not create backup files (valid for file overwrite mode only)')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_file():
        # Process single file
        success = process_file(args.input, args.output, backup=not args.no_backup)
        sys.exit(0 if success else 1)
    elif input_path.is_dir():
        # Process directory
        success = process_directory(args.input, args.output,
                                  recursive=args.recursive,
                                  backup=not args.no_backup)
        sys.exit(0 if success else 1)
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        sys.exit(1)


if __name__ == '__main__':
    main()