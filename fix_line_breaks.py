#!/usr/bin/env python3
"""
Text Line Break Fixer
Features:
1. Fix abnormal line breaks (line ending with Chinese character, next line starting with Chinese character)
2. Support batch processing of multiple files
3. Support recursive directory processing
4. Support backup of original files
"""

import sys
import os
import re
import shutil
import argparse
from pathlib import Path

def is_chinese_char(char):
    """Check if character is Chinese"""
    return '\u4e00' <= char <= '\u9fff'

def fix_abnormal_line_breaks(text):
    """Fix abnormal line breaks"""
    lines = text.split('\n')
    fixed_lines = []

    i = 0
    while i < len(lines):
        current_line = lines[i].rstrip()

        # 如果是最后一行，直接添加
        if i == len(lines) - 1:
            fixed_lines.append(current_line)
            break

        # 跳过空行
        if not current_line:
            fixed_lines.append(current_line)
            i += 1
            continue

        # 检查是否需要合并：当前行以汉字结尾，下一行以汉字开始
        # 使用循环来处理连续的多行合并
        merged_line = current_line
        j = i + 1

        while j < len(lines):
            next_line = lines[j].strip()

            # 如果下一行是空行，停止合并
            if not next_line:
                break

            # 检查合并条件：当前行以汉字结尾，下一行以汉字开始
            if (is_chinese_char(merged_line[-1]) and
                is_chinese_char(next_line[0]) and
                not merged_line.endswith(('。', '！', '？', '：', '；', '」', '』', '】', '）', '》', '，', '、')) and
                not next_line.startswith(('　', ' ', '「', '『', '【', '（', '《', '』', '」', '，', '、'))):

                # 合并两行，保持缩进格式
                merged_line = merged_line + next_line.lstrip()
                j += 1
            else:
                # 不满足合并条件，停止合并
                break

        fixed_lines.append(merged_line)
        i = j

    return '\n'.join(fixed_lines)

def get_text_files(directory, recursive=False):
    """Get list of text files"""
    text_extensions = {'.txt', '.md', '.log'}
    files = []

    if recursive:
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if Path(filename).suffix.lower() in text_extensions:
                    files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            if Path(filename).suffix.lower() in text_extensions:
                files.append(os.path.join(directory, filename))

    return files

def process_file(input_file, output_file=None, backup=False):
    """Process single file"""
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix line breaks
        fixed_content = fix_abnormal_line_breaks(content)

        # If no changes, return directly
        if content == fixed_content:
            print(f"No fix needed: {input_file}")
            return True

        # Write output file
        if output_file is None:
            output_file = input_file

        # Backup original file
        if backup:
            backup_file = input_file + '.bak'
            shutil.copy2(input_file, backup_file)
            print(f"Backup created: {backup_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        print(f"Fixed: {input_file}")
        if output_file != input_file:
            print(f"Output to: {output_file}")

        return True

    except Exception as e:
        print(f"Error processing file {input_file}: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Fix abnormal line breaks in Chinese text files',
        epilog="""
Examples:
  %(prog)s file.txt                    # Fix single file
  %(prog)s folder/                     # Fix all text files in folder
  %(prog)s folder/ -r                  # Recursive processing
  %(prog)s file.txt -o fixed.txt       # Output to different file
  %(prog)s file.txt -b                 # Create backup
  %(prog)s folder/ -f txt,md           # Only process .txt and .md files
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-o', '--output', help='Output file or directory (optional)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Process subdirectories recursively')
    parser.add_argument('-b', '--backup', action='store_true',
                        help='Create backup files (use with caution)')
    parser.add_argument('-f', '--filter', default='txt,md,log',
                        help='File extensions to process (default: txt,md,log)')

    args = parser.parse_args()

    # Check input path
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Path does not exist: {args.input}")
        sys.exit(1)

    # Get list of files to process
    files_to_process = []

    if input_path.is_file():
        # Process single file
        files_to_process = [str(input_path)]
    else:
        # Process directory
        extensions = args.filter.split(',')
        text_extensions = {f'.{ext.strip()}' for ext in extensions}

        if args.recursive:
            for root, dirs, filenames in os.walk(str(input_path)):
                for filename in filenames:
                    if Path(filename).suffix.lower() in text_extensions:
                        files_to_process.append(os.path.join(root, filename))
        else:
            for filename in os.listdir(str(input_path)):
                if Path(filename).suffix.lower() in text_extensions:
                    files_to_process.append(os.path.join(str(input_path), filename))

    if not files_to_process:
        print("No files found to process")
        sys.exit(0)

    print(f"Found {len(files_to_process)} files to process")

    # Process files
    success_count = 0

    for file_path in files_to_process:
        if process_file(file_path, None, args.backup):
            success_count += 1

    # Show summary
    print(f"Processing complete: {success_count}/{len(files_to_process)} files successful")

if __name__ == "__main__":
    main()