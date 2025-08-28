#!/usr/bin/env python3
"""
PDF Table Detection and Rotation using Amazon Textract (Async Version)
Detects tables in PDF pages and rotates them 90 degrees for optimal extraction
"""

import sys
import asyncio
import aioboto3
import boto3
import fitz  # PyMuPDF
from pathlib import Path
import json
from datetime import datetime


async def detect_tables_async(s3_uri, textract_client, s3_client):
    """
    Detect tables in PDF using Amazon Textract (async job processing)
    
    Args:
        s3_uri: S3 URI (s3://bucket/key)
        textract_client: Async Textract client
        s3_client: Regular boto3 S3 client
    
    Returns:
        List of page numbers containing tables
    """
    # Parse S3 URI
    s3_parts = s3_uri.replace('s3://', '').split('/', 1)
    bucket_name = s3_parts[0]
    s3_key = s3_parts[1]
    pdf_name = Path(s3_key).name
    
    print(f"Processing PDF from S3: s3://{bucket_name}/{s3_key}")
    print()
    
    pages_with_tables = []
    detection_results = {
        'pdf_path': s3_uri,
        'pdf_name': pdf_name,
        'timestamp': datetime.now().isoformat(),
        'pages_with_tables': [],
        'summary': {}
    }
    
    try:
        # Start async job for table detection
        print("Starting Textract async job...")
        response = await textract_client.start_document_analysis(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': s3_key
                }
            },
            FeatureTypes=['TABLES']
        )
        
        job_id = response['JobId']
        print(f"Job ID: {job_id}")
        print("Waiting for job to complete...")
        
        # Poll for completion
        import time
        while True:
            job_status = await textract_client.get_document_analysis(JobId=job_id)
            status = job_status['JobStatus']
            
            if status == 'SUCCEEDED':
                print("✅ Job completed successfully!")
                break
            elif status == 'FAILED':
                print("❌ Job failed!")
                return []
            else:
                print(f"Job status: {status}... waiting 10 seconds")
                await asyncio.sleep(10)
        
        # Get all results (handle pagination)
        all_blocks = job_status['Blocks']
        next_token = job_status.get('NextToken')
        
        while next_token:
            print("Getting additional results...")
            job_status = await textract_client.get_document_analysis(
                JobId=job_id, 
                NextToken=next_token
            )
            all_blocks.extend(job_status['Blocks'])
            next_token = job_status.get('NextToken')
        
        # Process all blocks to find tables and their page numbers
        page_tables = {}
        for block in all_blocks:
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
        
        detection_results['total_pages'] = job_status.get('DocumentMetadata', {}).get('Pages', len(page_tables))
        
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
    output_file = Path(pdf_name).stem + '_table_detection.json'
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


def rotate_table_pages(s3_uri, page_numbers, s3_client):
    """
    Rotate the specified table pages 90 degrees and create output PDF
    
    Args:
        s3_uri: S3 URI (s3://bucket/key)
        page_numbers: List of page numbers to rotate
        s3_client: Regular boto3 S3 client
    
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
    
    # Parse S3 URI
    s3_parts = s3_uri.replace('s3://', '').split('/', 1)
    bucket_name = s3_parts[0]
    s3_key = s3_parts[1]
    pdf_name = Path(s3_key).name
    
    # Download PDF from S3 to temporary file
    response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
    pdf_bytes = response['Body'].read()
    
    # Create temporary local file
    temp_pdf_path = Path(__file__).parent / f"temp_{pdf_name}"
    with open(temp_pdf_path, 'wb') as f:
        f.write(pdf_bytes)
    
    # Create output path
    output_path = Path(__file__).parent / f"{Path(pdf_name).stem}_tables_rotated.pdf"
    
    # Open PDF from temporary file
    pdf_doc = fitz.open(str(temp_pdf_path))
    
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
    
    # Clean up temporary file
    temp_pdf_path.unlink()
    
    print(f"\n✅ Rotated PDF saved to: {output_path}")
    print(f"📄 {len(page_numbers)} pages rotated 90° clockwise")
    print(f"🎯 Ready for table extraction!")
    
    return str(output_path)


async def main():
    if len(sys.argv) != 2:
        print("Usage: python table_detector_async.py <s3_uri>")
        print("Example: python table_detector_async.py s3://bucket-name/path/to/document.pdf")
        sys.exit(1)
    
    s3_uri = sys.argv[1]
    
    if not s3_uri.startswith('s3://'):
        print(f"Error: Must provide S3 URI starting with 's3://'")
        print(f"Example: s3://bucket-name/path/to/document.pdf")
        sys.exit(1)
    
    # Initialize AWS clients (hybrid approach)
    try:
        # Regular boto3 for S3 operations (working credentials)
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # aioboto3 for async Textract operations
        session = aioboto3.Session()
        async with session.client('textract', region_name='us-east-1') as textract_client:
            # Step 1: Detect tables
            print("🔍 STEP 1: DETECTING TABLES WITH TEXTRACT (ASYNC)")
            pages_with_tables = await detect_tables_async(s3_uri, textract_client, s3_client)
            
            if not pages_with_tables:
                print("\n❌ No tables found. No rotation needed.")
                return
            
            # Step 2: Rotate table pages
            print("\n🔄 STEP 2: ROTATING TABLE PAGES")
            output_path = rotate_table_pages(s3_uri, pages_with_tables, s3_client)
            
            print(f"\n🎉 COMPLETE! Table pages detected and rotated.")
            print(f"📁 Output: {output_path}")
            
    except Exception as e:
        print(f"Error: Could not initialize AWS clients")
        print(f"Make sure AWS credentials are configured")
        print(f"Run 'aws configure' to set up credentials")
        print(f"Error details: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())