#!/usr/bin/env python3
"""
Cleanup script for Django Library Management System
Removes unnecessary files and directories for cloud deployment
"""

import os
import shutil
import sys
from pathlib import Path


def log_info(message):
    """Log info message."""
    print(f"✅ {message}")


def log_warn(message):
    """Log warning message."""
    print(f"⚠️  {message}")


def log_error(message):
    """Log error message."""
    print(f"❌ {message}")


def remove_file(file_path):
    """Remove a file if it exists."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            log_info(f"Removed file: {file_path}")
        except Exception as e:
            log_error(f"Failed to remove file {file_path}: {e}")
    else:
        log_warn(f"File not found: {file_path}")


def remove_directory(dir_path):
    """Remove a directory if it exists."""
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            log_info(f"Removed directory: {dir_path}")
        except Exception as e:
            log_error(f"Failed to remove directory {dir_path}: {e}")
    else:
        log_warn(f"Directory not found: {dir_path}")


def clean_log_files():
    """Clean log files."""
    log_info("Cleaning log files...")
    
    log_files = [
        "logging/book.admin.log",
        "logging/performance.log",
        "logging/book.performance.log",
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                # Keep the file but empty it
                with open(log_file, 'w') as f:
                    f.write("")
                log_info(f"Cleared log file: {log_file}")
            except Exception as e:
                log_error(f"Failed to clear log file {log_file}: {e}")


def clean_cache_files():
    """Clean Python cache files."""
    log_info("Cleaning Python cache files...")
    
    for root, dirs, files in os.walk("."):
        # Remove __pycache__ directories
        for dir_name in dirs[:]:
            if dir_name == "__pycache__":
                cache_path = os.path.join(root, dir_name)
                remove_directory(cache_path)
                dirs.remove(dir_name)
        
        # Remove .pyc files
        for file_name in files:
            if file_name.endswith(('.pyc', '.pyo')):
                file_path = os.path.join(root, file_name)
                remove_file(file_path)


def clean_development_files():
    """Clean development-specific files."""
    log_info("Cleaning development files...")
    
    dev_files = [
        "migrate_comments.py",
        "run_ruff.py",
        "db.sqlite3",
        "db.sqlite3-journal",
        ".coverage",
        "coverage.xml",
        "htmlcov",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    ]
    
    for item in dev_files:
        if os.path.isfile(item):
            remove_file(item)
        elif os.path.isdir(item):
            remove_directory(item)


def clean_virtual_environments():
    """Clean virtual environment directories."""
    log_info("Cleaning virtual environment directories...")
    
    venv_dirs = [
        "env",
        "venv",
        ".venv",
        ".env",
        "ENV",
        "env.bak",
        "venv.bak",
    ]
    
    for venv_dir in venv_dirs:
        if os.path.isdir(venv_dir):
            remove_directory(venv_dir)


def clean_datacenter_files():
    """Clean datacenter CSV files."""
    log_info("Cleaning datacenter files...")
    
    datacenter_path = "datacenter"
    if os.path.exists(datacenter_path):
        for file_name in os.listdir(datacenter_path):
            if file_name.endswith('.csv'):
                file_path = os.path.join(datacenter_path, file_name)
                remove_file(file_path)


def clean_media_files():
    """Clean user-uploaded media files (optional)."""
    log_info("Cleaning media files...")
    
    # Be careful with this - you might want to keep some media files
    # This is commented out by default
    # media_path = "media"
    # if os.path.exists(media_path):
    #     for root, dirs, files in os.walk(media_path):
    #         for file_name in files:
    #             if not file_name.startswith('.'):
    #                 file_path = os.path.join(root, file_name)
    #                 remove_file(file_path)
    
    log_warn("Media files cleanup skipped (uncomment in script if needed)")


def clean_ide_files():
    """Clean IDE-specific files."""
    log_info("Cleaning IDE files...")
    
    ide_items = [
        ".vscode",
        ".idea",
        "*.sublime-project",
        "*.sublime-workspace",
        ".spyderproject",
        ".spyproject",
        ".ropeproject",
    ]
    
    for item in ide_items:
        if '*' in item:
            # Handle glob patterns
            import glob
            for match in glob.glob(item):
                if os.path.isfile(match):
                    remove_file(match)
                elif os.path.isdir(match):
                    remove_directory(match)
        else:
            if os.path.isfile(item):
                remove_file(item)
            elif os.path.isdir(item):
                remove_directory(item)


def clean_os_files():
    """Clean OS-specific files."""
    log_info("Cleaning OS files...")
    
    os_files = [
        ".DS_Store",
        "Thumbs.db",
        "ehthumbs.db",
        "Desktop.ini",
    ]
    
    for root, dirs, files in os.walk("."):
        for file_name in files:
            if file_name in os_files:
                file_path = os.path.join(root, file_name)
                remove_file(file_path)


def clean_temporary_files():
    """Clean temporary files."""
    log_info("Cleaning temporary files...")
    
    temp_extensions = ['.tmp', '.temp', '.swp', '.swo', '~']
    
    for root, dirs, files in os.walk("."):
        for file_name in files:
            if any(file_name.endswith(ext) for ext in temp_extensions):
                file_path = os.path.join(root, file_name)
                remove_file(file_path)


def main():
    """Main cleanup function."""
    print("🧹 Starting cleanup for cloud deployment...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("manage.py"):
        log_error("manage.py not found. Please run this script from the Django project root.")
        sys.exit(1)
    
    # Run cleanup functions
    clean_cache_files()
    clean_development_files()
    clean_virtual_environments()
    clean_log_files()
    clean_datacenter_files()
    clean_media_files()
    clean_ide_files()
    clean_os_files()
    clean_temporary_files()
    
    print("=" * 50)
    log_info("Cleanup completed successfully!")
    log_info("Your project is now ready for cloud deployment.")
    
    print("\n📋 Next steps:")
    print("1. Review the cleaned files")
    print("2. Update your .env file with production settings")
    print("3. Test your application locally")
    print("4. Deploy to your cloud platform")


if __name__ == "__main__":
    main() 