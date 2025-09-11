#!/usr/bin/env python3
import json
import pandas as pd

def is_header_row(row, page_num):
    """
    Determine if a row is a header row that should be skipped on pages > 1.
    """
    if page_num == 1:
        return False  # Don't skip headers on first page
    
    row_text = ' '.join(str(cell) for cell in row).strip()
    row_text_upper = row_text.upper()
    
    # Check for common header patterns
    header_indicators = [
        row_text.isdigit(),  # Rows with just numbers like "1 2 3 4 5"
        'TABLE' in row_text_upper,
        'LOCATION.' in row_text_upper,
        'INSTITUTION.' in row_text_upper,
        'FOR MEN, FOR WOMEN' in row_text_upper,
        'CONTROL.' in row_text_upper,
        'MEN.' in row_text_upper and 'WOMEN.' in row_text_upper,
        len(row_text) < 10 and any(char.isdigit() for char in row_text),  # Short rows with numbers
        # Check if row contains mostly single digits or column numbers
        len([cell for cell in row if str(cell).strip() in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22']]) > len(row) * 0.5
    ]
    
    return any(header_indicators)

def extract_table_from_pages(blocks, start_page, end_page):
    """
    Extract table data from a range of pages.
    """
    all_rows = []
    
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
        
        # Add page number to each row and append to all_rows, skipping headers on pages > 1
        for row in table_matrix:
            # Skip header rows on pages after page 1
            if is_header_row(row, page_num):
                print(f"Skipping header row on page {page_num}: {' '.join(str(cell) for cell in row[:5])}...")
                continue
                
            row_with_page = row + [page_num]
            all_rows.append(row_with_page)
    
    return all_rows

def get_total_pages(blocks):
    """
    Find the total number of pages in the document.
    """
    max_page = 0
    for block in blocks:
        page_num = block.get('Page', 0)
        if page_num > max_page:
            max_page = page_num
    return max_page

def examine_headers_from_page(blocks, page_num):
    """
    Examine the first few rows of a table to understand header structure.
    """
    cells = [block for block in blocks if block.get('BlockType') == 'CELL' and block.get('Page') == page_num]
    
    if not cells:
        return []
    
    # Get first 5 rows to understand header structure
    max_col = max(cell.get('ColumnIndex', 0) for cell in cells)
    header_rows = []
    
    for row_idx in range(1, 6):  # First 5 rows
        row = ['' for _ in range(max_col)]
        row_cells = [cell for cell in cells if cell.get('RowIndex', 0) == row_idx]
        
        for cell in row_cells:
            col_idx = cell.get('ColumnIndex', 1) - 1
            cell_text = ''
            if 'Relationships' in cell:
                for rel in cell['Relationships']:
                    if rel['Type'] == 'CHILD':
                        for child_id in rel['Ids']:
                            child_block = next((b for b in blocks if b['Id'] == child_id), None)
                            if child_block and child_block.get('BlockType') == 'WORD':
                                cell_text += child_block.get('Text', '') + ' '
            row[col_idx] = cell_text.strip()
        
        header_rows.append(row)
    
    return header_rows

def extract_all_pages(json_file_path):
    """
    Extract tables from all pages of Amazon Textract JSON, handling different formats.
    """
    
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    blocks = data.get('Blocks', [])
    total_pages = get_total_pages(blocks)
    
    print(f"Found {total_pages} total pages in document")
    
    all_tables = []
    standard_tables = []
    non_standard_tables = []
    
    # Standard format reference (from first table)
    reference_format = None
    
    # Extract tables from all pages
    for page_num in range(1, total_pages + 1):
        table_matrix, table_name = extract_table_from_page(blocks, page_num)
        
        if table_matrix is not None:
            format_info = detect_table_format(table_matrix)
            
            # Set reference format from first valid table
            if reference_format is None:
                reference_format = format_info
                print(f"Setting reference format from page {page_num}: {format_info['num_columns']} columns")
            
            table_info = {
                'page': page_num,
                'table_name': table_name,
                'matrix': table_matrix,
                'format': format_info
            }
            
            # Check if format matches reference
            if (format_info['num_columns'] == reference_format['num_columns'] and 
                format_info['appears_standard'] == reference_format['appears_standard']):
                standard_tables.append(table_info)
                print(f"Page {page_num}: Standard format - {format_info['num_columns']} columns")
            else:
                non_standard_tables.append(table_info)
                print(f"Page {page_num}: NON-STANDARD format - {format_info['num_columns']} columns")
                print(f"  Will create specialized extractor for this format")
            
            all_tables.append(table_info)
        else:
            print(f"Warning: No table found on page {page_num}")
    
    return all_tables, standard_tables, non_standard_tables


def create_meaningful_headers(table_matrix):
    """
    Create meaningful headers based on the university survey structure.
    """
    
    # Based on the table structure observed, create proper headers
    headers = [
        'Location',
        'Institution_Name',
        'Education_Type',  # For men, women, or coeducational
        'Control_Type',    # State, Private, etc.
        'Year_First_Opened',
        'Professors_Men',
        'Professors_Women', 
        'Total_Professors_Men',
        'Total_Professors_Women',
        'Students_Men',
        'Students_Women',
        'Total_Students_Men',
        'Total_Students_Women',
        'First_Degrees_Men',
        'First_Degrees_Women',
        'Total_First_Degrees_Men',
        'Total_First_Degrees_Women',
        'Graduate_Degrees_Men',
        'Graduate_Degrees_Women',
        'Total_Graduate_Degrees_Men',
        'Total_Graduate_Degrees_Women',
        'Honorary_Degrees'
    ]
    
    # Find data rows (skip the first few rows that are headers/labels)
    data_rows = []
    for i, row in enumerate(table_matrix):
        # Skip rows that appear to be headers (contain mostly text, numbers like "1", "2", etc.)
        row_text = ' '.join(str(cell) for cell in row).strip()
        
        # Skip empty rows
        if not row_text:
            continue
            
        # Skip header-like rows
        if (i < 3 or 
            row_text.isdigit() or  # Skip rows with just numbers
            'TABLE' in row_text.upper() or
            len([cell for cell in row if str(cell).isdigit() and len(str(cell)) < 3]) > len(row) * 0.7):  # Skip rows with mostly single/double digit numbers
            continue
            
        data_rows.append(row)
    
    return headers, data_rows

def clean_data(df):
    """
    Clean the extracted data.
    """
    # Replace empty strings with NaN
    df = df.replace('', pd.NA)
    
    # Convert numeric columns to proper types
    numeric_columns = [col for col in df.columns if any(keyword in col.lower() 
                      for keyword in ['professors', 'students', 'degrees', 'year'])]
    
    for col in numeric_columns:
        if col in df.columns:
            # Clean numeric values
            df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def clean_table_data(table_data):
    """
    Clean the table data by removing empty rows and header rows.
    """
    clean_data = []
    for row in table_data:
        # Skip completely empty rows
        row_text = ' '.join(str(cell) for cell in row[:-1]).strip()  # Exclude page number
        if not row_text:
            continue
        
        # Skip rows that seem to be headers (contain only numbers or table identifiers)
        if (row_text.isdigit() or 
            'TABLE' in row_text.upper() or
            len(row_text) < 5):
            continue
            
        clean_data.append(row)
    
    return clean_data

def main():
    json_file = '/Users/cjwardius/Documents/GitHub/demo_of_education/analyzeDocResponse.json'
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    blocks = data.get('Blocks', [])
    total_pages = get_total_pages(blocks)
    
    print(f"Found {total_pages} total pages in document")
    print("Processing only pages 1-111 as requested")
    
    # First, let's examine the headers of the first page
    print("\nExamining headers from page 1...")
    headers_sample = examine_headers_from_page(blocks, 1)
    for i, row in enumerate(headers_sample[:3]):
        print(f"  Row {i+1}: {row}")
    
    # Extract first 20 pages for testing
    print(f"\nExtracting pages 1-20...")
    table_data = extract_table_from_pages(blocks, 1, 20)  # Test with first 20 pages
    
    if not table_data:
        print("No data extracted!")
        return
    
    print(f"Extracted {len(table_data)} raw rows")
    
    # Clean the data
    clean_data_rows = clean_table_data(table_data)
    print(f"After cleaning: {len(clean_data_rows)} rows")
    
    if not clean_data_rows:
        print("No clean data available!")
        return
    
    # Use meaningful headers
    headers, final_clean_data = create_meaningful_headers(clean_data_rows)
    
    # Standardize all rows to match the header count from first page + page number column
    if final_clean_data:
        # Add page number to headers if not already there
        if 'Page_Number' not in headers:
            headers.append('Page_Number')
        
        target_columns = len(headers)  # Use header count from first page + page number
        print(f"Target columns (including page number): {target_columns}")
        
        # Track pages with mismatches
        pages_with_too_many = []
        pages_with_too_few = []
        
        standardized_data = []
        for i, row in enumerate(final_clean_data):
            current_cols = len(row)
            page_num = row[-1] if len(row) > 0 else 'Unknown'  # Page number is last column
            
            if current_cols > target_columns:
                # Remove excess columns but keep page number (last column)
                data_part = row[:-1]  # All columns except page number
                page_part = [row[-1]]  # Page number
                # Trim data part to fit target - 1 (for page number)
                trimmed_data = data_part[:target_columns-1]
                standardized_row = trimmed_data + page_part
                pages_with_too_many.append(page_num)
                if i < 5:  # Log first few adjustments
                    print(f"Row {i+1} (Page {page_num}): Removed {current_cols - target_columns} excess data columns")
            elif current_cols < target_columns:
                # Add empty columns but keep page number last
                data_part = row[:-1] if current_cols > 0 else []  # All columns except page number
                page_part = [row[-1]] if current_cols > 0 else ['Unknown']  # Page number
                # Add empty columns to data part
                padded_data = data_part + [''] * (target_columns - 1 - len(data_part))
                standardized_row = padded_data + page_part
                pages_with_too_few.append(page_num)
                if i < 5:  # Log first few adjustments
                    print(f"Row {i+1} (Page {page_num}): Added {target_columns - current_cols} empty data columns")
            else:
                standardized_row = row
            
            standardized_data.append(standardized_row)
        
        # Report summary of column mismatches by page
        if pages_with_too_many:
            unique_pages_many = sorted(set(pages_with_too_many))
            print(f"\nPages with TOO MANY columns: {unique_pages_many} ({len(pages_with_too_many)} rows affected)")
        
        if pages_with_too_few:
            unique_pages_few = sorted(set(pages_with_too_few))
            print(f"Pages with TOO FEW columns: {unique_pages_few} ({len(pages_with_too_few)} rows affected)")
        
        print(f"Standardized {len(standardized_data)} rows to {target_columns} columns (including page number)")
        final_clean_data = standardized_data
    
    df = pd.DataFrame(final_clean_data, columns=headers)
    df = clean_data(df)
    df.to_csv('/Users/cjwardius/Documents/GitHub/demo_of_education/pages_1_111_extracted.csv', index=False)
    
    print(f"Table extracted and saved: {df.shape[0]} rows, {df.shape[1]} columns")
    
    print("\n=== EXTRACTION COMPLETE ===")
    print("CSV file created: pages_1_111_extracted.csv")

if __name__ == "__main__":
    main()