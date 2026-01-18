"""
NovelTuner Utilities Package
Shared utility functions for all tools
"""

from .file_utils import *
from .encoding_utils import *
from .backup_utils import *
from .cli_utils import *
from .epub_utils import *

__version__ = "1.0.0"
__all__ = [
    # File utilities
    'get_files_to_process', 'ensure_output_dir', 'safe_write_file',
    # Encoding utilities
    'detect_encoding', 'read_file_with_encoding',
    # Backup utilities
    'create_backup', 'BackupManager',
    # CLI utilities
    'add_common_arguments', 'validate_input_path',
    # EPUB utilities
    'extract_epub', 'create_epub_from_dir', 'find_xhtml_files',
    'read_xhtml_content', 'write_xhtml_content', 'process_epub_text_content',
    'get_epub_metadata', 'cleanup_extracted_epub'
]