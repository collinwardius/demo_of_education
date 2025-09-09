import json
import csv
import re
from collections import defaultdict

def load_json_file(file_path):
    """Load the large JSON file"""
    print(f"Loading JSON file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_first_table(data):
    """Find the first TABLE block and return its ID and related cells"""
    print("Searching for first table...")
    
    # Find the first TABLE block
    table_block = None
    for block in data['Blocks']:
        if block['BlockType'] == 'TABLE':
            table_block = block
            print(f"Found first table with ID: {block['Id']}")
            break
    
    if not table_block:
        print("No table found!")
        return None, []
    
    # Get all child cell IDs for this table
    cell_ids = set()
    if 'Relationships' in table_block:
        for relationship in table_block['Relationships']:
            if relationship['Type'] == 'CHILD':
                cell_ids.update(relationship['Ids'])
    
    # Find all CELL blocks belonging to this table
    table_cells = []
    for block in data['Blocks']:
        if block['BlockType'] == 'CELL' and block['Id'] in cell_ids:
            table_cells.append(block)
    
    print(f"Found {len(table_cells)} cells in the table")
    return table_block, table_cells

def get_cell_text(cell_block, all_blocks):
    """Extract text content from a cell by following its relationships"""
    text_parts = []
    
    if 'Relationships' in cell_block:
        for relationship in cell_block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    # Find the child block
                    for block in all_blocks:
                        if block['Id'] == child_id and 'Text' in block:
                            text_parts.append(block['Text'])
    
    return ' '.join(text_parts).strip()

def analyze_header_structure(table_cells, all_blocks):
    """Analyze the header structure and determine header rows"""
    print("Analyzing header structure...")
    
    # Group cells by row
    rows = defaultdict(list)
    max_row = 0
    max_col = 0
    
    for cell in table_cells:
        row_idx = cell.get('RowIndex', 1)
        col_idx = cell.get('ColumnIndex', 1)
        rows[row_idx].append(cell)
        max_row = max(max_row, row_idx + cell.get('RowSpan', 1) - 1)
        max_col = max(max_col, col_idx + cell.get('ColumnSpan', 1) - 1)
    
    print(f"Table dimensions: {max_row} rows x {max_col} columns")
    print(f"Row distribution: {dict([(k, len(v)) for k, v in rows.items()])}")
    
    # Assume first few rows are headers - let's examine first 3 rows
    header_rows = min(3, max(rows.keys()))
    print(f"Analyzing first {header_rows} rows as potential headers")
    
    # Extract text for header cells
    header_cells_with_text = []
    for row_idx in range(1, header_rows + 1):
        if row_idx in rows:
            for cell in rows[row_idx]:
                text = get_cell_text(cell, all_blocks)
                cell_info = {
                    'row': cell.get('RowIndex', 1),
                    'col': cell.get('ColumnIndex', 1),
                    'row_span': cell.get('RowSpan', 1),
                    'col_span': cell.get('ColumnSpan', 1),
                    'text': text
                }
                header_cells_with_text.append(cell_info)
    
    # Sort by row, then column
    header_cells_with_text.sort(key=lambda x: (x['row'], x['col']))
    
    print(f"\nFound {len(header_cells_with_text)} header cells:")
    for cell in header_cells_with_text:
        print(f"  Row {cell['row']}, Col {cell['col']} (span: {cell['row_span']}x{cell['col_span']}): '{cell['text']}'")
    
    return header_cells_with_text, max_col

def clean_text(text):
    """Clean text for use as column names"""
    if not text:
        return ""
    
    # Remove non-English characters and OCR artifacts
    text = re.sub(r'[^\x00-\x7F]', '', text)  # Remove non-ASCII
    text = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]', '', text)  # Remove superscript numbers
    text = re.sub(r'[^\w\s]', ' ', text)  # Keep only letters, numbers, spaces
    
    # Handle hyphenated words from OCR line breaks
    text = re.sub(r'-\s+', '', text)  # Remove line-break hyphens
    text = re.sub(r'\s+', '_', text.strip())
    text = text.lower()
    
    # Remove common OCR artifacts and trailing numbers
    text = re.sub(r'_\d+$', '', text)
    text = re.sub(r'^_+|_+$', '', text)  # Remove leading/trailing underscores
    
    # Fix common OCR issues
    text = re.sub(r'instruo', 'instructo', text)  # Fix OCR error
    text = re.sub(r'_+', '_', text)  # Collapse multiple underscores
    
    return text

def build_column_mapping(header_cells, max_col):
    """Build a mapping from column index to hierarchical header names"""
    print("\nBuilding column hierarchy...")
    
    # Create dictionaries for each header row
    row1_headers = {}  # Main categories
    row2_headers = {}  # Gender subdivisions
    
    # Parse headers and handle spans properly
    for cell in header_cells:
        row = cell['row']
        col = cell['col']
        text = clean_text(cell['text'])
        col_span = cell['col_span']
        
        if row == 1 and text:  # Only store non-empty headers
            # Distribute row 1 headers across their column span
            for i in range(col_span):
                row1_headers[col + i] = text
        elif row == 2 and text:  # Only store non-empty headers
            # Row 2 headers (Men/Women subdivisions)
            for i in range(col_span):
                row2_headers[col + i] = text
    
    # Build final column names with smart mapping
    column_names = []
    used_names = set()  # Track used names to avoid duplicates
    
    for col_idx in range(1, max_col + 1):
        name_parts = []
        
        # Get the main category header
        main_header = row1_headers.get(col_idx, "")
        sub_header = row2_headers.get(col_idx, "")
        
        # Build meaningful names based on available headers
        if main_header and sub_header:
            # Both headers available - combine them
            name_parts = [main_header, sub_header]
        elif main_header:
            # Only main header - use it alone
            name_parts = [main_header]
        elif sub_header:
            # Only sub header - use it alone
            name_parts = [sub_header]
        else:
            # No meaningful headers - use generic name
            name_parts = [f"column_{col_idx}"]
        
        # Create column name
        column_name = "_".join(name_parts)
        
        # Handle duplicates by adding suffix
        original_name = column_name
        counter = 1
        while column_name in used_names:
            counter += 1
            column_name = f"{original_name}_{counter}"
        
        used_names.add(column_name)
        column_names.append(column_name)
        
        # Debug output
        print(f"  Col {col_idx}: '{main_header}' + '{sub_header}' = '{column_name}'")
    
    return column_names

def save_headers_to_csv(column_names, output_file):
    """Save the flattened headers to a CSV file"""
    print(f"\nSaving headers to {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(column_names)
    
    print(f"Saved {len(column_names)} column headers to CSV")

def main():
    file_path = "/Users/cjwardius/Documents/GitHub/demo_of_education/bi_survey1916_1918 (1)/analyzeDocResponse.json"
    output_file = "/Users/cjwardius/Documents/GitHub/demo_of_education/table_headers.csv"
    
    # Load JSON data
    data = load_json_file(file_path)
    
    # Find first table
    table_block, table_cells = find_first_table(data)
    if not table_block:
        return
    
    # Analyze header structure
    header_cells, max_col = analyze_header_structure(table_cells, data['Blocks'])
    
    # Build column mapping
    column_names = build_column_mapping(header_cells, max_col)
    
    # Save to CSV
    save_headers_to_csv(column_names, output_file)
    
    print(f"\nFinal column names:")
    for i, name in enumerate(column_names, 1):
        print(f"  {i}: {name}")

if __name__ == "__main__":
    main()