#!/usr/bin/env python3
"""
Simple PDF Table Detection using Amazon Textract
Reads PDF and identifies which pages contain tables
"""

import sys
import boto3
import fitz  # PyMuPDF
from pathlib import Path
import json
from datetime import datetime


def main():
    if len(sys.argv) != 2:
        print("Usage: python table_detector.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' not found")
        sys.exit(1)
    
    # Initialize Textract client (using us-east-1 region)
    try:
        textract_client = boto3.client('textract', region_name='us-east-1')
    except Exception as e:
        print(f"Error: Could not initialize AWS Textract client")
        print(f"Make sure AWS credentials are configured")
        print(f"Run 'aws configure' to set up credentials")
        sys.exit(1)
    
    # Open PDF
    pdf_doc = fitz.open(pdf_path)
    print(f"Processing PDF: {Path(pdf_path).name}")
    print(f"Total pages: {pdf_doc.page_count}")
    print()
    
    pages_with_tables = []
    detection_results = {
        'pdf_path': pdf_path,
        'pdf_name': Path(pdf_path).name,
        'total_pages': pdf_doc.page_count,
        'timestamp': datetime.now().isoformat(),
        'pages_with_tables': [],
        'summary': {}
    }
    
    # Process each page
    for page_num in range(pdf_doc.page_count):
        page = pdf_doc[page_num]
        
        # Convert page to image (PNG format)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x resolution
        image_bytes = pix.tobytes("png")
        
        try:
            # Send to Textract for table detection
            response = textract_client.analyze_document(
                Document={'Bytes': image_bytes},
                FeatureTypes=['TABLES']
            )
            
            # Check if any tables were found
            tables_found = any(block['BlockType'] == 'TABLE' for block in response['Blocks'])
            
            if tables_found:
                # Count number of tables
                table_count = sum(1 for block in response['Blocks'] if block['BlockType'] == 'TABLE')
                page_info = {
                    'page_number': page_num + 1,
                    'table_count': table_count,
                    'textract_confidence': 'high'  # Could extract actual confidence if needed
                }
                pages_with_tables.append(page_num + 1)
                detection_results['pages_with_tables'].append(page_info)
                print(f"Page {page_num + 1}: Contains {table_count} table(s)")
            
        except Exception as e:
            print(f"Page {page_num + 1}: Error processing - {str(e)}")
            # Could also store errors in results if needed
    
    pdf_doc.close()
    
    # Complete results
    detection_results['summary'] = {
        'total_pages_with_tables': len(pages_with_tables),
        'page_numbers': pages_with_tables,
        'detection_success': True if pages_with_tables else False
    }
    
    # Save results to JSON file
    output_file = Path(pdf_path).stem + '_table_detection.json'
    output_path = Path(__file__).parent / output_file
    
    with open(output_path, 'w') as f:
        json.dump(detection_results, f, indent=2)
    
    # Summary
    print()
    print("=" * 50)
    print(f"SUMMARY: {len(pages_with_tables)} pages contain tables")
    if pages_with_tables:
        print(f"Pages with tables: {', '.join(map(str, pages_with_tables))}")
    else:
        print("No tables detected in any pages")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()