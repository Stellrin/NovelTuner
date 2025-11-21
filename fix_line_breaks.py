#!/usr/bin/env python3
"""
文本换行修复脚本
功能：
1. 修复不正常换行（一行以汉字结尾，下一行以汉字开始）
2. 支持批量处理多个文件
3. 支持递归处理目录
4. 支持备份原文件
"""

import sys
import os
import re
import shutil
import argparse
from pathlib import Path

def is_chinese_char(char):
    """判断字符是否为汉字"""
    return '\u4e00' <= char <= '\u9fff'

def fix_abnormal_line_breaks(text):
    """修复不正常的换行"""
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
    """获取文本文件列表"""
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

def process_file(input_file, output_file=None, backup=True, preview=False):
    """处理单个文件"""
    try:
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复换行
        fixed_content = fix_abnormal_line_breaks(content)

        # 如果没有变化，直接返回
        if content == fixed_content:
            print(f"No fix needed: {input_file}")
            return True

        # 写入输出文件
        if output_file is None:
            output_file = input_file

        # 备份原文件
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
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Fix abnormal line breaks in Chinese text files',
        epilog="""
Examples:
  %(prog)s file.txt                    # Fix single file
  %(prog)s folder/                     # Fix all text files in folder
  %(prog)s folder/ -r                  # Recursive processing
  %(prog)s file.txt -o fixed.txt       # Output to different file
  %(prog)s file.txt -b                 # No backup (use with caution)
  %(prog)s folder/ -f txt,md           # Only process .txt and .md files
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-o', '--output', help='Output file or directory (optional)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Process subdirectories recursively')
    parser.add_argument('-b', '--no-backup', action='store_true',
                        help='Do not create backup files (use with caution)')
    parser.add_argument('-f', '--filter', default='txt,md,log',
                        help='File extensions to process (default: txt,md,log)')

    args = parser.parse_args()

    # 检查输入路径
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Path does not exist: {args.input}")
        sys.exit(1)

    # 获取要处理的文件列表
    files_to_process = []

    if input_path.is_file():
        # 处理单个文件
        files_to_process = [str(input_path)]
    else:
        # 处理目录
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

    # 处理文件
    success_count = 0

    for file_path in files_to_process:
        if process_file(file_path, None, not args.no_backup, False):
            success_count += 1

    # 显示总结
    print(f"Processing complete: {success_count}/{len(files_to_process)} files successful")

if __name__ == "__main__":
    main()