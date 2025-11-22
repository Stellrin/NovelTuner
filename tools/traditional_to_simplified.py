#!/usr/bin/env python3
"""
Traditional to Simplified Chinese Converter for NovelTuner
繁体中文转简体中文工具

This tool converts Traditional Chinese characters to Simplified Chinese using OpenCC.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Import utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    get_files_to_process, ensure_output_dir, safe_write_file,
    detect_encoding, read_file_with_encoding, create_backup, should_create_backup,
    add_common_arguments, validate_input_path, parse_file_extensions, create_progress_callback
)

try:
    from opencc import OpenCC
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False


def get_description() -> str:
    """Return tool description"""
    return "Convert Traditional Chinese to Simplified Chinese"


def get_parser() -> argparse.ArgumentParser:
    """Return configured ArgumentParser for this tool"""
    parser = argparse.ArgumentParser(
        prog="traditional_to_simplified",
        description=get_description(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python novel_tuner.py traditional_to_simplified input.txt
  python novel_tuner.py traditional_to_simplified input.txt -o output.txt
  python novel_tuner.py traditional_to_simplified novel_dir -r -f txt,md
  python novel_tuner.py traditional_to_simplified input.txt -b -v
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

    return parser


def convert_text_traditional_to_simplified(text: str) -> str:
    """
    Convert Traditional Chinese text to Simplified Chinese

    Args:
        text: Text in Traditional Chinese

    Returns:
        Text in Simplified Chinese
    """
    if not HAS_OPENCC:
        # Fallback: basic character mapping (limited)
        return basic_traditional_to_simplified(text)

    try:
        converter = OpenCC('t2s')  # Traditional to Simplified
        return converter.convert(text)
    except Exception as e:
        print(f"Warning: OpenCC conversion failed: {e}, using fallback")
        return basic_traditional_to_simplified(text)


def basic_traditional_to_simplified(text: str) -> str:
    """
    Basic Traditional to Simplified conversion using character mapping
    This is a fallback when OpenCC is not available

    Args:
        text: Text in Traditional Chinese

    Returns:
        Text in Simplified Chinese (basic conversion)
    """
    # Common Traditional to Simplified character mappings
    mapping = {
        '們': '们', '來': '来', '對': '对', '時': '时', '會': '会',
        '個': '个', '說': '说', '過': '过', '發': '发', '現': '现',
        '開': '开', '關': '关', '長': '长', '電': '电', '視': '视',
        '聽': '听', '見': '见', '頭': '头', '買': '买', '賣': '卖',
        '讀': '读', '書': '书', '寫': '写', '話': '话', '語': '语',
        '學': '学', '習': '习', '進': '进', '齊': '齐', '業': '业',
        '産': '产', '産': '产', '黨': '党', '國': '国', '園': '园',
        '場': '场', '車': '车', '運': '运', '輸': '输', '經': '经',
        '濟': '济', '財': '财', '錢': '钱', '銀': '银', '門': '门',
        '問': '问', '間': '间', '體': '体', '現': '现', '實': '实',
        '質': '质', '還': '还', '給': '给', '讓': '让', '為': '为',
        '這': '这', '那': '那', '裡': '里', '邊': '边', '後': '后',
        '前': '前', '東': '东', '西': '西', '南': '南', '北': '北',
        '風': '风', '雨': '雨', '雲': '云', '電': '电', '燈': '灯',
        '紅': '红', '綠': '绿', '藍': '蓝', '黃': '黄', '顏': '颜',
        '樂': '乐', '歡': '欢', '愛': '爱', '戀': '恋', '親': '亲',
        '龍': '龙', '鳳': '凤', '鳥': '鸟', '魚': '鱼', '馬': '马',
        '鳴': '鸣', '鷗': '鸥', '鴨': '鸭', '鵝': '鹅', '鶴': '鹤',
        '龜': '龟', '龍': '龙'
    }

    result = text
    for traditional, simplified in mapping.items():
        result = result.replace(traditional, simplified)

    return result


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

        # Convert Traditional to Simplified
        converted_content = convert_text_traditional_to_simplified(content)

        # Write output
        safe_write_file(output_path, converted_content, encoding)

        if args.verbose:
            print(f"Converted Traditional to Simplified: {file_path} -> {output_path}")

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main(args: argparse.Namespace) -> int:
    """
    Main function for traditional_to_simplified tool

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Check OpenCC availability
    if not HAS_OPENCC:
        print("Warning: OpenCC not available. Using basic character mapping fallback.")
        print("For better results, install with: pip install opencc-python-reimplemented")

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