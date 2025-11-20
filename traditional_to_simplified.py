#!/usr/bin/env python3
"""
Traditional Chinese to Simplified Chinese Converter
Command-line tool that converts traditional Chinese characters to simplified Chinese in text files
Enhanced version with automatic encoding detection and conversion
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

try:
    import chardet
except ImportError:
    print("Warning: chardet library is not installed")
    print("For better encoding detection, install it with: pip install chardet")
    chardet = None


def convert_traditional_to_simplified(text):
    """Convert traditional Chinese characters to simplified Chinese"""
    converter = opencc.OpenCC('t2s')  # traditional to simplified
    return converter.convert(text)


def detect_file_encoding(file_path):
    """Detect file encoding using chardet or fallback methods"""
    # First try chardet if available
    if chardet:
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB for detection
                result = chardet.detect(raw_data)
                if result and result['encoding']:
                    confidence = result['confidence']
                    encoding = result['encoding'].lower()
                    if confidence > 0.7:  # Only use if confidence is high enough
                        print(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
                        return encoding
        except Exception as e:
            print(f"Warning: chardet detection failed - {e}")

    # Fallback: try common encodings
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'cp936', 'iso-8859-1']

    for encoding in common_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1000)  # Try reading first 1000 characters
                print(f"Successfully detected encoding: {encoding}")
                return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue

    # If all else fails, return None
    print("Warning: Could not detect file encoding, will try utf-8 as fallback")
    return None


def read_file_with_encoding(file_path):
    """Read file with automatic encoding detection"""
    detected_encoding = detect_file_encoding(file_path)

    # Try detected encoding first
    if detected_encoding:
        try:
            with open(file_path, 'r', encoding=detected_encoding) as f:
                content = f.read()
                return content, detected_encoding
        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"Warning: Failed to read with detected encoding {detected_encoding} - {e}")

    # Fallback: try common encodings
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'cp936', 'iso-8859-1']

    for encoding in common_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"Successfully read file with encoding: {encoding}")
                return content, encoding
        except (UnicodeDecodeError, UnicodeError):
            continue

    # If all attempts fail
    raise UnicodeDecodeError(f"Unable to decode file {file_path} with any known encoding")


def process_file(input_file, output_file=None, backup=True):
    """Process a single file"""
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: File {input_file} does not exist")
        return False

    # Read input file with encoding detection
    try:
        content, original_encoding = read_file_with_encoding(input_path)
        print(f"Processing file with encoding: {original_encoding}")
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