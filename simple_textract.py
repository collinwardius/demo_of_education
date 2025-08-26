#!/usr/bin/env python3
"""
Simple Amazon Textract Extractor
Minimal processing - preserves raw Textract output with basic CSV export
"""

import boto3
import json
import pandas as pd
from pathlib import Path
import argparse
import logging

class SimpleTextractExtractor:
    def __init__(self, aws_region: str = 'us-east-1'):
        """Initialize simple Textract extractor."""
        self.textract = boto3.client('textract', region_name=aws_region)
        
        # Setup basic logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def extract_from_file(self, file_path: str) -> dict:
        """Extract text and tables from file with minimal processing."""
        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Use analyze_document to get both text and tables
            response = self.textract.analyze_document(
                Document={'Bytes': file_bytes},
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            self.logger.info(f"Extracted {len(response['Blocks'])} blocks from {file_path}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            raise
    
    def extract_raw_text(self, response: dict) -> str:
        """Extract all text in reading order."""
        lines = []
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                lines.append(block['Text'])
        return '\n'.join(lines)
    
    def extract_tables_simple(self, response: dict) -> list:
        """Extract tables with minimal processing."""
        tables = []
        block_map = {block['Id']: block for block in response['Blocks']}
        
        for block in response['Blocks']:
            if block['BlockType'] == 'TABLE':
                table = self._build_table_from_cells(block, block_map)
                if table:
                    tables.append(table)
        
        return tables
    
    def _build_table_from_cells(self, table_block: dict, block_map: dict) -> list:
        """Build table from cells with minimal processing."""
        if 'Relationships' not in table_block:
            return []
        
        # Get all cells
        cells = []
        for relationship in table_block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for cell_id in relationship['Ids']:
                    if cell_id in block_map:
                        cell = block_map[cell_id]
                        if cell['BlockType'] == 'CELL':
                            cells.append(cell)
        
        # Organize cells by position
        cell_grid = {}
        max_row = 0
        max_col = 0
        
        for cell in cells:
            row = cell['RowIndex'] - 1  # Convert to 0-based
            col = cell['ColumnIndex'] - 1
            max_row = max(max_row, row)
            max_col = max(max_col, col)
            
            # Extract text from cell
            cell_text = self._get_cell_text(cell, block_map)
            
            if row not in cell_grid:
                cell_grid[row] = {}
            cell_grid[row][col] = cell_text
        
        # Convert to list format
        table_data = []
        for row in range(max_row + 1):
            row_data = []
            for col in range(max_col + 1):
                cell_value = cell_grid.get(row, {}).get(col, "")
                row_data.append(cell_value)
            table_data.append(row_data)
        
        return table_data
    
    def _get_cell_text(self, cell: dict, block_map: dict) -> str:
        """Extract text from a cell."""
        text = ""
        if 'Relationships' in cell:
            for relationship in cell['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        if child_id in block_map:
                            child = block_map[child_id]
                            if child['BlockType'] == 'WORD':
                                text += child['Text'] + " "
        return text.strip()
    
    def save_results(self, file_path: str, response: dict, output_dir: str):
        """Save all results with minimal processing."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        base_name = Path(file_path).stem
        
        # 1. Save complete JSON response
        json_file = output_path / f"{base_name}_full_response.json"
        with open(json_file, 'w') as f:
            json.dump(response, f, indent=2, default=str)
        self.logger.info(f"Saved full response: {json_file}")
        
        # 2. Save raw text
        raw_text = self.extract_raw_text(response)
        text_file = output_path / f"{base_name}_raw_text.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(raw_text)
        self.logger.info(f"Saved raw text: {text_file}")
        
        # 3. Save tables as CSVs
        tables = self.extract_tables_simple(response)
        
        if tables:
            for i, table in enumerate(tables):
                if table:  # Only save non-empty tables
                    if len(tables) == 1:
                        csv_file = output_path / f"{base_name}_table.csv"
                    else:
                        csv_file = output_path / f"{base_name}_table_{i+1}.csv"
                    
                    # Convert to DataFrame and save
                    df = pd.DataFrame(table)
                    df.to_csv(csv_file, index=False, header=False)
                    self.logger.info(f"Saved table {i+1}: {csv_file}")
                    
                    # Also save with headers if first row looks like headers
                    if len(table) > 1:
                        df_with_headers = pd.DataFrame(table[1:], columns=table[0])
                        header_csv = output_path / f"{base_name}_table_{i+1}_with_headers.csv"
                        df_with_headers.to_csv(header_csv, index=False)
                        self.logger.info(f"Saved table with headers: {header_csv}")
            
            self.logger.info(f"Extracted {len(tables)} tables from {file_path}")
        else:
            self.logger.warning(f"No tables found in {file_path}")
        
        # 4. Create summary
        summary = {
            "file": file_path,
            "total_blocks": len(response['Blocks']),
            "tables_found": len(tables),
            "text_lines": len(raw_text.split('\n')),
            "output_files": [
                str(json_file.name),
                str(text_file.name)
            ]
        }
        
        if tables:
            for i in range(len(tables)):
                if len(tables) == 1:
                    summary["output_files"].append(f"{base_name}_table.csv")
                    summary["output_files"].append(f"{base_name}_table_with_headers.csv")
                else:
                    summary["output_files"].append(f"{base_name}_table_{i+1}.csv")
                    summary["output_files"].append(f"{base_name}_table_{i+1}_with_headers.csv")
        
        summary_file = output_path / f"{base_name}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        self.logger.info(f"Saved summary: {summary_file}")

def main():
    parser = argparse.ArgumentParser(description='Simple Textract extraction with minimal processing')
    parser.add_argument('input_file', help='Path to input file (PDF, PNG, JPG, etc.)')
    parser.add_argument('--output-dir', '-o', 
                       default='/Users/cjwardius/Documents/GitHub/demo_of_education/test_results',
                       help='Output directory')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = SimpleTextractExtractor(aws_region=args.region)
    
    # Process file
    try:
        print(f"Processing: {args.input_file}")
        response = extractor.extract_from_file(args.input_file)
        extractor.save_results(args.input_file, response, args.output_dir)
        print(f"✅ Complete! Results saved to: {args.output_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())