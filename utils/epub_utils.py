"""
EPUB processing utilities for NovelTuner
EPUB格式电子书处理工具函数
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Callable, Optional, List, Tuple, Any
from xml.etree import ElementTree as ET


def extract_epub(epub_path: str, extract_dir: str = None) -> str:
    """
    Extract EPUB file to a directory

    Args:
        epub_path: Path to the EPUB file
        extract_dir: Directory to extract to (None for temp directory)

    Returns:
        Path to the extracted directory
    """
    import zipfile

    if extract_dir is None:
        extract_dir = tempfile.mkdtemp(prefix="epub_extract_")

    # Ensure extract directory exists
    Path(extract_dir).mkdir(parents=True, exist_ok=True)

    # Extract EPUB (it's a ZIP file)
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    return extract_dir


def create_epub_from_dir(source_dir: str, output_epub: str) -> None:
    """
    Create an EPUB file from a directory

    Args:
        source_dir: Directory containing the extracted EPUB content
        output_epub: Path for the output EPUB file
    """
    import zipfile

    # Ensure output directory exists
    output_path = Path(output_epub)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the EPUB (ZIP) file
    with zipfile.ZipFile(output_epub, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zip_ref.write(file_path, arcname)


def find_xhtml_files(extract_dir: str) -> List[Path]:
    """
    Find all XHTML/HTML files in the extracted EPUB directory

    Args:
        extract_dir: Path to the extracted EPUB directory

    Returns:
        List of XHTML file paths
    """
    extract_path = Path(extract_dir)
    xhtml_files = []

    # Common EPUB content directories
    content_dirs = ['OEBPS', 'OPS', 'Content', '']

    for content_dir in content_dirs:
        search_dir = extract_path / content_dir if content_dir else extract_path
        if not search_dir.exists():
            continue

        # Search for XHTML/HTML files
        for pattern in ['**/*.xhtml', '**/*.html', '**/*.htm']:
            xhtml_files.extend(search_dir.glob(pattern))

    return xhtml_files


def get_content_opf_path(extract_dir: str) -> Optional[str]:
    """
    Find the content.opf file in the extracted EPUB directory

    Args:
        extract_dir: Path to the extracted EPUB directory

    Returns:
        Path to the content.opf file or None
    """
    extract_path = Path(extract_dir)

    # Search for .opf files
    for opf_file in extract_path.rglob('*.opf'):
        return str(opf_file)

    # Search in common locations
    for container_dir in ['OEBPS', 'OPS', 'Content']:
        container_path = extract_path / container_dir
        if container_path.exists():
            opf_path = container_path / 'content.opf'
            if opf_path.exists():
                return str(opf_path)

    return None


def get_container_xml_path(extract_dir: str) -> Optional[str]:
    """
    Find the container.xml file in the META-INF directory

    Args:
        extract_dir: Path to the extracted EPUB directory

    Returns:
        Path to the container.xml file or None
    """
    container_path = Path(extract_dir) / 'META-INF' / 'container.xml'
    return str(container_path) if container_path.exists() else None


def read_xhtml_content(file_path: str) -> str:
    """
    Read XHTML file content

    Args:
        file_path: Path to the XHTML file

    Returns:
        File content as string
    """
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'gb18030', 'gbk', 'big5', 'iso-8859-1']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue

    # Fallback: read with error handling
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def write_xhtml_content(file_path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    Write content to XHTML file

    Args:
        file_path: Path to the XHTML file
        content: Content to write
        encoding: File encoding
    """
    # Ensure parent directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)


def extract_text_from_xhtml(xhtml_content: str) -> str:
    """
    Extract plain text from XHTML content

    Args:
        xhtml_content: XHTML content string

    Returns:
        Plain text content
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(xhtml_content, 'html.parser')

    # Remove script and style elements
    for script in soup(['script', 'style']):
        script.decompose()

    # Get text
    text = soup.get_text(separator='\n')

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines()]
    text = '\n'.join(line for line in lines if line)

    return text


def process_epub_text_content(
    xhtml_content: str,
    process_func: Callable[[str], str]
) -> str:
    """
    Process text content within XHTML while preserving structure

    Args:
        xhtml_content: Original XHTML content
        process_func: Function to process text content

    Returns:
        Processed XHTML content
    """
    from bs4 import BeautifulSoup, NavigableString

    soup = BeautifulSoup(xhtml_content, 'html.parser')

    def process_node(node):
        """Recursively process text nodes"""
        if isinstance(node, NavigableString):
            # Process text content
            processed_text = process_func(str(node))
            node.replace_with(processed_text)
        elif node.name:
            # Process child nodes
            for child in list(node.children):
                process_node(child)

    # Process all nodes
    for element in soup.descendants:
        if element.parent and isinstance(element, NavigableString):
            process_node(element)

    return str(soup)


def get_epub_metadata(extract_dir: str) -> dict:
    """
    Extract metadata from the EPUB content.opf file

    Args:
        extract_dir: Path to the extracted EPUB directory

    Returns:
        Dictionary containing metadata
    """
    metadata = {
        'title': '',
        'author': '',
        'language': '',
        'publisher': '',
        'description': ''
    }

    opf_path = get_content_opf_path(extract_dir)
    if not opf_path:
        return metadata

    try:
        tree = ET.parse(opf_path)
        root = tree.getroot()

        # Define namespace (common in EPUB)
        namespaces = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf'
        }

        # Try to find metadata elements
        metadata_elem = root.find('.//metadata')

        if metadata_elem is not None:
            for tag, key in [
                ('title', 'title'),
                ('creator', 'author'),
                ('language', 'language'),
                ('publisher', 'publisher'),
                ('description', 'description')
            ]:
                elem = metadata_elem.find(f'.//dc:{tag}', namespaces)
                if elem is not None and elem.text:
                    metadata[key] = elem.text

    except Exception as e:
        pass  # Silently fail on metadata extraction

    return metadata


def cleanup_extracted_epub(extract_dir: str, keep_extracted: bool = False) -> None:
    """
    Clean up extracted EPUB directory

    Args:
        extract_dir: Path to the extracted directory
        keep_extracted: Whether to keep the extracted directory
    """
    if not keep_extracted and os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
