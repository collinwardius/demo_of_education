#!/usr/bin/env python3
"""
Identify and filter college-related tables from extracted Textract results.

This script analyzes table titles and page locations to identify tables related to
colleges, universities, and higher education.
"""

import argparse
import json
import csv
import shutil
from pathlib import Path
from typing import List, Dict, Tuple


# College-related keywords to search for in titles
COLLEGE_KEYWORDS = [
    'college', 'university', 'universities', 'collegiate',
    'ph.d', 'ph. d', 'professor', 'graduate', 'undergraduate',
    'higher education', 'normal school'
]


def load_textract_data(json_path: str) -> dict:
    """Load Textract JSON data."""
    with open(json_path, 'r') as f:
        return json.load(f)


def has_college_keyword(title: str) -> bool:
    """Check if title contains college-related keywords."""
    if not title:
        return False
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in COLLEGE_KEYWORDS)


def identify_college_tables(
    data: dict,
    filter_level: str = 'medium'
) -> Tuple[List[dict], Dict[str, int]]:
    """
    Identify college-related tables.

    Args:
        data: Textract JSON data
        filter_level: 'strict' or 'medium'
            strict: Only keyword matches
            medium: Keywords + continuation tables (recommended)

    Returns:
        Tuple of (college_tables list, statistics dict)
    """
    college_tables = []
    prev_was_college = False
    prev_title = None

    stats = {
        'total_tables': len(data['tables']),
        'keyword_matches': 0,
        'continuation_tables': 0
    }

    for i, table in enumerate(data['tables']):
        table_num = i + 1
        page = table.get('page', 0)
        title = table.get('title')
        confidence = table.get('confidence', 0)

        is_college = False
        reason = None

        # Method 1: Keyword match
        if has_college_keyword(title):
            is_college = True
            reason = 'keyword_match'
            stats['keyword_matches'] += 1
            prev_was_college = True
            prev_title = title

        # Method 2: Continuation of previous college table (no title)
        elif filter_level == 'medium':
            if not title and prev_was_college:
                is_college = True
                reason = 'continuation'
                stats['continuation_tables'] += 1
            else:
                prev_was_college = False
        else:
            # strict mode: reset tracking
            prev_was_college = False

        if is_college:
            college_tables.append({
                'table_number': table_num,
                'page': page,
                'title': title if title else f'(Continuation of: {prev_title})' if reason == 'continuation' else '(No title)',
                'confidence': confidence,
                'reason': reason,
                'id': table.get('id'),
                'bounding_box': table.get('bounding_box'),
            })

    stats['college_tables_found'] = len(college_tables)

    return college_tables, stats


def save_college_tables_json(college_tables: List[dict], output_path: str):
    """Save college tables list as JSON."""
    with open(output_path, 'w') as f:
        json.dump(college_tables, f, indent=2)
    print(f'Saved {len(college_tables)} college tables to: {output_path}')


def save_college_tables_csv(college_tables: List[dict], output_path: str):
    """Save college tables list as CSV."""
    if not college_tables:
        print('No college tables to save to CSV')
        return

    with open(output_path, 'w', newline='') as f:
        fieldnames = ['table_number', 'page', 'title', 'confidence', 'reason']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for table in college_tables:
            writer.writerow({
                'table_number': table['table_number'],
                'page': table['page'],
                'title': table['title'],
                'confidence': table['confidence'],
                'reason': table['reason']
            })

    print(f'Saved college tables CSV to: {output_path}')


def copy_college_files(
    college_tables: List[dict],
    source_png_dir: str,
    source_csv_dir: str,
    dest_dir: str
):
    """Copy PNG and CSV files for college tables to a separate directory."""
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    png_dest = dest_path / 'png'
    csv_dest = dest_path / 'csv'
    png_dest.mkdir(exist_ok=True)
    csv_dest.mkdir(exist_ok=True)

    source_png_path = Path(source_png_dir)
    source_csv_path = Path(source_csv_dir)

    copied_png = 0
    copied_csv = 0

    # Get list of all PNG and CSV files
    png_files = {f.name: f for f in source_png_path.glob('*.png')}
    csv_files = {f.name: f for f in source_csv_path.glob('*.csv')}

    for table in college_tables:
        page = table['page']

        # Find matching files (they start with page_XXX)
        page_prefix = f'page_{page:03d}_'

        for filename, filepath in png_files.items():
            if filename.startswith(page_prefix):
                shutil.copy2(filepath, png_dest / filename)
                copied_png += 1

        for filename, filepath in csv_files.items():
            if filename.startswith(page_prefix):
                shutil.copy2(filepath, csv_dest / filename)
                copied_csv += 1

    print(f'\nCopied {copied_png} PNG files to: {png_dest}')
    print(f'Copied {copied_csv} CSV files to: {csv_dest}')


def print_statistics(stats: Dict[str, int], filter_level: str):
    """Print statistics report."""
    print('\n' + '='*60)
    print('COLLEGE TABLES IDENTIFICATION STATISTICS')
    print('='*60)
    print(f'Filter level: {filter_level}')
    print(f'\nTotal tables in document: {stats["total_tables"]}')
    print(f'College tables identified: {stats["college_tables_found"]}')
    print(f'  - Keyword matches: {stats["keyword_matches"]}')
    print(f'  - Continuation tables: {stats["continuation_tables"]}')
    print(f'\nPercentage of tables: {stats["college_tables_found"] / stats["total_tables"] * 100:.1f}%')
    print('='*60)


def save_statistics_report(stats: Dict[str, int], filter_level: str, output_path: str):
    """Save statistics to a text file."""
    with open(output_path, 'w') as f:
        f.write('='*60 + '\n')
        f.write('COLLEGE TABLES IDENTIFICATION STATISTICS\n')
        f.write('='*60 + '\n')
        f.write(f'Filter level: {filter_level}\n\n')
        f.write(f'Total tables in document: {stats["total_tables"]}\n')
        f.write(f'College tables identified: {stats["college_tables_found"]}\n')
        f.write(f'  - Keyword matches: {stats["keyword_matches"]}\n')
        f.write(f'  - Continuation tables: {stats["continuation_tables"]}\n')
        f.write(f'\nPercentage of tables: {stats["college_tables_found"] / stats["total_tables"] * 100:.1f}%\n')
        f.write('='*60 + '\n')

    print(f'\nSaved statistics report to: {output_path}')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Identify and filter college-related tables from Textract results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Filter Levels:
  strict  - Only tables with college keywords in title (most conservative)
  medium  - Keywords + untitled continuation tables (recommended)

Example usage:
  python3 4_identify_college_tables.py \\
    /path/to/textract.json \\
    /path/to/output_dir \\
    --filter medium \\
    --copy-files

This will:
  1. Identify college-related tables using keyword matching
  2. Save list as JSON and CSV
  3. Copy matching PNG/CSV files to separate directory
  4. Generate statistics report
        """
    )

    parser.add_argument(
        'json_file',
        help='Path to Textract JSON file'
    )
    parser.add_argument(
        'output_dir',
        help='Directory to save results'
    )
    parser.add_argument(
        '--filter',
        choices=['strict', 'medium'],
        default='medium',
        help='Filter level for identifying college tables (default: medium)'
    )
    parser.add_argument(
        '--copy-files',
        action='store_true',
        help='Copy PNG and CSV files for college tables to separate directory'
    )
    parser.add_argument(
        '--source-png-dir',
        help='Source directory containing PNG files (required with --copy-files)'
    )
    parser.add_argument(
        '--source-csv-dir',
        help='Source directory containing CSV files (required with --copy-files)'
    )

    args = parser.parse_args()

    # Validate copy-files arguments
    if args.copy_files:
        if not args.source_png_dir or not args.source_csv_dir:
            parser.error('--copy-files requires --source-png-dir and --source-csv-dir')

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print('Loading Textract data...')
    data = load_textract_data(args.json_file)

    print(f'Identifying college tables (filter: {args.filter})...')
    college_tables, stats = identify_college_tables(data, args.filter)

    # Save results
    json_output = output_path / 'college_tables.json'
    csv_output = output_path / 'college_tables.csv'
    stats_output = output_path / 'college_statistics.txt'

    save_college_tables_json(college_tables, str(json_output))
    save_college_tables_csv(college_tables, str(csv_output))
    save_statistics_report(stats, args.filter, str(stats_output))

    # Print statistics
    print_statistics(stats, args.filter)

    # Copy files if requested
    if args.copy_files:
        print('\nCopying college table files...')
        college_files_dir = output_path / 'college_tables'
        copy_college_files(
            college_tables,
            args.source_png_dir,
            args.source_csv_dir,
            str(college_files_dir)
        )

    print('\n✓ Complete!')
    print(f'\nResults saved to: {args.output_dir}')


if __name__ == '__main__':
    main()
