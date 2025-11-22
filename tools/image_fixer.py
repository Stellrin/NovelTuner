#!/usr/bin/env python3
"""
EPUB Image Fixer Tool for NovelTuner
EPUB图片下载修复工具

This tool processes EPUB files to download and fix image references,
supporting batch processing of multiple EPUB files and recursive directory processing.
"""

import argparse
import os
import re
import sys
import time
import zipfile
import shutil
from pathlib import Path
from io import BytesIO
from urllib.parse import urlparse
from typing import Optional, List, Tuple

# Import utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import (
    get_files_to_process, ensure_output_dir, safe_write_file,
    create_backup, should_create_backup, add_common_arguments,
    validate_input_path, create_progress_callback, format_file_size
)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


def get_description() -> str:
    """Return tool description"""
    return "Download and fix image references in EPUB files"


def get_parser() -> argparse.ArgumentParser:
    """Return configured ArgumentParser for this tool"""
    parser = argparse.ArgumentParser(
        prog="image_fixer",
        description=get_description(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python novel_tuner.py image_fixer input.epub
  python novel_tuner.py image_fixer input.epub -o output.epub
  python novel_tuner.py image_fixer novel_dir/ -r
  python novel_tuner.py image_fixer input.epub -b -v
        """
    )

    # Add common arguments
    add_common_arguments(parser, tool_specific_args=False)

    # Tool-specific arguments
    parser.add_argument(
        '-f', '--file-extensions',
        default='epub',
        help='File extensions to process (default: epub)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts for failed downloads (default: 3)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=15,
        help='Request timeout in seconds (default: 15)'
    )

    return parser


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required dependencies are available"""
    missing_deps = []

    if not HAS_REQUESTS:
        missing_deps.append("requests")
    if not HAS_BS4:
        missing_deps.append("beautifulsoup4")
    if not HAS_PIL:
        missing_deps.append("pillow")
    if not HAS_TQDM:
        missing_deps.append("tqdm")

    return len(missing_deps) == 0, missing_deps


def download_image(image_url: str, save_dir: str, timeout: int = 15, max_retries: int = 3) -> Optional[str]:
    """Download image to specified directory with retry mechanism"""
    if not HAS_REQUESTS or not HAS_PIL:
        return None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(image_url, timeout=timeout)
            response.raise_for_status()

            # Extract filename
            img_name = os.path.basename(urlparse(image_url).path)
            if not img_name:
                img_name = "img_" + str(abs(hash(image_url))) + ".jpg"

            # Ensure valid image extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            if not any(img_name.lower().endswith(ext) for ext in valid_extensions):
                img_name += ".jpg"

            img_path = os.path.join(save_dir, img_name)

            # Save image
            image = Image.open(BytesIO(response.content))
            image.save(img_path)
            return img_name

        except Exception as e:
            print(f"[Image download failed][Attempt {attempt}] {image_url} -> {e}")
            if attempt == max_retries:
                return None
            else:
                time.sleep(2)


def extract_epub(epub_file: str, temp_dir: str) -> bool:
    """Extract EPUB to temporary directory"""
    try:
        with zipfile.ZipFile(epub_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return True
    except Exception as e:
        print(f"Error: Failed to extract EPUB file {epub_file} - {e}")
        return False


def update_xhtml_images(xhtml_path: str, images_dir: str, args: argparse.Namespace) -> Tuple[bool, int]:
    """Update XHTML files to replace <图片> tags with <img> tags"""
    if not HAS_BS4:
        print(f"Error: beautifulsoup4 required for XHTML processing")
        return False, 0

    try:
        with open(xhtml_path, 'r', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        print(f"Error: Failed to read XHTML file {xhtml_path} - {e}")
        return False, 0

    changed = False
    download_count = 0

    # Find all <图片> tags (both as text content and as actual tags)
    for p_tag in soup.find_all('p'):
        text_content = p_tag.get_text(strip=True)
        if text_content.startswith("<图片>"):
            img_url = text_content[len("<图片>"):]
            if img_url.startswith("http") and "mitemin.net" in img_url:
                if args.verbose:
                    print(f"Downloading image: {img_url}")
                img_filename = download_image(img_url, images_dir, args.timeout, args.max_retries)
                if img_filename:
                    img_tag = soup.new_tag('img', src=f"../images/{img_filename}")
                    p_tag.clear()
                    p_tag.append(img_tag)
                    changed = True
                    download_count += 1
                    if args.verbose:
                        print(f"Successfully downloaded and replaced: {img_filename}")
                else:
                    print(f"Failed to download image: {img_url}")

    if changed:
        try:
            with open(xhtml_path, 'w', encoding='utf-8') as file:
                file.write(str(soup))
            if args.verbose:
                print(f"Updated XHTML file: {xhtml_path} ({download_count} images processed)")
            return True, download_count
        except Exception as e:
            print(f"Error: Failed to write XHTML file {xhtml_path} - {e}")
            return False, 0

    return False, 0


def rebuild_epub(temp_dir: str, output_epub_file: str) -> bool:
    """Repackage EPUB (ensure mimetype file is first and uncompressed)"""
    try:
        epub_files = []
        for foldername, subfolders, filenames in os.walk(temp_dir):
            for filename in filenames:
                filepath = os.path.join(foldername, filename)
                arcname = os.path.relpath(filepath, temp_dir)
                epub_files.append((filepath, arcname))

        with zipfile.ZipFile(output_epub_file, 'w') as zf:
            # mimetype must be uncompressed and first
            for filepath, arcname in epub_files:
                if arcname == "mimetype":
                    zf.write(filepath, arcname, compress_type=zipfile.ZIP_STORED)
            # Other files can be compressed normally
            for filepath, arcname in epub_files:
                if arcname != "mimetype":
                    zf.write(filepath, arcname, compress_type=zipfile.ZIP_DEFLATED)

        return True
    except Exception as e:
        print(f"Error: Failed to rebuild EPUB file {output_epub_file} - {e}")
        return False


def process_single_epub(epub_file: str, output_file: Optional[str], args: argparse.Namespace, temp_dir: str = "temp_epub") -> Tuple[bool, int]:
    """Process a single EPUB file"""
    epub_path = Path(epub_file)

    if not epub_path.exists():
        print(f"Error: EPUB file {epub_file} does not exist")
        return False, 0

    if not epub_path.suffix.lower() == '.epub':
        print(f"Error: {epub_file} is not an EPUB file")
        return False, 0

    # Clean up temp directory if it exists
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        if args.verbose:
            print(f"Processing EPUB: {epub_file}")

        # Extract EPUB
        if not extract_epub(epub_file, temp_dir):
            return False, 0

        # Ensure OEBPS/images directory exists
        images_dir = os.path.join(temp_dir, "OEBPS", "images")
        os.makedirs(images_dir, exist_ok=True)

        # Process all XHTML files
        text_dir = os.path.join(temp_dir, "OEBPS", "Text")
        if not os.path.exists(text_dir):
            if args.verbose:
                print(f"Warning: Text directory not found in {epub_file}")
            # Try alternative structure
            text_dir = os.path.join(temp_dir, "text")
            if not os.path.exists(text_dir):
                print(f"Error: Could not find text directory in {epub_file}")
                return False, 0

        xhtml_files = []
        for root, dirs, files in os.walk(text_dir):
            for file in files:
                if file.endswith(".xhtml") or file.endswith(".html"):
                    xhtml_files.append(os.path.join(root, file))

        if not xhtml_files:
            print(f"Warning: No XHTML files found in {epub_file}")
            return False, 0

        if args.verbose:
            print(f"Found {len(xhtml_files)} XHTML files to process")

        processed_count = 0
        total_downloads = 0

        # Progress bar or simple progress
        if HAS_TQDM and not args.quiet:
            progress_bar = tqdm(xhtml_files, desc="Processing XHTML files")
            file_iterator = progress_bar
        else:
            file_iterator = xhtml_files

        for xhtml_file in file_iterator:
            success, downloads = update_xhtml_images(xhtml_file, images_dir, args)
            if success:
                processed_count += 1
                total_downloads += downloads

        if args.verbose:
            print(f"Processed {processed_count} XHTML files with {total_downloads} images downloaded")

        # Determine output file
        if output_file is None:
            base_name = epub_path.stem
            output_path = epub_path.parent / f"{base_name}_fixed.epub"
        else:
            output_path = Path(output_file)

        # Create backup if requested
        if should_create_backup(getattr(args, 'backup', False), str(epub_path)):
            backup_path = create_backup(str(epub_path))
            if not backup_path:
                print(f"Warning: Failed to create backup for {epub_path}")

        # Rebuild EPUB
        if rebuild_epub(temp_dir, str(output_path)):
            if args.verbose:
                print(f"Successfully created fixed EPUB: {output_path}")
            return True, total_downloads
        else:
            return False, 0

    except Exception as e:
        print(f"Error: Failed to process EPUB file {epub_file} - {e}")
        return False, 0
    finally:
        # Clean up temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def main(args: argparse.Namespace) -> int:
    """
    Main function for image_fixer tool

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Check dependencies
    has_deps, missing_deps = check_dependencies()
    if not has_deps:
        print(f"Error: Missing required dependencies: {', '.join(missing_deps)}")
        print("Please install with: pip install " + " ".join(missing_deps))
        return 1

    # Validate input path
    if not validate_input_path(args.input):
        return 1

    # Parse file extensions (default to epub)
    file_extensions = parse_file_extensions(args.file_extensions) or {'epub'}

    # Get EPUB files to process
    try:
        files_to_process = list(get_files_to_process(args.input, args.recursive, file_extensions))
    except Exception as e:
        print(f"Error getting files to process: {e}")
        return 1

    if not files_to_process:
        print("No EPUB files found to process.")
        return 1

    if not args.quiet:
        print(f"Found {len(files_to_process)} EPUB files to process")

    # Ensure output directory
    if args.output:
        ensure_output_dir(args.output)

    # Process files
    success_count = 0
    failed_count = 0
    total_downloads = 0

    progress_callback = create_progress_callback(len(files_to_process), args.verbose)

    for file_path in files_to_process:
        try:
            # Determine output file
            if args.output:
                if Path(args.output).is_dir():
                    # Output is directory, preserve filename with suffix
                    output_file = str(Path(args.output) / f"{file_path.stem}_fixed.epub")
                else:
                    # Output is specific file (only for single file processing)
                    if len(files_to_process) == 1:
                        output_file = args.output
                    else:
                        print(f"Error: When processing multiple files, output must be a directory")
                        return 1
            else:
                # No output specified, auto-generate
                output_file = None

            # Process the EPUB file
            success, downloads = process_single_epub(str(file_path), output_file, args)

            if success:
                success_count += 1
                total_downloads += downloads
                progress_callback(str(file_path), True, f"Downloaded {downloads} images")
            else:
                failed_count += 1
                progress_callback(str(file_path), False, "Processing failed")

        except Exception as e:
            failed_count += 1
            progress_callback(str(file_path), False, f"Exception: {e}")

    # Final summary
    if not args.quiet:
        print(f"\nProcessing complete: {success_count} successful, {failed_count} failed")
        if total_downloads > 0:
            print(f"Total images downloaded: {total_downloads}")

    return 0 if failed_count == 0 else 1


# For standalone execution
if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    sys.exit(main(args))


def parse_file_extensions(extensions_str: Optional[str]) -> Optional[set]:
    """Parse comma-separated file extensions string into a set"""
    if not extensions_str:
        return None

    try:
        extensions = set()
        for ext in extensions_str.split(','):
            ext = ext.strip().lower()
            if ext:
                if ext.startswith('.'):
                    ext = ext[1:]
                extensions.add(ext)
        return extensions if extensions else None
    except Exception:
        return None