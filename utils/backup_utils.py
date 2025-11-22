"""
Backup management utilities for NovelTuner tools
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class BackupManager:
    """Manages backup operations for files"""

    def __init__(self, backup_suffix: str = ".backup"):
        """
        Initialize backup manager

        Args:
            backup_suffix: Suffix to add to backup files
        """
        self.backup_suffix = backup_suffix

    def create_backup(self, file_path: str, timestamp: bool = True) -> Optional[str]:
        """
        Create a backup of the specified file

        Args:
            file_path: Path to file to backup
            timestamp: Whether to add timestamp to backup filename

        Returns:
            Path to backup file, or None if failed
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                print(f"Warning: File {file_path} does not exist, skipping backup")
                return None

            # Generate backup filename
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{file_path_obj.stem}_{timestamp_str}{file_path_obj.suffix}{self.backup_suffix}"
            else:
                backup_name = f"{file_path_obj.name}{self.backup_suffix}"

            backup_path = file_path_obj.parent / backup_name

            # Copy file
            shutil.copy2(file_path, backup_path)

            print(f"Backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            print(f"Error creating backup for {file_path}: {e}")
            return None

    def restore_backup(self, file_path: str, backup_path: Optional[str] = None) -> bool:
        """
        Restore file from backup

        Args:
            file_path: Original file path
            backup_path: Specific backup file to restore from (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_path is None:
                # Find most recent backup
                file_path_obj = Path(file_path)
                backup_pattern = f"{file_path_obj.stem}*{file_path_obj.suffix}{self.backup_suffix}"
                backup_files = list(file_path_obj.parent.glob(backup_pattern))

                if not backup_files:
                    print(f"No backup found for {file_path}")
                    return False

                # Get most recent backup
                backup_path = str(max(backup_files, key=lambda p: p.stat().st_mtime))

            # Restore from backup
            shutil.copy2(backup_path, file_path)
            print(f"Restored {file_path} from {backup_path}")
            return True

        except Exception as e:
            print(f"Error restoring backup for {file_path}: {e}")
            return False

    def cleanup_old_backups(self, file_path: str, keep_count: int = 5) -> int:
        """
        Clean up old backup files, keeping only the specified number

        Args:
            file_path: Original file path
            keep_count: Number of recent backups to keep

        Returns:
            Number of backups removed
        """
        try:
            file_path_obj = Path(file_path)
            backup_pattern = f"{file_path_obj.stem}*{file_path_obj.suffix}{self.backup_suffix}"
            backup_files = list(file_path_obj.parent.glob(backup_pattern))

            if len(backup_files) <= keep_count:
                return 0

            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda p: p.stat().st_mtime)

            # Remove oldest backups
            removed_count = 0
            for backup_file in backup_files[:-keep_count]:
                try:
                    backup_file.unlink()
                    removed_count += 1
                    print(f"Removed old backup: {backup_file}")
                except Exception as e:
                    print(f"Error removing backup {backup_file}: {e}")

            return removed_count

        except Exception as e:
            print(f"Error cleaning up backups for {file_path}: {e}")
            return 0


def create_backup(file_path: str, backup_suffix: str = ".backup", timestamp: bool = True) -> Optional[str]:
    """
    Convenience function to create a backup

    Args:
        file_path: Path to file to backup
        backup_suffix: Suffix for backup files
        timestamp: Whether to add timestamp

    Returns:
        Path to backup file, or None if failed
    """
    backup_manager = BackupManager(backup_suffix)
    return backup_manager.create_backup(file_path, timestamp)


def should_create_backup(backup_enabled: bool, file_path: str) -> bool:
    """
    Determine whether to create a backup based on settings and file existence

    Args:
        backup_enabled: Whether backup is enabled
        file_path: Path to file

    Returns:
        True if backup should be created
    """
    if not backup_enabled:
        return False

    if not os.path.exists(file_path):
        return False

    return True