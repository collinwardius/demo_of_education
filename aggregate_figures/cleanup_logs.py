#!/usr/bin/env python3
"""
Cluster Log Cleanup Script

Groups log/error files by job name and extension, keeps the most recent
file in each group, and archives older files to an archive/ subdirectory
with gzip compression.

Usage:
    python cleanup_logs.py [directory]
    
If no directory is specified, uses the current directory.
"""

import os
import sys
import gzip
import shutil
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def parse_log_filename(filename):
    """
    Parse a log filename to extract job name, job ID, and extension.
    
    Expected format: <job_name>_<job_id>.<extension>
    Example: census_pipeline_43513229.err -> ('census_pipeline', '43513229', 'err')
    
    Returns: (job_name, job_id, extension) or None if pattern doesn't match
    """
    pattern = r'^(.+?)_(\d+)\.(log|err|out)$'
    match = re.match(pattern, filename)
    
    if match:
        job_name = match.group(1)
        job_id = match.group(2)
        extension = match.group(3)
        return (job_name, job_id, extension)
    
    return None


def get_file_info(filepath):
    """Get file modification time and size."""
    stat = filepath.stat()
    return {
        'mtime': stat.st_mtime,
        'size': stat.st_size,
        'mtime_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }


def compress_and_move(source_path, archive_dir):
    """Compress a file with gzip and move it to the archive directory."""
    # Create compressed filename
    compressed_name = source_path.name + '.gz'
    dest_path = archive_dir / compressed_name
    
    # Compress and write
    with open(source_path, 'rb') as f_in:
        with gzip.open(dest_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove original file
    source_path.unlink()
    
    return dest_path


def cleanup_logs(directory='.', dry_run=False):
    """
    Clean up log files in the specified directory.
    
    Args:
        directory: Path to directory containing log files
        dry_run: If True, only print what would be done without making changes
    """
    dir_path = Path(directory).resolve()
    
    if not dir_path.exists():
        print(f"Error: Directory '{dir_path}' does not exist")
        return
    
    if not dir_path.is_dir():
        print(f"Error: '{dir_path}' is not a directory")
        return
    
    # Find all log files
    log_files = []
    for filepath in dir_path.iterdir():
        if filepath.is_file():
            parsed = parse_log_filename(filepath.name)
            if parsed:
                job_name, job_id, extension = parsed
                file_info = get_file_info(filepath)
                log_files.append({
                    'path': filepath,
                    'name': filepath.name,
                    'job_name': job_name,
                    'job_id': job_id,
                    'extension': extension,
                    'mtime': file_info['mtime'],
                    'mtime_str': file_info['mtime_str'],
                    'size': file_info['size']
                })
    
    if not log_files:
        print(f"No log files found in {dir_path}")
        return
    
    print(f"Found {len(log_files)} log file(s) in {dir_path}")
    print()
    
    # Group files by (job_name, extension)
    groups = defaultdict(list)
    for file_info in log_files:
        key = (file_info['job_name'], file_info['extension'])
        groups[key].append(file_info)
    
    # Process each group
    archive_dir = dir_path / 'archive'
    files_to_archive = []
    files_to_keep = []
    
    for (job_name, extension), files in sorted(groups.items()):
        # Sort by modification time (most recent first)
        files.sort(key=lambda x: x['mtime'], reverse=True)
        
        # Keep the most recent, archive the rest
        most_recent = files[0]
        older_files = files[1:]
        
        files_to_keep.append(most_recent)
        
        if older_files:
            print(f"\nJob: {job_name}.{extension}")
            print(f"  Keeping: {most_recent['name']} (modified: {most_recent['mtime_str']})")
            print(f"  Archiving {len(older_files)} older file(s):")
            
            for old_file in older_files:
                print(f"    - {old_file['name']} (modified: {old_file['mtime_str']})")
                files_to_archive.append(old_file)
    
    if not files_to_archive:
        print("\nNo files to archive. All files are the latest versions.")
        return
    
    # Summary
    print(f"\n{'='*70}")
    print(f"Summary:")
    print(f"  Total files: {len(log_files)}")
    print(f"  Files to keep: {len(files_to_keep)}")
    print(f"  Files to archive: {len(files_to_archive)}")
    
    if dry_run:
        print(f"\n[DRY RUN] No changes made. Run without --dry-run to archive files.")
        return
    
    # Create archive directory if it doesn't exist
    if not archive_dir.exists():
        print(f"\nCreating archive directory: {archive_dir}")
        archive_dir.mkdir()
    
    # Archive files
    print(f"\nArchiving files to {archive_dir}...")
    archived_count = 0
    total_saved_bytes = 0
    
    for file_info in files_to_archive:
        original_size = file_info['size']
        compressed_path = compress_and_move(file_info['path'], archive_dir)
        compressed_size = compressed_path.stat().st_size
        saved_bytes = original_size - compressed_size
        total_saved_bytes += saved_bytes
        
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        print(f"  ✓ {file_info['name']} -> {compressed_path.name} "
              f"({compression_ratio:.1f}% compression)")
        archived_count += 1
    
    print(f"\n{'='*70}")
    print(f"Done! Archived {archived_count} file(s)")
    print(f"Space saved: {total_saved_bytes / 1024 / 1024:.2f} MB")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clean up cluster log files by archiving older versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean up logs in current directory
  python cleanup_logs.py
  
  # Clean up logs in specific directory
  python cleanup_logs.py /path/to/logs
  
  # Dry run to see what would be archived
  python cleanup_logs.py --dry-run
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory containing log files (default: current directory)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    cleanup_logs(args.directory, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
