#!/usr/bin/env python3
"""
Extract table bounding boxes from PDF using AWS Textract (simplified polling version).

This script uploads a PDF to S3, runs Textract analysis, and extracts
bounding box coordinates for all detected tables using direct status polling.
"""

import boto3
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
import sys
import os
from pypdf import PdfReader, PdfWriter


class TableBoundingBoxExtractor:
    """Extract table bounding boxes from PDF using AWS Textract."""

    def __init__(self, bucket_name: str, region: str = 'us-east-2'):
        """
        Initialize the extractor.

        Args:
            bucket_name: S3 bucket name for temporary storage
            region: AWS region (default: us-east-2)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        self.textract_client = boto3.client('textract', region_name=region)

    def split_pdf(self, pdf_path: str, max_pages: int, output_path: str) -> str:
        """
        Split PDF to extract only first N pages.

        Args:
            pdf_path: Path to original PDF file
            max_pages: Maximum number of pages to extract
            output_path: Path to save the split PDF

        Returns:
            Path to the split PDF file
        """
        print(f"Splitting PDF to extract first {max_pages} pages...")

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        if max_pages >= total_pages:
            print(f"PDF has only {total_pages} pages, using original file")
            return pdf_path

        writer = PdfWriter()
        for i in range(min(max_pages, total_pages)):
            writer.add_page(reader.pages[i])

        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        print(f"Created temporary PDF with {max_pages} pages: {output_path}")
        return output_path

    def upload_pdf_to_s3(self, pdf_path: str) -> str:
        """
        Upload PDF to S3.

        Args:
            pdf_path: Path to PDF file

        Returns:
            S3 key of uploaded file
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        s3_key = f"temp/{pdf_file.name}"

        print(f"Uploading {pdf_file.name} to S3...")
        self.s3_client.upload_file(str(pdf_file), self.bucket_name, s3_key)
        print(f"Upload complete: s3://{self.bucket_name}/{s3_key}")

        return s3_key

    def start_textract_analysis(self, s3_key: str) -> str:
        """
        Start Textract document analysis.

        Args:
            s3_key: S3 key of document to analyze

        Returns:
            Job ID
        """
        print(f"Starting Textract analysis for s3://{self.bucket_name}/{s3_key}")

        response = self.textract_client.start_document_analysis(
            DocumentLocation={
                'S3Object': {
                    'Bucket': self.bucket_name,
                    'Name': s3_key
                }
            },
            FeatureTypes=['TABLES']
        )

        job_id = response['JobId']
        print(f"Job started: {job_id}")
        return job_id

    def wait_for_completion(self, job_id: str, poll_interval: int = 5) -> bool:
        """
        Wait for Textract job to complete by polling status.

        Args:
            job_id: Textract job ID
            poll_interval: Seconds between status checks

        Returns:
            True if succeeded, False otherwise
        """
        print("Waiting for job completion (polling every 5 seconds)...")

        while True:
            response = self.textract_client.get_document_analysis(JobId=job_id)
            status = response['JobStatus']

            print(f"  Status: {status}")

            if status == 'SUCCEEDED':
                print("Job completed successfully!")
                return True
            elif status == 'FAILED':
                print(f"Job failed: {response.get('StatusMessage', 'Unknown error')}")
                return False
            elif status in ['IN_PROGRESS', 'PARTIAL_SUCCESS']:
                time.sleep(poll_interval)
            else:
                print(f"Unexpected status: {status}")
                return False

    def extract_table_bboxes(self, job_id: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract table bounding boxes and titles from Textract results.

        Args:
            job_id: Textract job ID

        Returns:
            Tuple of (tables list, all_blocks list)
        """
        print("Extracting table bounding boxes and titles...")

        all_blocks = []
        next_token = None

        # First, collect all blocks
        while True:
            # Get results
            if next_token:
                response = self.textract_client.get_document_analysis(
                    JobId=job_id,
                    NextToken=next_token
                )
            else:
                response = self.textract_client.get_document_analysis(JobId=job_id)

            all_blocks.extend(response.get('Blocks', []))

            # Check for more pages
            next_token = response.get('NextToken')
            if not next_token:
                break

        # Create block lookup map
        block_map = {block['Id']: block for block in all_blocks}

        # Extract table titles
        title_blocks = [b for b in all_blocks if b.get('BlockType') == 'TABLE_TITLE']

        # Create a map of page -> titles for matching
        page_titles = {}
        for title_block in title_blocks:
            page = title_block.get('Page')

            # Get title text from child WORD blocks
            title_text = ''
            if 'Relationships' in title_block:
                for rel in title_block['Relationships']:
                    if rel['Type'] == 'CHILD':
                        child_texts = []
                        for child_id in rel['Ids']:
                            child = block_map.get(child_id)
                            if child and 'Text' in child:
                                child_texts.append(child['Text'])
                        title_text = ' '.join(child_texts)

            if page not in page_titles:
                page_titles[page] = []

            page_titles[page].append({
                'text': title_text,
                'top': title_block.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0),
                'confidence': title_block.get('Confidence')
            })

        # Extract TABLE blocks with associated titles
        tables = []
        for block in all_blocks:
            if block['BlockType'] == 'TABLE':
                # Extract bounding box
                bbox = block.get('Geometry', {}).get('BoundingBox', {})
                page = block.get('Page', None)
                table_top = bbox.get('Top', 0)

                table_info = {
                    'id': block['Id'],
                    'page': page,
                    'confidence': block.get('Confidence', None),
                    'bounding_box': {
                        'left': bbox.get('Left', 0),
                        'top': table_top,
                        'width': bbox.get('Width', 0),
                        'height': bbox.get('Height', 0)
                    },
                    'polygon': block.get('Geometry', {}).get('Polygon', []),
                    'title': None,
                    'title_confidence': None
                }

                # Find the closest title above the table on the same page
                if page in page_titles:
                    # Find titles above this table (title.top < table.top)
                    titles_above = [t for t in page_titles[page] if t['top'] < table_top]

                    # Get the closest one (highest top value that's still less than table top)
                    if titles_above:
                        closest_title = max(titles_above, key=lambda t: t['top'])
                        table_info['title'] = closest_title['text']
                        table_info['title_confidence'] = closest_title['confidence']

                # Count rows and columns if relationships exist
                if 'Relationships' in block:
                    for relationship in block['Relationships']:
                        if relationship['Type'] == 'CHILD':
                            table_info['cell_ids'] = relationship['Ids']

                tables.append(table_info)

        print(f"Found {len(tables)} tables and {len(title_blocks)} titles")
        print(f"Saving {len(all_blocks)} total blocks (includes CELL and WORD blocks for text extraction)")
        return tables, all_blocks

    def process_pdf(self, pdf_path: str, output_path: str, max_pages: int = None):
        """
        Complete workflow to extract table bounding boxes.

        Args:
            pdf_path: Path to PDF file
            output_path: Path to save JSON output
            max_pages: Maximum number of pages to process
        """
        temp_pdf_path = None
        try:
            # Split PDF if max_pages is specified
            pdf_to_upload = pdf_path
            if max_pages:
                temp_pdf_path = f"/tmp/temp_pages_{int(time.time())}.pdf"
                pdf_to_upload = self.split_pdf(pdf_path, max_pages, temp_pdf_path)

            # Upload PDF to S3
            s3_key = self.upload_pdf_to_s3(pdf_to_upload)

            # Start Textract analysis
            job_id = self.start_textract_analysis(s3_key)

            # Wait for completion
            success = self.wait_for_completion(job_id)

            if not success:
                print("ERROR: Textract job failed")
                sys.exit(1)

            # Extract bounding boxes and ALL blocks
            tables, all_blocks = self.extract_table_bboxes(job_id)

            # Save results including all blocks for text extraction later
            output_data = {
                'pdf_file': Path(pdf_path).name,
                's3_bucket': self.bucket_name,
                's3_key': s3_key,
                'job_id': job_id,
                'total_tables': len(tables),
                'tables': tables,
                'all_blocks': all_blocks  # Save all blocks for CSV extraction
            }

            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)

            print(f"\nResults saved to: {output_path}")
            print(f"Total tables found: {len(tables)}")

            # Print summary
            print("\nTable Summary:")
            for i, table in enumerate(tables, 1):
                title_str = f"\"{table['title']}\"" if table['title'] else "No title"
                print(f"  Table {i}: Page {table['page']}, "
                      f"Title: {title_str}, "
                      f"Confidence: {table['confidence']:.1f}%")

        finally:
            # Remove temporary PDF if it was created
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                print(f"\nRemoved temporary PDF: {temp_pdf_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract table bounding boxes from PDF using AWS Textract'
    )
    parser.add_argument(
        'pdf_file',
        help='Path to PDF file'
    )
    parser.add_argument(
        'bucket_name',
        help='S3 bucket name for temporary storage'
    )
    parser.add_argument(
        '--output',
        default='table_bboxes.json',
        help='Output JSON file path (default: table_bboxes.json)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        help='Maximum number of pages to process'
    )
    parser.add_argument(
        '--region',
        default='us-east-2',
        help='AWS region (default: us-east-2)'
    )

    args = parser.parse_args()

    # Create extractor and process
    extractor = TableBoundingBoxExtractor(args.bucket_name, args.region)
    extractor.process_pdf(args.pdf_file, args.output, args.max_pages)

    print("\nDone!")


if __name__ == '__main__':
    main()
