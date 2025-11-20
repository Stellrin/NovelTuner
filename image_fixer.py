#!/usr/bin/env python3
"""
EPUB Image Fixer
Command-line tool that processes EPUB files to download and fix image references
Supports batch processing of multiple EPUB files and recursive directory processing
"""

import os
import sys
import re
import zipfile
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image
import shutil
import time
import argparse
from tqdm import tqdm

try:
    from tqdm import tqdm
except ImportError:
    print("Error: tqdm library is required")
    print("Please install it with: pip install tqdm")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests library is required")
    print("Please install it with: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 library is required")
    print("Please install it with: pip install beautifulsoup4")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow library is required")
    print("Please install it with: pip install pillow")
    sys.exit(1)


def download_image(image_url, save_dir):
    """Download image to specified directory (returns relative path), with retry mechanism"""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()

            # Extract filename
            img_name = os.path.basename(urlparse(image_url).path)
            if not img_name:  # Avoid empty filename
                img_name = "img_" + str(abs(hash(image_url))) + ".jpg"

            # Ensure valid image extension
            if not any(img_name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
                img_name += ".jpg"

            img_path = os.path.join(save_dir, img_name)

            # Save image
            image = Image.open(BytesIO(response.content))
            image.save(img_path)
            return img_name  # Return only filename
        except Exception as e:
            print(f"[Image download failed][Attempt {attempt}] {image_url} -> {e}")
            if attempt == max_retries:
                return None
            else:
                time.sleep(2)  # Wait 2 seconds before retry


def extract_epub(epub_file, temp_dir):
    """Extract EPUB to temporary directory"""
    try:
        with zipfile.ZipFile(epub_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return True
    except Exception as e:
        print(f"Error: Failed to extract EPUB file {epub_file} - {e}")
        return False


def update_xhtml_images(xhtml_path, images_dir):
    """Update XHTML files to replace <图片> tags with <img src="../images/...">"""
    try:
        with open(xhtml_path, 'r', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        print(f"Error: Failed to read XHTML file {xhtml_path} - {e}")
        return False

    changed = False
    download_count = 0

    # Find all <图片> tags (both as text content and as actual tags)
    for p_tag in soup.find_all('p'):
        text_content = p_tag.get_text(strip=True)
        if text_content.startswith("<图片>"):
            img_url = text_content[len("<图片>"):]
            if img_url.startswith("http") and "mitemin.net" in img_url:
                print(f"Downloading image: {img_url}")
                img_filename = download_image(img_url, images_dir)
                if img_filename:
                    img_tag = soup.new_tag('img', src=f"../images/{img_filename}")
                    p_tag.clear()
                    p_tag.append(img_tag)
                    changed = True
                    download_count += 1
                    print(f"Successfully downloaded and replaced: {img_filename}")
                else:
                    print(f"Failed to download image: {img_url}")

    if changed:
        try:
            with open(xhtml_path, 'w', encoding='utf-8') as file:
                file.write(str(soup))
            print(f"Updated XHTML file: {xhtml_path} ({download_count} images processed)")
            return True
        except Exception as e:
            print(f"Error: Failed to write XHTML file {xhtml_path} - {e}")
            return False

    return False


def rebuild_epub(temp_dir, output_epub_file):
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


def process_single_epub(epub_file, output_file=None, temp_dir="temp_epub"):
    """Process a single EPUB file"""
    epub_path = Path(epub_file)

    if not epub_path.exists():
        print(f"Error: EPUB file {epub_file} does not exist")
        return False

    if not epub_path.suffix.lower() == '.epub':
        print(f"Error: {epub_file} is not an EPUB file")
        return False

    # Clean up temp directory if it exists
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        print(f"Processing EPUB: {epub_file}")

        # Extract EPUB
        if not extract_epub(epub_file, temp_dir):
            return False

        # Ensure OEBPS/images directory exists
        images_dir = os.path.join(temp_dir, "OEBPS", "images")
        os.makedirs(images_dir, exist_ok=True)

        # Process all XHTML files
        text_dir = os.path.join(temp_dir, "OEBPS", "Text")
        if not os.path.exists(text_dir):
            print(f"Warning: Text directory not found in {epub_file}")
            # Try alternative structure
            text_dir = os.path.join(temp_dir, "text")
            if not os.path.exists(text_dir):
                print(f"Error: Could not find text directory in {epub_file}")
                return False

        xhtml_files = []
        for root, dirs, files in os.walk(text_dir):
            for file in files:
                if file.endswith(".xhtml") or file.endswith(".html"):
                    xhtml_files.append(os.path.join(root, file))

        if not xhtml_files:
            print(f"Warning: No XHTML files found in {epub_file}")
            return False

        print(f"Found {len(xhtml_files)} XHTML files to process")

        processed_count = 0
        for xhtml_file in tqdm(xhtml_files, desc="Processing XHTML files"):
            if update_xhtml_images(xhtml_file, images_dir):
                processed_count += 1

        print(f"Processed {processed_count} XHTML files with images")

        # Determine output file
        if output_file is None:
            # Create output filename by adding suffix
            base_name = epub_path.stem
            output_path = epub_path.parent / f"{base_name}_fixed.epub"
        else:
            output_path = Path(output_file)

        # Rebuild EPUB
        if rebuild_epub(temp_dir, str(output_path)):
            print(f"Successfully created fixed EPUB: {output_path}")
            return True
        else:
            return False

    except Exception as e:
        print(f"Error: Failed to process EPUB file {epub_file} - {e}")
        return False
    finally:
        # Clean up temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def find_epub_files(input_path, recursive=False):
    """Find all EPUB files in the given path"""
    input_path = Path(input_path)

    if input_path.is_file():
        if input_path.suffix.lower() == '.epub':
            return [input_path]
        else:
            return []

    elif input_path.is_dir():
        if recursive:
            return list(input_path.rglob('*.epub'))
        else:
            return list(input_path.glob('*.epub'))

    return []


def process_epub_files(input_path, output_path=None, recursive=False):
    """Process EPUB files with batch support"""
    epub_files = find_epub_files(input_path, recursive)

    if not epub_files:
        print(f"No EPUB files found in {input_path}")
        return False

    print(f"Found {len(epub_files)} EPUB file(s) to process")

    success_count = 0

    for epub_file in epub_files:
        print(f"\nProcessing file {epub_files.index(epub_file) + 1}/{len(epub_files)}: {epub_file}")

        if output_path:
            if Path(output_path).is_dir():
                # Output is a directory, preserve original filename
                output_file = Path(output_path) / f"{epub_file.stem}_fixed.epub"
            else:
                # Output is a specific file path
                output_file = output_path
        else:
            # Auto-generate output filename
            output_file = None

        if process_single_epub(str(epub_file), str(output_file) if output_file else None):
            success_count += 1

    print(f"\nProcessing completed: Successfully processed {success_count}/{len(epub_files)} EPUB files")
    return success_count > 0


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(
        description='EPUB Image Fixer - Downloads and fixes image references in EPUB files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.epub                           # Process single EPUB file
  %(prog)s input.epub -o output.epub            # Process and save to specific file
  %(prog)s input_dir/                           # Process all EPUB files in directory
  %(prog)s input_dir/ -r                        # Recursively process EPUB files
  %(prog)s input_dir/ -o output_dir/            # Process and save to output directory
        """
    )

    parser.add_argument('input', help='Input EPUB file or directory path')
    parser.add_argument('-o', '--output', help='Output file or directory path')
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='Recursively process subdirectories')
    parser.add_argument('--version', action='version', version='%(prog)s 2.0')

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: {args.input} does not exist")
        sys.exit(1)

    success = process_epub_files(args.input, args.output, args.recursive)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()