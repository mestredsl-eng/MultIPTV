"""Automatic backup service for database."""

import shutil
from pathlib import Path
from datetime import datetime


def create_backup(db_path, backup_dir):
    """Create automatic backup of database before critical operations."""
    db_path = Path(db_path)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    backup_file = backup_dir / f'iptv_{timestamp}.db'
    
    # Copy database file
    shutil.copy2(db_path, backup_file)
    
    return str(backup_file)


def cleanup_old_backups(backup_dir, keep_days=7):
    """Clean up old backups older than specified days."""
    backup_dir = Path(backup_dir)
    
    if not backup_dir.exists():
        return
    
    cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    
    for backup_file in backup_dir.glob('iptv_*.db'):
        if backup_file.stat().st_mtime < cutoff_date:
            backup_file.unlink()
