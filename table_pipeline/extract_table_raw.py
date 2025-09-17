#!/usr/bin/env python3
import json
import pandas as pd
import argparse

def is_header_row(row):
    """
    Determine if a row is a header row.
    """
    row_text = ' '.join(str(cell) for cell in row).strip()
    row_text_upper = row_text.upper()
    
    # List of US states and territories (including common abbreviations)
    us_states = {
        'ALABAMA', 'AL', 'ALASKA', 'AK', 'ARIZONA', 'AZ', 'ARKANSAS', 'AR',
        'CALIFORNIA', 'CA', 'COLORADO', 'CO', 'CONNECTICUT', 'CT', 'DELAWARE', 'DE',
        'FLORIDA', 'FL', 'GEORGIA', 'GA', 'HAWAII', 'HI', 'IDAHO', 'ID',
        'ILLINOIS', 'IL', 'INDIANA', 'IN', 'IOWA', 'IA', 'KANSAS', 'KS',
        'KENTUCKY', 'KY', 'LOUISIANA', 'LA', 'MAINE', 'ME', 'MARYLAND', 'MD',
        'MASSACHUSETTS', 'MA', 'MICHIGAN', 'MI', 'MINNESOTA', 'MN', 'MISSISSIPPI', 'MS',
        'MISSOURI', 'MO', 'MONTANA', 'MT', 'NEBRASKA', 'NE', 'NEVADA', 'NV',
        'NEW HAMPSHIRE', 'NH', 'NEW JERSEY', 'NJ', 'NEW MEXICO', 'NM', 'NEW YORK', 'NY',
        'NORTH CAROLINA', 'NC', 'NORTH DAKOTA', 'ND', 'OHIO', 'OH', 'OKLAHOMA', 'OK',
        'OREGON', 'OR', 'PENNSYLVANIA', 'PA', 'RHODE ISLAND', 'RI', 'SOUTH CAROLINA', 'SC',
        'SOUTH DAKOTA', 'SD', 'TENNESSEE', 'TN', 'TEXAS', 'TX', 'UTAH', 'UT',
        'VERMONT', 'VT', 'VIRGINIA', 'VA', 'WASHINGTON', 'WA', 'WEST VIRGINIA', 'WV',
        'WISCONSIN', 'WI', 'WYOMING', 'WY', 'DISTRICT OF COLUMBIA', 'DC',
        'PUERTO RICO', 'PR', 'AMERICAN SAMOA', 'AS', 'GUAM', 'GU',
        'NORTHERN MARIANA ISLANDS', 'MP', 'U.S. VIRGIN ISLANDS', 'VI'
    }
    
    # Check if any cell in the row resembles a state name
    for cell in row:
        cell_text = str(cell).strip().upper()
        if cell_text in us_states:
            return False  # Don't classify as header if it contains a state name
    
    # Check if row is primarily comprised of string variables (non-numeric content)
    non_empty_cells = [str(cell).strip() for cell in row if str(cell).strip()]
    if len(non_empty_cells) == 0:
        string_ratio = 0
    else:
        string_cells = 0
        for cell in non_empty_cells:
            # Check if cell is not a number (considering various formats)
            try:
                float(cell.replace(',', '').replace('$', '').replace('%', ''))
                # It's a number
            except ValueError:
                # It's a string/text
                string_cells += 1
        string_ratio = string_cells / len(non_empty_cells)
    
    # Check for common header patterns
    header_indicators = [
        row_text.isdigit(),  # Rows with just numbers like "1 2 3 4 5"
        'TABLE' in row_text_upper,
        'LOCATION.' in row_text_upper,
        'INSTITUTION.' in row_text_upper,
        'FOR MEN, FOR WOMEN' in row_text_upper,
        'CONTROL.' in row_text_upper,
        'MEN.' in row_text_upper and 'WOMEN.' in row_text_upper,
        'VALUE' in row_text_upper,
        len(row_text) < 10 and any(char.isdigit() for char in row_text),  # Short rows with numbers
        # Check if row contains mostly single digits or column numbers
        len([cell for cell in row if str(cell).strip() in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22']]) > len(row) * 0.5,
        # Check if row is primarily strings (>= 30% non-numeric content)
        string_ratio >= 0.5
    ]
    
    return any(header_indicators)

def extract_raw_table_data(json_file_path, page_ranges=None):
    """
    Extract all table data from Amazon Textract JSON without any header modifications or filtering.
    
    Args:
        json_file_path: Path to the JSON file
        page_ranges: Optional list of tuples (start_page, end_page) to define ranges for separate exports.
                    If None, extracts all pages as one document.
                    Example: [(1, 5), (6, 10)] creates two documents
    
    Returns:
        If page_ranges is None: List of all rows
        If page_ranges is provided: Dict mapping range descriptions to row lists
    """
    
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    blocks = data.get('Blocks', [])
    
    # Get all pages
    max_page = 0
    for block in blocks:
        page_num = block.get('Page', 0)
        if page_num > max_page:
            max_page = page_num
    
    print(f"Found {max_page} total pages in document")
    
    # If no page ranges specified, extract all pages as one document
    if page_ranges is None:
        pages_to_process = [(1, max_page, "all_pages")]
    else:
        # Validate page ranges
        for start, end in page_ranges:
            if start < 1 or end > max_page or start > end:
                raise ValueError(f"Invalid page range ({start}, {end}). Pages must be between 1 and {max_page}")
        
        pages_to_process = [(start, end, f"pages_{start}_to_{end}") for start, end in page_ranges]
    
    # Dictionary to store results for each range
    results = {}
    
    # Process each page range
    for start_page, end_page, range_name in pages_to_process:
        range_rows = []
        
        # Extract from specified page range
        for page_num in range(start_page, end_page + 1):
            # Find cells for this page
            cells = [block for block in blocks if block.get('BlockType') == 'CELL' and block.get('Page') == page_num]
            
            if not cells:
                print(f"No cells found on page {page_num}")
                continue
            
            # Create table matrix for this page
            max_row = max(cell.get('RowIndex', 0) for cell in cells)
            max_col = max(cell.get('ColumnIndex', 0) for cell in cells)
            
            table_matrix = [['' for _ in range(max_col)] for _ in range(max_row)]
            
            # Fill matrix with cell text
            for cell in cells:
                row_idx = cell.get('RowIndex', 1) - 1
                col_idx = cell.get('ColumnIndex', 1) - 1
                
                cell_text = ''
                if 'Relationships' in cell:
                    for rel in cell['Relationships']:
                        if rel['Type'] == 'CHILD':
                            for child_id in rel['Ids']:
                                child_block = next((b for b in blocks if b['Id'] == child_id), None)
                                if child_block and child_block.get('BlockType') == 'WORD':
                                    cell_text += child_block.get('Text', '') + ' '
                
                table_matrix[row_idx][col_idx] = cell_text.strip()
            
            # Add ALL rows from this page with page number and header indicator as first columns
            for row in table_matrix:
                # Add page number as first column, header indicator (1 if header, 0 if not) as second column
                header_indicator = 1 if is_header_row(row) else 0
                row_with_indicators = [page_num, header_indicator] + row
                range_rows.append(row_with_indicators)
        
        # Store results for this range
        if page_ranges is None:
            results = range_rows  # Return simple list for backward compatibility
        else:
            results[range_name] = range_rows
    
    return results

def process_and_save_data(table_data, output_base_path, range_name=None):
    """
    Process table data and save to CSV file.
    
    Args:
        table_data: List of rows
        output_base_path: Base path for output file
        range_name: Optional range name to append to filename
    
    Returns:
        Path to saved file
    """
    if not table_data:
        print(f"No data to save for {range_name or 'document'}")
        return None
    
    print(f"Processing {len(table_data)} total rows for {range_name or 'document'}")
    
    # Find maximum number of columns to standardize
    max_cols = max(len(row) for row in table_data) if table_data else 0
    print(f"Maximum columns found: {max_cols}")
    
    # Standardize all rows to have the same number of columns
    standardized_data = []
    for row in table_data:
        if len(row) < max_cols:
            # Pad with empty strings
            padded_row = row + [''] * (max_cols - len(row))
        else:
            padded_row = row[:max_cols]  # Truncate if longer
        standardized_data.append(padded_row)
    
    # Keep all rows including the first row
    
    # Create DataFrame
    df = pd.DataFrame(standardized_data)
    
    # Generate output filename
    if range_name and range_name != "all_pages":
        output_file = output_base_path.replace('.csv', f'_{range_name}.csv')
    else:
        output_file = output_base_path
    
    # Save to CSV without headers
    df.to_csv(output_file, index=False, header=False)
    
    print(f"Saved: {df.shape[0]} rows, {df.shape[1]} columns to {output_file}")
    return output_file

def extract_multiple_documents(json_file_path, page_ranges, output_base_path):
    """
    Convenience function to extract multiple documents based on page ranges.
    
    Args:
        json_file_path: Path to the JSON file
        page_ranges: List of tuples (start_page, end_page)
        output_base_path: Base path for output files
    
    Returns:
        List of output file paths created
    """
    try:
        table_data_ranges = extract_raw_table_data(json_file_path, page_ranges=page_ranges)
        
        if isinstance(table_data_ranges, dict):
            output_files = []
            for range_name, range_data in table_data_ranges.items():
                output_file = process_and_save_data(range_data, output_base_path, range_name)
                if output_file:
                    output_files.append(output_file)
            
            print(f"\nSuccessfully created {len(output_files)} separate documents:")
            for file_path in output_files:
                print(f"  - {file_path}")
            
            return output_files
        
    except ValueError as e:
        print(f"Error with page ranges: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Extract table data from Amazon Textract JSON with optional page ranges')
    parser.add_argument('--json-file', '-j', 
                       default='/Users/cjwardius/Documents/GitHub/demo_of_education/analyzeDocResponse.json',
                       help='Path to the JSON file (default: analyzeDocResponse.json)')
    parser.add_argument('--output', '-o',
                       default='/Users/cjwardius/Documents/GitHub/demo_of_education/raw_table_extract.csv',
                       help='Output CSV file path (default: raw_table_extract.csv)')
    parser.add_argument('--page-ranges', '-p', 
                       help='Page ranges as comma-separated start-end pairs (e.g., "1-3,4-6,7-10")')
    
    args = parser.parse_args()
    
    json_file = args.json_file
    output_base_path = args.output
    
    if args.page_ranges:
        # Parse page ranges from command line
        try:
            page_ranges = []
            ranges_str = args.page_ranges.split(',')
            for range_str in ranges_str:
                start, end = map(int, range_str.strip().split('-'))
                page_ranges.append((start, end))
            
            print(f"=== Extracting page ranges to separate documents ===")
            print(f"Page ranges: {page_ranges}")
            
            output_files = extract_multiple_documents(json_file, page_ranges, output_base_path)
            
        except ValueError as e:
            print(f"Error parsing page ranges: {e}")
            print("Format should be: 1-3,4-6,7-10")
            
    else:
        # Default behavior: extract all pages as one document
        print("=== Extracting all pages as one document ===")
        table_data = extract_raw_table_data(json_file)
        if isinstance(table_data, list):
            process_and_save_data(table_data, output_base_path)

if __name__ == "__main__":
    main()