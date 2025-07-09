#!/usr/bin/env python
"""
Backup script for IntelliDocs data
"""
import os
import sys
import subprocess
import datetime
from pathlib import Path

def backup_database():
    """Backup PostgreSQL database"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    backup_file = backup_dir / f'intellidocs_db_{timestamp}.sql'
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'postgres'),
        'database': os.getenv('DB_NAME', 'intellidocs'),
    }
    
    # Create pg_dump command
    cmd = [
        'pg_dump',
        '-h', db_params['host'],
        '-p', db_params['port'],
        '-U', db_params['user'],
        '-f', str(backup_file),
        '--clean',
        '--no-owner',
        '--no-privileges',
        db_params['database']
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Database backup created: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Database backup failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def backup_media_files():
    """Backup media files"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    media_dir = Path('media')
    if not media_dir.exists():
        print("📁 No media directory found, skipping media backup")
        return None
    
    backup_file = backup_dir / f'intellidocs_media_{timestamp}.tar.gz'
    
    cmd = [
        'tar',
        '-czf',
        str(backup_file),
        '-C',
        str(media_dir.parent),
        str(media_dir.name)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Media files backup created: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Media backup failed: {e}")
        return None

def cleanup_old_backups(days=30):
    """Remove backups older than specified days"""
    backup_dir = Path('backups')
    if not backup_dir.exists():
        return
    
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    
    for backup_file in backup_dir.glob('intellidocs_*'):
        if backup_file.stat().st_mtime < cutoff_date.timestamp():
            try:
                backup_file.unlink()
                print(f"🗑️ Removed old backup: {backup_file}")
            except Exception as e:
                print(f"❌ Failed to remove {backup_file}: {e}")

def main():
    print("🚀 Starting IntelliDocs backup process...")
    
    # Create backups
    db_backup = backup_database()
    media_backup = backup_media_files()
    
    # Cleanup old backups
    cleanup_old_backups()
    
    # Summary
    print("\n📊 Backup Summary:")
    print(f"  Database backup: {'✅' if db_backup else '❌'}")
    print(f"  Media backup: {'✅' if media_backup else '❌'}")
    
    if db_backup or media_backup:
        print("✅ Backup process completed successfully!")
    else:
        print("❌ Backup process failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()