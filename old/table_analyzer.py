#!/usr/bin/env python3
"""
Table Title Analyzer

This script analyzes the analyzeDocResponse.json file to determine distinct tables
based on their titles and outputs the number of different tables along with
their page ranges.
"""

import json
import re


def find_table_title_on_page(page_num: int, blocks: list) -> str:
    """Find table title on a specific page by looking for 'TABLE [number]' or 'table [number]' text."""
    
    for block in blocks:
        if block.get('Page') == page_num and block['BlockType'] == 'LINE':
            if 'Text' in block:
                text = block['Text'].strip()
                # Look for "TABLE [number]" pattern (case insensitive)
                match = re.search(r'table\s+(\d+)', text.lower())
                if match:
                    # Preserve original case from the document
                    if 'TABLE' in text:
                        return f"TABLE {match.group(1)}"
                    else:
                        return f"table {match.group(1)}"
    
    return None


def analyze_table_structure(json_file: str) -> None:
    """
    Analyze table structure from AWS Textract response JSON based on titles.
    
    Args:
        json_file: Path to the analyzeDocResponse.json file
    """
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Find all pages with tables
    pages_with_tables = set()
    for block in data['Blocks']:
        if block['BlockType'] == 'TABLE':
            pages_with_tables.add(block['Page'])
    
    # Extract table titles for each page and fill gaps
    page_titles = {}
    current_title = None
    
    for page in sorted(pages_with_tables):
        title = find_table_title_on_page(page, data['Blocks'])
        
        if title:
            current_title = title
        
        # Always assign the current title (which fills gaps)
        page_titles[page] = current_title
    
    # Group consecutive pages with same table title
    table_groups = []
    current_table = None
    
    for page in sorted(pages_with_tables):
        title = page_titles[page]
        
        if current_table is None or current_table['title'] != title:
            # Start a new table only if the title actually changed
            if current_table:
                table_groups.append(current_table)
            
            current_table = {
                'title': title,
                'start_page': page,
                'end_page': page
            }
        else:
            # Continue current table
            current_table['end_page'] = page
    
    # Add the last table
    if current_table:
        table_groups.append(current_table)
    
    # Output results
    print(f"{len(table_groups)}")
    for i, table in enumerate(table_groups, 1):
        if table['start_page'] == table['end_page']:
            print(f"{table['title']}: Page {table['start_page']}")
        else:
            print(f"{table['title']}: Pages {table['start_page']}-{table['end_page']}")


if __name__ == "__main__":
    analyze_table_structure('analyzeDocResponse.json')