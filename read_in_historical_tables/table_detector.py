#!/usr/bin/env python3
"""
PDF Table Detection and Smart Orientation using Amazon Textract
Detects tables in PDF pages and applies orientation correction based on table content
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
            # Send to Textract for table detection and orientation info
            response = textract_client.analyze_document(
                Document={'Bytes': image_bytes},
                FeatureTypes=['TABLES', 'FORMS']  # Adding FORMS to get orientation info
            )
            
            # Debug: Output DocumentMetadata to check for orientation info
            print(f"    DEBUG: DocumentMetadata contents:")
            if 'DocumentMetadata' in response:
                for key, value in response['DocumentMetadata'].items():
                    print(f"      {key}: {value}")
            else:
                print("      DocumentMetadata not found")
                
            # Find table blocks 
            table_blocks = [block for block in response['Blocks'] if block['BlockType'] == 'TABLE']
            
            if table_blocks:
                # Extract page-level orientation info from document metadata
                orientation_correction = 0
                confidence = 0
                
                # Look for orientation correction in various locations
                page_orientation_raw = None
                
                # First check DocumentMetadata
                if 'DocumentMetadata' in response and 'OrientationCorrection' in response['DocumentMetadata']:
                    page_orientation_raw = response['DocumentMetadata']['OrientationCorrection']
                    print(f"    Found OrientationCorrection in DocumentMetadata: {page_orientation_raw}")
                
                # Then check response root level
                elif 'OrientationCorrection' in response:
                    page_orientation_raw = response['OrientationCorrection']
                    print(f"    Found OrientationCorrection at response root: {page_orientation_raw}")
                
                # Finally check PAGE blocks
                else:
                    page_blocks = [block for block in response['Blocks'] if block['BlockType'] == 'PAGE']
                    if page_blocks and 'Geometry' in page_blocks[0]:
                        page_geometry = page_blocks[0]['Geometry']
                        page_orientation_raw = page_geometry.get('OrientationCorrection')
                        if page_orientation_raw:
                            print(f"    Found OrientationCorrection in PAGE block: {page_orientation_raw}")
                
                if page_orientation_raw is None:
                    print(f"    ⚠️  WARNING: Page-level OrientationCorrection not found for page {page_num + 1}")
                    print(f"    Available response keys: {list(response.keys())}")
                    page_blocks = [block for block in response['Blocks'] if block['BlockType'] == 'PAGE']
                    if page_blocks and 'Geometry' in page_blocks[0]:
                        print(f"    Available PAGE geometry keys: {list(page_blocks[0]['Geometry'].keys())}")
                    page_orientation_raw = 'ROTATE_0'  # Default fallback
                
                # Convert Textract orientation strings to degrees
                orientation_mapping = {
                    'ROTATE_0': 0,
                    'ROTATE_90': 90,
                    'ROTATE_180': 180,
                    'ROTATE_270': 270
                }
                
                # Handle both string and numeric values
                if isinstance(page_orientation_raw, str):
                    orientation_correction = orientation_mapping.get(page_orientation_raw, 0)
                else:
                    orientation_correction = page_orientation_raw or 0
                
                # Get confidence from the first table block for quality indication
                if 'Confidence' in table_blocks[0]:
                    confidence = table_blocks[0]['Confidence']
                
                page_info = {
                    'page_number': page_num + 1,
                    'table_count': len(table_blocks),
                    'orientation_correction': orientation_correction,
                    'textract_confidence': confidence,
                    'needs_rotation': orientation_correction != 0
                }
                pages_with_tables.append(page_num + 1)
                detection_results['pages_with_tables'].append(page_info)
                rotation_status = f"needs {orientation_correction}° rotation" if orientation_correction != 0 else "correctly oriented"
                print(f"Page {page_num + 1}: Contains {len(table_blocks)} table(s) - {rotation_status}")
            
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


def correct_table_orientations(pdf_path, pages_with_tables):
    """
    Create PDF with table pages only, applying orientation correction as needed
    
    Args:
        pdf_path: Path to the original PDF
        pages_with_tables: List of dicts with page info including orientation_correction
    
    Returns:
        Path to the output PDF file with table pages only
    """
    if not pages_with_tables:
        print("No pages with tables found")
        return None
    
    # Separate pages that need rotation vs those that don't
    pages_needing_rotation = [page for page in pages_with_tables if page.get('needs_rotation', False)]
    pages_correctly_oriented = [page for page in pages_with_tables if not page.get('needs_rotation', False)]
    
    print()
    print("=" * 50)
    print(f"CREATING TABLE-ONLY PDF")
    print(f"Total table pages: {len(pages_with_tables)}")
    print(f"Pages needing rotation: {len(pages_needing_rotation)}")
    print(f"Pages correctly oriented: {len(pages_correctly_oriented)}")
    
    if pages_needing_rotation:
        print("\nOrientation corrections needed:")
        for page in pages_needing_rotation:
            print(f"  Page {page['page_number']}: {page['orientation_correction']}° correction")
    
    if pages_correctly_oriented:
        print("\nPages already correctly oriented:")
        for page in pages_correctly_oriented:
            print(f"  Page {page['page_number']}: no rotation needed")
    
    # Create output path
    pdf_path_obj = Path(pdf_path)
    output_path = pdf_path_obj.parent / f"{pdf_path_obj.stem}_tables_oriented.pdf"
    
    # Open original PDF
    pdf_doc = fitz.open(pdf_path)
    
    # Create new PDF for output
    new_pdf = fitz.open()
    
    # Process ALL pages with tables (with and without rotation)
    all_table_pages = sorted(pages_with_tables, key=lambda x: x['page_number'])
    
    print(f"\nProcessing {len(all_table_pages)} table pages:")
    
    for page_info in all_table_pages:
        page_num = page_info['page_number'] - 1  # Convert to 0-indexed for PyMuPDF
        rotation_angle = page_info.get('orientation_correction', 0)
        
        original_page = pdf_doc[page_num]
        
        if rotation_angle != 0:
            print(f"  Adding page {page_info['page_number']} with {rotation_angle}° correction")
            original_page.set_rotation(rotation_angle)
        else:
            print(f"  Adding page {page_info['page_number']} (no rotation needed)")
        
        # Add page to new PDF
        new_pdf.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
    
    # Save the rotated PDF
    new_pdf.save(output_path)
    new_pdf.close()
    pdf_doc.close()
    
    print(f"\n✅ Table-only PDF saved to: {output_path}")
    print(f"📄 {len(all_table_pages)} table pages included")
    if pages_needing_rotation:
        print(f"🔄 {len(pages_needing_rotation)} pages had orientation corrected")
    print(f"🎯 Table content ready for extraction!")
    
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
    
    # Step 1: Detect tables and orientation
    print("🔍 STEP 1: DETECTING TABLES AND ORIENTATION WITH TEXTRACT")
    pages_with_tables = detect_tables(pdf_path, textract_client)
    
    if not pages_with_tables:
        print("\n❌ No tables found. No orientation correction needed.")
        return
    
    # Get detailed page info from detection results
    output_file = Path(pdf_path).stem + '_table_detection.json'
    output_path_json = Path(__file__).parent / output_file
    
    with open(output_path_json, 'r') as f:
        detection_results = json.load(f)
    
    # Step 2: Create table-only PDF with orientation corrections
    print("\n🔄 STEP 2: CREATING TABLE-ONLY PDF WITH CORRECTIONS")
    output_path = correct_table_orientations(pdf_path, detection_results['pages_with_tables'])
    
    if output_path:
        print(f"\n🎉 COMPLETE! Table-only PDF created with proper orientations.")
        print(f"📁 Output: {output_path}")
    else:
        print(f"\n❌ ERROR: Could not create table PDF.")
        print(f"📁 Check the original file: {pdf_path}")


if __name__ == "__main__":
    main()