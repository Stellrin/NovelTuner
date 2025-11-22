"""
Encoding detection and handling utilities for NovelTuner tools
"""

import chardet
from typing import Optional, Tuple


def detect_encoding(file_path: str, confidence_threshold: float = 0.7) -> Tuple[str, float]:
    """
    Detect file encoding using chardet

    Args:
        file_path: Path to file
        confidence_threshold: Minimum confidence level to accept detection

    Returns:
        Tuple of (encoding, confidence)
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()

        if not raw_data:
            return 'utf-8', 1.0  # Default for empty files

        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0.0)

        # Handle common encoding aliases
        if encoding:
            encoding = encoding.lower().replace('gb2312', 'gbk')
            encoding = encoding.replace('big5-hkscs', 'big5')

        if confidence < confidence_threshold:
            # Fall back to common encodings
            for fallback_encoding in ['utf-8', 'gbk', 'big5', 'utf-16']:
                try:
                    raw_data.decode(fallback_encoding)
                    return fallback_encoding, 0.5  # Lower confidence
                except UnicodeDecodeError:
                    continue

        return encoding or 'utf-8', confidence

    except Exception as e:
        print(f"Warning: Failed to detect encoding for {file_path}: {e}")
        return 'utf-8', 0.0


def read_file_with_encoding(file_path: str, encoding: Optional[str] = None) -> Tuple[str, str]:
    """
    Read file with automatic encoding detection if not specified

    Args:
        file_path: Path to file
        encoding: Specific encoding to use (optional)

    Returns:
        Tuple of (content, detected_encoding)
    """
    if encoding is None:
        encoding, confidence = detect_encoding(file_path)
        if confidence < 0.7:
            print(f"Warning: Low confidence ({confidence:.2f}) for encoding detection of {file_path}")

    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        return content, encoding

    except Exception as e:
        # Try common fallback encodings
        for fallback_encoding in ['utf-8', 'gbk', 'big5', 'utf-16', 'latin1']:
            if fallback_encoding == encoding:
                continue
            try:
                with open(file_path, 'r', encoding=fallback_encoding, errors='replace') as f:
                    content = f.read()
                print(f"Warning: Used fallback encoding {fallback_encoding} for {file_path}")
                return content, fallback_encoding
            except Exception:
                continue

        raise IOError(f"Failed to read file {file_path} with any encoding: {e}")


def get_encoding_info(file_path: str) -> dict:
    """
    Get detailed encoding information for a file

    Args:
        file_path: Path to file

    Returns:
        Dictionary with encoding information
    """
    encoding, confidence = detect_encoding(file_path)

    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()

        return {
            'file_path': file_path,
            'detected_encoding': encoding,
            'confidence': confidence,
            'file_size': len(raw_data),
            'is_utf8_with_bom': raw_data.startswith(b'\xef\xbb\xbf'),
            'has_binary_content': b'\x00' in raw_data
        }
    except Exception as e:
        return {
            'file_path': file_path,
            'error': str(e)
        }


def convert_encoding(input_file: str, output_file: str, target_encoding: str = 'utf-8') -> bool:
    """
    Convert file from detected encoding to target encoding

    Args:
        input_file: Input file path
        output_file: Output file path
        target_encoding: Target encoding

    Returns:
        True if successful, False otherwise
    """
    try:
        content, source_encoding = read_file_with_encoding(input_file)

        # Write with target encoding
        with open(output_file, 'w', encoding=target_encoding, newline='') as f:
            f.write(content)

        print(f"Converted {input_file} from {source_encoding} to {target_encoding}")
        return True

    except Exception as e:
        print(f"Error converting encoding for {input_file}: {e}")
        return False