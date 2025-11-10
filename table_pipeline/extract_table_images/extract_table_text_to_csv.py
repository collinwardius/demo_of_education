#!/usr/bin/env python3
"""
Extract table text from saved Textract blocks and export to CSV files.

This script reads a JSON file (from extract_table_bboxes_simple.py) that contains
all Textract blocks and extracts the text content from each table into CSV files.
"""

import json
import argparse
from pathlib import Path
import csv
import re
from typing import List, Dict, Any


def sanitize_filename(text: str, max_length: int = 100) -> str:
    """
    Sanitize text for use in filename.

    Args:
        text: Text to sanitize
        max_length: Maximum filename length

    Returns:
        Sanitized filename string
    """
    if not text:
        return "untitled"

    # Remove or replace invalid filename characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)

    # Replace spaces and periods with underscores
    text = re.sub(r'[\s.]+', '_', text)

    # Remove multiple consecutive underscores
    text = re.sub(r'_+', '_', text)

    # Remove leading/trailing underscores
    text = text.strip('_')

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rstrip('_')

    return text.lower() if text else "untitled"


def extract_table_to_grid(table_id: str, block_map: Dict[str, Dict]) -> List[List[str]]:
    """
    Extract table text organized as a 2D grid.

    Args:
        table_id: Table block ID
        block_map: Dictionary mapping block IDs to blocks

    Returns:
        2D list representing the table grid
    """
    table_block = block_map.get(table_id)
    if not table_block:
        return []

    # Get all cell IDs for this table
    cell_ids = []
    if 'Relationships' in table_block:
        for relationship in table_block['Relationships']:
            if relationship['Type'] == 'CHILD':
                cell_ids = relationship['Ids']
                break

    if not cell_ids:
        return []

    # Collect cell information
    cells = []
    max_row = 0
    max_col = 0

    for cell_id in cell_ids:
        cell_block = block_map.get(cell_id)
        if not cell_block or cell_block.get('BlockType') != 'CELL':
            continue

        row_index = cell_block.get('RowIndex', 1)
        col_index = cell_block.get('ColumnIndex', 1)
        row_span = cell_block.get('RowSpan', 1)
        col_span = cell_block.get('ColumnSpan', 1)

        # Extract text from cell
        cell_text = ''
        if 'Relationships' in cell_block:
            for rel in cell_block['Relationships']:
                if rel['Type'] == 'CHILD':
                    # Get text from child WORD blocks
                    words = []
                    for word_id in rel['Ids']:
                        word_block = block_map.get(word_id)
                        if word_block and 'Text' in word_block:
                            words.append(word_block['Text'])
                    cell_text = ' '.join(words)

        cells.append({
            'row': row_index,
            'col': col_index,
            'row_span': row_span,
            'col_span': col_span,
            'text': cell_text
        })

        max_row = max(max_row, row_index + row_span - 1)
        max_col = max(max_col, col_index + col_span - 1)

    # Build grid
    grid = [['' for _ in range(max_col)] for _ in range(max_row)]

    # Fill grid with cell text
    for cell in cells:
        row = cell['row'] - 1  # Convert to 0-indexed
        col = cell['col'] - 1
        text = cell['text']

        # Handle merged cells by filling all spanned positions
        for r in range(row, min(row + cell['row_span'], max_row)):
            for c in range(col, min(col + cell['col_span'], max_col)):
                if r < max_row and c < max_col:
                    grid[r][c] = text

    return grid


def process_json(json_path: str, output_dir: str):
    """
    Process JSON file and extract all tables to CSV.

    Args:
        json_path: Path to JSON file with table metadata and blocks
        output_dir: Directory to save CSV files
    """
    # Load JSON data
    print(f"Loading data from {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Check if all_blocks exists in the JSON
    if 'all_blocks' not in data:
        print("ERROR: This JSON file doesn't contain 'all_blocks'.")
        print("Please re-run extract_table_bboxes_simple.py to generate a new JSON file with all blocks.")
        return

    all_blocks = data['all_blocks']
    tables = data.get('tables', [])

    print(f"Found {len(tables)} tables to extract")
    print(f"Loaded {len(all_blocks)} blocks")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Build block lookup map
    block_map = {block['Id']: block for block in all_blocks}

    # Track filenames for duplicates
    filename_counts = {}

    # Extract each table
    for i, table_metadata in enumerate(tables, 1):
        table_id = table_metadata['id']
        page = table_metadata['page']
        title = table_metadata.get('title', None)
        confidence = table_metadata.get('confidence', 0)

        title_str = f"\"{title}\"" if title else "No title"
        print(f"\nExtracting Table {i}/{len(tables)}: Page {page}, Title: {title_str}")

        # Extract table grid
        grid = extract_table_to_grid(table_id, block_map)

        if not grid:
            print(f"  Warning: No cells found for table {i}")
            continue

        print(f"  Table size: {len(grid)} rows x {len(grid[0]) if grid else 0} columns")

        # Create CSV filename matching PNG naming convention
        if title:
            sanitized_title = sanitize_filename(title, max_length=80)
            base_filename = f"page_{page:03d}_{sanitized_title}"
        else:
            base_filename = f"page_{page:03d}_table_{i:03d}"

        # Handle duplicate filenames
        if base_filename in filename_counts:
            filename_counts[base_filename] += 1
            csv_filename = f"{base_filename}_{filename_counts[base_filename]}.csv"
        else:
            filename_counts[base_filename] = 0
            csv_filename = f"{base_filename}.csv"

        # Save to CSV
        csv_path = output_path / csv_filename

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(grid)

        print(f"  Saved: {csv_filename}")

    print(f"\nDone! Extracted {len(tables)} tables to {output_dir}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract table text from saved Textract blocks and export to CSV files'
    )
    parser.add_argument(
        'json_file',
        help='Path to JSON file with table metadata and blocks (from extract_table_bboxes_simple.py)'
    )
    parser.add_argument(
        'output_dir',
        help='Directory to save CSV files'
    )

    args = parser.parse_args()

    process_json(args.json_file, args.output_dir)

    print("\nDone!")


if __name__ == '__main__':
    main()
