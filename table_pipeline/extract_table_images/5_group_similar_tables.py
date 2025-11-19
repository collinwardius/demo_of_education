#!/usr/bin/env python3
"""
Group similar tables based on CSV structure and content analysis.
"""

import os
import csv
import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import hashlib


def extract_table_metadata(csv_path: str) -> Dict:
    """Extract metadata from a CSV file."""
    metadata = {
        'path': csv_path,
        'filename': os.path.basename(csv_path),
        'headers': [],
        'num_columns': 0,
        'num_rows': 0,
        'column_types': [],
        'table_title': None,
        'has_numeric_data': False,
        'header_hash': None,
    }

    # Extract table title from filename
    filename = os.path.basename(csv_path)
    # Pattern: page_XXX_table_YYY_TITLE.csv or page_XXX_table_YYY.csv
    title_match = re.search(r'table_\d+[-_](.+)\.csv$', filename)
    if title_match:
        metadata['table_title'] = title_match.group(1).strip('-_')

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

            if not rows:
                return metadata

            # Get headers (first row)
            metadata['headers'] = rows[0] if rows else []
            metadata['num_columns'] = len(metadata['headers'])
            metadata['num_rows'] = len(rows) - 1  # Exclude header row

            # Create a hash of headers for similarity comparison
            header_str = '|'.join([h.lower().strip() for h in metadata['headers']])
            metadata['header_hash'] = hashlib.md5(header_str.encode()).hexdigest()

            # Analyze column types by sampling data
            if len(rows) > 1:
                sample_rows = rows[1:min(6, len(rows))]  # Sample up to 5 rows
                for col_idx in range(metadata['num_columns']):
                    col_values = [row[col_idx] if col_idx < len(row) else ''
                                for row in sample_rows]

                    # Check if column contains numeric data
                    numeric_count = 0
                    for val in col_values:
                        val_clean = val.strip().replace(',', '').replace('$', '')
                        try:
                            float(val_clean)
                            numeric_count += 1
                            metadata['has_numeric_data'] = True
                        except ValueError:
                            pass

                    if numeric_count > len(col_values) / 2:
                        metadata['column_types'].append('numeric')
                    else:
                        metadata['column_types'].append('text')

    except Exception as e:
        print(f"Error reading {csv_path}: {e}")

    return metadata


def group_tables_by_similarity(csv_dir: str) -> Dict[str, List[Dict]]:
    """Group tables based on multiple similarity criteria."""

    # Find all CSV files
    csv_files = list(Path(csv_dir).glob('*.csv'))
    print(f"Found {len(csv_files)} CSV files")

    # Extract metadata for all files
    print("Analyzing CSV files...")
    all_metadata = []
    for csv_file in csv_files:
        metadata = extract_table_metadata(str(csv_file))
        all_metadata.append(metadata)

    # Group by different criteria
    groups = {
        'by_title_pattern': defaultdict(list),
        'by_header_similarity': defaultdict(list),
        'by_structure': defaultdict(list),
        'by_table_number': defaultdict(list),
    }

    # Group by title pattern (e.g., "table 26", "table 29")
    for metadata in all_metadata:
        filename = metadata['filename']

        # Extract table number/name from filename
        table_num_match = re.search(r'table_(\d+)[-_]', filename)
        if table_num_match:
            table_num = table_num_match.group(1)
            groups['by_table_number'][f"Table_{table_num}"].append(metadata)

        # Group by title pattern
        if metadata['table_title']:
            # Clean up title for grouping
            title = metadata['table_title']

            # Check for common patterns
            if 'privately' in title.lower() and 'controlled' in title.lower():
                groups['by_title_pattern']['Privately_Controlled_Institutions'].append(metadata)
            elif 'publicly' in title.lower() and 'controlled' in title.lower():
                groups['by_title_pattern']['Publicly_Controlled_Institutions'].append(metadata)
            elif 'normal school' in title.lower():
                groups['by_title_pattern']['State_Normal_Schools'].append(metadata)
            elif 'teachers college' in title.lower():
                groups['by_title_pattern']['Teachers_Colleges'].append(metadata)
            elif 'engineering' in title.lower():
                groups['by_title_pattern']['Engineering_Programs'].append(metadata)
            elif 'enrollment' in title.lower():
                groups['by_title_pattern']['Enrollment_Data'].append(metadata)
            elif 'property' in title.lower():
                groups['by_title_pattern']['Property_Data'].append(metadata)
            elif 'receipt' in title.lower():
                groups['by_title_pattern']['Financial_Receipts'].append(metadata)
            elif 'endowment' in title.lower():
                groups['by_title_pattern']['Endowment_Data'].append(metadata)
            elif 'instructor' in title.lower() or 'teacher' in title.lower():
                groups['by_title_pattern']['Instructor_Data'].append(metadata)
            elif 'student' in title.lower():
                groups['by_title_pattern']['Student_Data'].append(metadata)
        else:
            # No title - group by page number pattern
            page_match = re.search(r'page_(\d+)', filename)
            if page_match:
                page_num = int(page_match.group(1))
                page_range = f"Pages_{(page_num // 100) * 100}-{((page_num // 100) + 1) * 100}"
                groups['by_title_pattern'][f'Untitled_{page_range}'].append(metadata)

    # Group by header similarity (exact match)
    for metadata in all_metadata:
        if metadata['header_hash']:
            groups['by_header_similarity'][metadata['header_hash']].append(metadata)

    # Group by structure (num_columns x num_rows pattern)
    for metadata in all_metadata:
        structure_key = f"{metadata['num_columns']}cols_x_{metadata['num_rows']}rows"
        groups['by_structure'][structure_key].append(metadata)

    return groups


def generate_report(groups: Dict[str, List[Dict]], output_file: str):
    """Generate a detailed report of table groupings."""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("TABLE GROUPING ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")

        # Report by title pattern (most useful grouping)
        f.write("\n" + "=" * 80 + "\n")
        f.write("GROUPING BY TITLE/CONTENT PATTERN\n")
        f.write("=" * 80 + "\n\n")

        title_groups = groups['by_title_pattern']
        for group_name in sorted(title_groups.keys()):
            tables = title_groups[group_name]
            if len(tables) > 1:  # Only show groups with multiple tables
                f.write(f"\n{group_name} ({len(tables)} tables)\n")
                f.write("-" * 80 + "\n")

                # Sample a few tables from the group
                for i, table in enumerate(sorted(tables, key=lambda x: x['filename'])[:5]):
                    f.write(f"  • {table['filename']}\n")
                    f.write(f"    Columns: {table['num_columns']}, Rows: {table['num_rows']}\n")
                    if table['headers']:
                        f.write(f"    Headers: {', '.join(table['headers'][:5])}")
                        if len(table['headers']) > 5:
                            f.write(f" ... (+{len(table['headers'])-5} more)")
                        f.write("\n")

                if len(tables) > 5:
                    f.write(f"  ... and {len(tables) - 5} more tables\n")

        # Report by table number
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("GROUPING BY TABLE NUMBER (Multi-page tables)\n")
        f.write("=" * 80 + "\n\n")

        table_num_groups = groups['by_table_number']
        for table_num in sorted(table_num_groups.keys()):
            tables = table_num_groups[table_num]
            if len(tables) > 1:  # Only show table numbers that span multiple pages
                f.write(f"\n{table_num} ({len(tables)} pages)\n")
                f.write("-" * 80 + "\n")

                for table in sorted(tables, key=lambda x: x['filename']):
                    page_match = re.search(r'page_(\d+)', table['filename'])
                    page_num = page_match.group(1) if page_match else "?"
                    f.write(f"  • Page {page_num}: {table['filename']}\n")
                    if table['table_title']:
                        f.write(f"    Title: {table['table_title']}\n")

        # Report by header similarity
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("GROUPING BY IDENTICAL HEADERS\n")
        f.write("=" * 80 + "\n\n")

        header_groups = groups['by_header_similarity']
        header_group_list = [(hash_val, tables) for hash_val, tables in header_groups.items() if len(tables) > 1]
        header_group_list.sort(key=lambda x: len(x[1]), reverse=True)

        for i, (hash_val, tables) in enumerate(header_group_list[:10], 1):  # Top 10
            f.write(f"\nHeader Group {i} ({len(tables)} tables with identical headers)\n")
            f.write("-" * 80 + "\n")
            if tables[0]['headers']:
                f.write(f"Headers: {', '.join(tables[0]['headers'])}\n\n")

            for table in sorted(tables, key=lambda x: x['filename'])[:5]:
                f.write(f"  • {table['filename']}\n")

            if len(tables) > 5:
                f.write(f"  ... and {len(tables) - 5} more tables\n")

        # Summary statistics
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("SUMMARY STATISTICS\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total CSV files analyzed: {sum(len(tables) for tables in title_groups.values())}\n")
        f.write(f"Content-based groups: {len([g for g in title_groups.values() if len(g) > 1])}\n")
        f.write(f"Multi-page table series: {len([g for g in table_num_groups.values() if len(g) > 1])}\n")
        f.write(f"Unique header patterns: {len(header_groups)}\n")
        f.write(f"Header groups with 2+ tables: {len([g for g in header_groups.values() if len(g) > 1])}\n")


def generate_json_output(groups: Dict[str, List[Dict]], output_file: str):
    """Generate JSON output with all groupings."""

    # Convert to serializable format
    json_data = {
        'summary': {
            'total_tables': sum(len(tables) for tables in groups['by_title_pattern'].values()),
            'groups': {}
        },
        'groups': {}
    }

    # Add title pattern groups
    for group_name, tables in groups['by_title_pattern'].items():
        if len(tables) > 1:
            json_data['groups'][group_name] = {
                'count': len(tables),
                'files': [t['filename'] for t in sorted(tables, key=lambda x: x['filename'])],
                'sample_metadata': {
                    'columns': tables[0]['num_columns'],
                    'headers': tables[0]['headers']
                }
            }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    csv_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/pdf_extractor/scans/extracted_tables/biennial_20_22/college_analysis/college_tables/csv"
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/pdf_extractor/scans/extracted_tables/biennial_20_22/college_analysis"

    print("Starting table grouping analysis...")
    groups = group_tables_by_similarity(csv_dir)

    report_file = os.path.join(output_dir, "table_grouping_report.txt")
    json_file = os.path.join(output_dir, "table_grouping.json")

    print(f"Generating report: {report_file}")
    generate_report(groups, report_file)

    print(f"Generating JSON: {json_file}")
    generate_json_output(groups, json_file)

    print("\nDone! Check the output files for results.")
