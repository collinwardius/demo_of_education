#!/usr/bin/env python3
"""
PDF Table Detection and Rotation using Amazon Textract (Async Version)
Detects tables in PDF pages and rotates them 90 degrees for optimal extraction
"""

import sys
import asyncio
import aioboto3
import fitz  # PyMuPDF
from pathlib import Path
import json
from datetime import datetime


async def detect_tables_async(pdf_path, textract_client):
    """
    Detect tables in PDF using Amazon Textract (async version)
    
    Returns:
        List of page numbers containing tables
    """
    print(f"Processing PDF: {Path(pdf_path).name}")
    print()
    
    pages_with_tables = []
    detection_results = {
        'pdf_path': pdf_path,
        'pdf_name': Path(pdf_path).name,
        'timestamp': datetime.now().isoformat(),
        'pages_with_tables': [],
        'summary': {}
    }
    
    # Read PDF file as bytes
    with open(pdf_path, 'rb') as pdf_file:
        pdf_bytes = pdf_file.read()
    
    try:
        # Send entire PDF to Textract for table detection (async)
        response = await textract_client.analyze_document(
            Document={'Bytes': pdf_bytes},
            FeatureTypes=['TABLES']
        )
        
        # Process blocks to find tables and their page numbers
        page_tables = {}
        for block in response['Blocks']:
            if block['BlockType'] == 'TABLE':
                page_num = block.get('Page', 1)
                if page_num not in page_tables:
                    page_tables[page_num] = 0
                page_tables[page_num] += 1
        
        # Convert results
        for page_num, table_count in page_tables.items():
            page_info = {
                'page_number': page_num,
                'table_count': table_count,
                'textract_confidence': 'high'
            }
            pages_with_tables.append(page_num)
            detection_results['pages_with_tables'].append(page_info)
            print(f"Page {page_num}: Contains {table_count} table(s)")
        
        detection_results['total_pages'] = response.get('DocumentMetadata', {}).get('Pages', len(page_tables))
        
    except Exception as e:
        print(f"Error processing PDF - {str(e)}")
        detection_results['total_pages'] = 0
    
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


async def main():
    if len(sys.argv) != 2:
        print("Usage: python table_detector_async.py <pdf_file>")
        print("Example: python table_detector_async.py document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' not found")
        sys.exit(1)
    
    # Initialize async Textract client
    try:
        session = aioboto3.Session()
        async with session.client('textract', region_name='us-east-1') as textract_client:
            # Step 1: Detect tables
            print("🔍 STEP 1: DETECTING TABLES WITH TEXTRACT (ASYNC)")
            pages_with_tables = await detect_tables_async(pdf_path, textract_client)
            
            if not pages_with_tables:
                print("\n❌ No tables found. No rotation needed.")
                return
            
            # Step 2: Rotate table pages
            print("\n🔄 STEP 2: ROTATING TABLE PAGES")
            output_path = rotate_table_pages(pdf_path, pages_with_tables)
            
            print(f"\n🎉 COMPLETE! Table pages detected and rotated.")
            print(f"📁 Output: {output_path}")
            
    except Exception as e:
        print(f"Error: Could not initialize AWS Textract client")
        print(f"Make sure AWS credentials are configured")
        print(f"Run 'aws configure' to set up credentials")
        print(f"Error details: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())