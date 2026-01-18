#!/usr/bin/env python3
"""
EPUB Converter for NovelTuner
EPUB格式小说处理工具

This tool unpacks EPUB files, applies text transformations to all content files,
and repacks them into a new EPUB file.
"""

import argparse
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Callable

# Import utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    validate_input_path, ensure_output_dir, create_backup, should_create_backup,
    add_common_arguments, parse_file_extensions, create_progress_callback,
    extract_epub, create_epub_from_dir, find_xhtml_files,
    read_xhtml_content, write_xhtml_content, process_epub_text_content,
    get_epub_metadata, cleanup_extracted_epub
)

try:
    from opencc import OpenCC
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False


def get_description() -> str:
    """Return tool description"""
    return "Process EPUB files by unpacking, transforming, and repacking"


def get_parser() -> argparse.ArgumentParser:
    """Return configured ArgumentParser for this tool"""
    parser = argparse.ArgumentParser(
        prog="epub_converter",
        description=get_description(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert Traditional Chinese EPUB to Simplified
  python novel_tuner.py epub_converter traditional.epub -o simplified.epub

  # Fix line breaks in EPUB
  python novel_tuner.py epub_converter novel.epub --fix-breaks -o output.epub

  # Apply both transformations
  python novel_tuner.py epub_converter input.epub --fix-breaks --to-simplified -o output.epub

  # Process with backup
  python novel_tuner.py epub_converter novel.epub -b -o converted.epub

  # Keep extracted files for debugging
  python novel_tuner.py epub_converter novel.epub --keep-extracted -o output.epub
        """
    )

    # Add common arguments
    add_common_arguments(parser, tool_specific_args=False)

    # Tool-specific arguments
    transform_group = parser.add_argument_group('Transformation Options')
    transform_group.add_argument(
        '--to-simplified',
        action='store_true',
        help='Convert Traditional Chinese to Simplified Chinese'
    )
    transform_group.add_argument(
        '--to-traditional',
        action='store_true',
        help='Convert Simplified Chinese to Traditional Chinese'
    )
    transform_group.add_argument(
        '--fix-breaks',
        action='store_true',
        help='Fix Chinese text line break issues'
    )
    transform_group.add_argument(
        '--punctuation',
        default='。！？：；',
        help='Punctuation marks for line break fixing (default: "。！？：；")'
    )

    epub_group = parser.add_argument_group('EPUB Options')
    epub_group.add_argument(
        '--keep-extracted',
        action='store_true',
        help='Keep extracted EPUB directory for debugging'
    )
    epub_group.add_argument(
        '--extract-dir',
        help='Specify directory for extracted files (default: temp directory)'
    )
    epub_group.add_argument(
        '--process-all',
        action='store_true',
        help='Process all files (including non-XHTML files with text content)'
    )

    return parser


def convert_traditional_to_simplified(text: str) -> str:
    """Convert Traditional Chinese to Simplified Chinese"""
    if not HAS_OPENCC:
        return basic_traditional_to_simplified(text)

    try:
        converter = OpenCC('t2s')
        return converter.convert(text)
    except Exception:
        return basic_traditional_to_simplified(text)


def convert_simplified_to_traditional(text: str) -> str:
    """Convert Simplified Chinese to Traditional Chinese"""
    if not HAS_OPENCC:
        # Fallback: reverse mapping (limited)
        return basic_simplified_to_traditional(text)

    try:
        converter = OpenCC('s2t')
        return converter.convert(text)
    except Exception:
        return basic_simplified_to_traditional(text)


def basic_traditional_to_simplified(text: str) -> str:
    """Basic Traditional to Simplified conversion (fallback)"""
    mapping = {
        '們': '们', '來': '来', '對': '对', '時': '时', '會': '会',
        '個': '个', '說': '说', '過': '过', '發': '发', '現': '现',
        '開': '开', '關': '关', '長': '长', '電': '电', '視': '视',
        '聽': '听', '見': '见', '頭': '头', '買': '买', '賣': '卖',
        '讀': '读', '書': '书', '寫': '写', '話': '话', '語': '语',
        '學': '学', '習': '习', '進': '进', '齊': '齐', '業': '业',
        '産': '产', '黨': '党', '國': '国', '園': '园',
        '場': '场', '車': '车', '運': '运', '輸': '输', '經': '经',
        '濟': '济', '財': '财', '錢': '钱', '銀': '银', '門': '门',
        '問': '问', '間': '间', '體': '体', '現': '现', '實': '实',
        '質': '质', '還': '还', '給': '给', '讓': '让', '為': '为',
        '這': '这', '裡': '里', '邊': '边', '後': '后',
        '東': '东', '風': '风', '雲': '云', '燈': '灯',
        '紅': '红', '綠': '绿', '藍': '蓝', '黃': '黄', '顏': '颜',
        '樂': '乐', '歡': '欢', '愛': '爱', '戀': '恋', '親': '亲',
        '龍': '龙', '鳳': '凤', '鳥': '鸟', '魚': '鱼', '馬': '马',
        '鳴': '鸣', '鷗': '鸥', '鴨': '鸭', '鵝': '鹅', '鶴': '鹤',
        '龜': '龟'
    }

    result = text
    for traditional, simplified in mapping.items():
        result = result.replace(traditional, simplified)
    return result


def basic_simplified_to_traditional(text: str) -> str:
    """Basic Simplified to Traditional conversion (fallback)"""
    mapping = {
        '们': '們', '来': '來', '对': '對', '时': '時', '会': '會',
        '个': '個', '说': '說', '过': '過', '发': '發', '现': '現',
        '开': '開', '关': '關', '长': '長', '电': '電', '视': '視',
        '听': '聽', '见': '見', '头': '頭', '买': '買', '卖': '賣',
        '读': '讀', '书': '書', '写': '寫', '话': '話', '语': '語',
        '学': '學', '习': '習', '进': '進', '齐': '齊', '业': '業',
        '产': '産', '党': '黨', '国': '國', '园': '園',
        '场': '場', '车': '車', '运': '運', '输': '輸', '经': '經',
        '济': '濟', '财': '財', '钱': '錢', '银': '銀', '门': '門',
        '问': '問', '间': '間', '体': '體', '实': '實',
        '质': '質', '还': '還', '给': '給', '让': '讓', '为': '為',
        '这': '這', '里': '裡', '边': '邊', '后': '後',
        '东': '東', '风': '風', '云': '雲', '灯': '燈',
        '红': '紅', '绿': '綠', '蓝': '藍', '黄': '黃', '颜': '顏',
        '乐': '樂', '欢': '歡', '爱': '愛', '恋': '戀', '亲': '親',
        '龙': '龍', '凤': '鳳', '鸟': '鳥', '鱼': '魚', '马': '馬',
        '鸣': '鳴', '鸥': '鷗', '鸭': '鴨', '鹅': '鵝', '鹤': '鶴',
        '龟': '龜'
    }

    result = text
    for simplified, traditional in mapping.items():
        result = result.replace(simplified, traditional)
    return result


def fix_line_breaks(text: str, punctuation: str = '。！？：；') -> str:
    """
    Fix Chinese text line break issues

    Args:
        text: Input text
        punctuation: Punctuation marks that indicate sentence ends

    Returns:
        Text with fixed line breaks
    """
    import re

    # Replace Windows line endings
    text = text.replace('\r\n', '\n')
    # Replace old Mac line endings
    text = text.replace('\r', '\n')

    lines = text.split('\n')
    result_lines = []
    buffer = ''

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            if buffer:
                result_lines.append(buffer)
                buffer = ''
            result_lines.append('')
            continue

        # Check if line ends with punctuation
        ends_with_punct = any(stripped.endswith(p) for p in punctuation)

        if ends_with_punct:
            # Line ends properly, add to buffer and flush
            if buffer:
                buffer += stripped
                result_lines.append(buffer)
                buffer = ''
            else:
                result_lines.append(stripped)
        else:
            # Line doesn't end with punctuation, might be broken
            if buffer:
                buffer += stripped
            else:
                buffer = stripped

    # Add remaining buffer
    if buffer:
        result_lines.append(buffer)

    return '\n'.join(result_lines)


def get_transformation_function(args: argparse.Namespace) -> Optional[Callable[[str], str]]:
    """
    Get the text transformation function based on arguments

    Args:
        args: Command line arguments

    Returns:
        Transformation function or None
    """
    transformations = []

    if args.to_simplified:
        transformations.append(convert_traditional_to_simplified)

    if args.to_traditional:
        transformations.append(convert_simplified_to_traditional)

    # Combine transformations if needed
    if not transformations:
        return None

    def combined_transform(text: str) -> str:
        result = text
        for transform in transformations:
            result = transform(result)
        return result

    return combined_transform


def process_epub_file(
    epub_path: str,
    output_path: str,
    args: argparse.Namespace
) -> bool:
    """
    Process a single EPUB file

    Args:
        epub_path: Input EPUB file path
        output_path: Output EPUB file path
        args: Command line arguments

    Returns:
        True if successful, False otherwise
    """
    extract_dir = None
    temp_extract = False

    try:
        # Create backup if requested
        if should_create_backup(args.backup, epub_path):
            backup_path = create_backup(epub_path)
            if backup_path and args.verbose:
                print(f"Created backup: {backup_path}")

        # Determine extraction directory
        if args.extract_dir:
            extract_dir = args.extract_dir
            Path(extract_dir).mkdir(parents=True, exist_ok=True)
        else:
            extract_dir = tempfile.mkdtemp(prefix="epub_convert_")
            temp_extract = True

        if args.verbose:
            print(f"Extracting EPUB: {epub_path} -> {extract_dir}")

        # Extract EPUB
        extract_epub(epub_path, extract_dir)

        # Get EPUB metadata
        metadata = get_epub_metadata(extract_dir)
        if args.verbose and metadata.get('title'):
            print(f"Processing: {metadata.get['title']}")

        # Find XHTML files to process
        xhtml_files = find_xhtml_files(extract_dir)

        if not xhtml_files:
            print("Warning: No XHTML files found in EPUB")
            # Still create the output EPUB even if no content to process
        else:
            if args.verbose:
                print(f"Found {len(xhtml_files)} XHTML files to process")

        # Get transformation function
        transform_func = get_transformation_function(args)
        fix_breaks = args.fix_breaks

        # Process each XHTML file
        success_count = 0
        failed_count = 0

        for xhtml_file in xhtml_files:
            try:
                # Read XHTML content
                content = read_xhtml_content(str(xhtml_file))

                # Apply transformations
                if transform_func:
                    if args.verbose:
                        print(f"Applying text transformation to {xhtml_file.relative_to(extract_dir)}")
                    content = process_epub_text_content(content, transform_func)

                # Fix line breaks if requested
                if fix_breaks:
                    if args.verbose:
                        print(f"Fixing line breaks in {xhtml_file.relative_to(extract_dir)}")

                    def fix_transform(text: str) -> str:
                        return fix_line_breaks(text, args.punctuation)

                    content = process_epub_text_content(content, fix_transform)

                # Write back
                write_xhtml_content(str(xhtml_file), content)
                success_count += 1

            except Exception as e:
                print(f"Error processing {xhtml_file}: {e}")
                failed_count += 1

        if not args.quiet:
            print(f"Processed {success_count} files, {failed_count} failed")

        # Create output EPUB
        if args.verbose:
            print(f"Creating output EPUB: {output_path}")

        ensure_output_dir(output_path)
        create_epub_from_dir(extract_dir, output_path)

        if not args.quiet:
            print(f"Created: {output_path}")

        return True

    except Exception as e:
        print(f"Error processing EPUB {epub_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up extracted directory
        if not args.keep_extracted and temp_extract and extract_dir:
            if args.verbose:
                print(f"Cleaning up: {extract_dir}")
            cleanup_extracted_epub(extract_dir, keep_extracted=False)
        elif args.keep_extracted and extract_dir:
            print(f"Extracted files kept at: {extract_dir}")


def main(args: argparse.Namespace) -> int:
    """
    Main function for epub_converter tool

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Validate that at least one transformation is specified
    if not any([args.to_simplified, args.to_traditional, args.fix_breaks]):
        print("Error: Please specify at least one transformation:")
        print("  --to-simplified    Convert to Simplified Chinese")
        print("  --to-traditional   Convert to Traditional Chinese")
        print("  --fix-breaks       Fix line break issues")
        return 1

    # Check OpenCC availability for conversion
    if (args.to_simplified or args.to_traditional) and not HAS_OPENCC:
        print("Warning: OpenCC not available. Using basic character mapping fallback.")
        print("For better results, install with: pip install opencc-python-reimplemented")

    # Validate input path
    input_path = Path(args.input)
    if not validate_input_path(args.input):
        return 1

    # Determine output path (default to overwrite input if not specified)
    if not args.output:
        # No output specified, overwrite input files
        if not args.quiet:
            print("Warning: No output specified. Will overwrite original files.")
        output_specified = False
    else:
        output_specified = True

    # Process single EPUB file or directory
    if input_path.is_file():
        # Single file
        if output_specified:
            output_file = args.output
            if not output_file.lower().endswith('.epub'):
                print("Warning: Output file does not have .epub extension")
        else:
            # Overwrite input file
            output_file = str(input_path)

        success = process_epub_file(str(input_path), output_file, args)
        return 0 if success else 1

    elif input_path.is_dir():
        # Directory - find all EPUB files
        epub_files = list(input_path.glob('*.epub'))
        epub_files.extend(input_path.glob('*.EPUB'))

        if not epub_files:
            print("No EPUB files found in the specified directory")
            return 1

        if not args.quiet:
            print(f"Found {len(epub_files)} EPUB files to process")

        # Determine output directory
        if output_specified:
            output_path = Path(args.output)
            if output_path.suffix:  # It's a file path, but we have multiple files
                print("Error: Output must be a directory when processing multiple EPUB files")
                return 1
            output_path.mkdir(parents=True, exist_ok=True)
            output_dir = str(output_path)
        else:
            # Overwrite in place
            output_dir = None

        # Process each EPUB file
        success_count = 0
        failed_count = 0

        progress_callback = create_progress_callback(len(epub_files), args.verbose)

        for epub_file in epub_files:
            if output_dir:
                output_file = str(Path(output_dir) / epub_file.name)
            else:
                # Overwrite in place
                output_file = str(epub_file)
            success = process_epub_file(str(epub_file), output_file, args)

            if success:
                success_count += 1
                progress_callback(str(epub_file), True)
            else:
                failed_count += 1
                progress_callback(str(epub_file), False, "Processing failed")

        # Final summary
        if not args.quiet:
            print(f"\nProcessing complete: {success_count} successful, {failed_count} failed")

        return 0 if failed_count == 0 else 1

    else:
        print("Error: Input path must be a file or directory")
        return 1


# For standalone execution
if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    sys.exit(main(args))
