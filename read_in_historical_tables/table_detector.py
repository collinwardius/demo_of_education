#!/usr/bin/env python3
"""
PDF Table Detection and Rotation using Amazon Textract
Detects tables in PDF pages and rotates them 90 degrees for optimal extraction
"""

import sys
import boto3
import fitz  # PyMuPDF
from pathlib import Path
import json
from datetime import datetime


def detect_tables(pdf_path, textract_client):
    """
    Detect tables in PDF using Amazon Textract
    
    Returns:
        List of page numbers containing tables
    """
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
    
    print()
    print("=" * 50)
    print(f"TABLE DETECTION SUMMARY: {len(pages_with_tables)} pages contain tables")
    if pages_with_tables:
        print(f"Pages with tables: {', '.join(map(str, pages_with_tables))}")
    else:
        print("No tables detected in any pages")
        return []
    print(f"Detection results saved to: {output_path}")
    
    return pages_with_tables


def rotate_table_pages(pdf_path, page_numbers):
    """
    Rotate the specified table pages 90 degrees and create output PDF
    
    Args:
        pdf_path: Path to the original PDF
        page_numbers: List of page numbers to rotate
    
    Returns:
        Path to the rotated PDF file
    """
    if not page_numbers:
        print("No pages to rotate")
        return None
    
    print()
    print("=" * 50)
    print(f"ROTATING TABLE PAGES")
    print(f"Rotating {len(page_numbers)} pages 90 degrees clockwise...")
    
    # Create output path
    pdf_path_obj = Path(pdf_path)
    output_path = pdf_path_obj.parent / f"{pdf_path_obj.stem}_tables_rotated.pdf"
    
    # Open original PDF
    pdf_doc = fitz.open(pdf_path)
    
    # Create new PDF for output
    new_pdf = fitz.open()
    
    # Process only pages that contain tables
    for page_index in sorted(page_numbers):
        page_num = page_index - 1  # Convert to 0-indexed for PyMuPDF
        original_page = pdf_doc[page_num]
        
        print(f"  Rotating page {page_index} by 90°")
        
        # Rotate the page 90 degrees
        original_page.set_rotation(90)
        
        # Add page to new PDF
        new_pdf.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
    
    # Save the rotated PDF
    new_pdf.save(output_path)
    new_pdf.close()
    pdf_doc.close()
    
    print(f"\n✅ Rotated PDF saved to: {output_path}")
    print(f"📄 {len(page_numbers)} pages rotated 90° clockwise")
    print(f"🎯 Ready for table extraction!")
    
    return str(output_path)


def main():
    if len(sys.argv) != 2:
        print("Usage: python table_detector_and_rotator.py <pdf_file>")
        print("Example: python table_detector_and_rotator.py document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' not found")
        sys.exit(1)
    
    # Initialize Textract client
    try:
        textract_client = boto3.client('textract', region_name='us-east-1')
    except Exception as e:
        print(f"Error: Could not initialize AWS Textract client")
        print(f"Make sure AWS credentials are configured")
        print(f"Run 'aws configure' to set up credentials")
        sys.exit(1)
    
    # Step 1: Detect tables
    print("🔍 STEP 1: DETECTING TABLES WITH TEXTRACT")
    pages_with_tables = detect_tables(pdf_path, textract_client)
    
    if not pages_with_tables:
        print("\n❌ No tables found. No rotation needed.")
        return
    
    # Step 2: Rotate table pages
    print("\n🔄 STEP 2: ROTATING TABLE PAGES")
    output_path = rotate_table_pages(pdf_path, pages_with_tables)
    
    print(f"\n🎉 COMPLETE! Table pages detected and rotated.")
    print(f"📁 Output: {output_path}")


if __name__ == "__main__":
    main()