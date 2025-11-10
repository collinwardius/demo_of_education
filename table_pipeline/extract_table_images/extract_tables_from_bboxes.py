#!/usr/bin/env python3
"""
Extract table images from PDF using bounding box coordinates.

This script takes a JSON file with table bounding boxes (from Textract)
and extracts each table as a separate image file.
"""

import json
import argparse
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import os
import re


def sanitize_filename(text: str, max_length: int = 100) -> str:
    """
    Sanitize text for use in filename.

    Args:
        text: Text to sanitize
        max_length: Maximum filename length

    Returns:
        Sanitized filename string
    """
    if not text:
        return "untitled"

    # Remove or replace invalid filename characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)

    # Replace spaces and periods with underscores
    text = re.sub(r'[\s.]+', '_', text)

    # Remove multiple consecutive underscores
    text = re.sub(r'_+', '_', text)

    # Remove leading/trailing underscores
    text = text.strip('_')

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rstrip('_')

    return text.lower() if text else "untitled"


def extract_tables_from_pdf(pdf_path: str, bbox_json_path: str, output_dir: str, max_pages: int = None):
    """
    Extract table images from PDF using bounding boxes.

    Args:
        pdf_path: Path to original PDF file
        bbox_json_path: Path to JSON file with bounding box data
        output_dir: Directory to save extracted table images
        max_pages: Maximum pages to process (must match bbox extraction)
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Load bounding box data
    print(f"Loading bounding boxes from {bbox_json_path}...")
    with open(bbox_json_path, 'r') as f:
        bbox_data = json.load(f)

    tables = bbox_data['tables']
    print(f"Found {len(tables)} tables to extract")

    # Convert PDF pages to images
    print(f"Converting PDF to images (first {max_pages} pages)..." if max_pages else "Converting PDF to images...")

    # Convert only the pages we need
    if max_pages:
        pages = convert_from_path(pdf_path, first_page=1, last_page=max_pages, dpi=300)
    else:
        pages = convert_from_path(pdf_path, dpi=300)

    print(f"Converted {len(pages)} pages")

    # Track filenames to handle duplicates
    filename_counts = {}

    # Extract each table
    for i, table in enumerate(tables, 1):
        page_num = table['page']
        bbox = table['bounding_box']
        confidence = table['confidence']
        title = table.get('title', None)

        title_str = f"\"{title}\"" if title else "No title"
        print(f"\nExtracting Table {i}/{len(tables)}: Page {page_num}, Title: {title_str}, Confidence {confidence:.1f}%")

        # Get the page image (page numbers are 1-indexed in Textract, 0-indexed in list)
        page_image = pages[page_num - 1]
        width, height = page_image.size

        # Convert normalized coordinates to pixel coordinates
        left_px = int(bbox['left'] * width)
        top_px = int(bbox['top'] * height)
        right_px = int((bbox['left'] + bbox['width']) * width)
        bottom_px = int((bbox['top'] + bbox['height']) * height)

        # Crop the table region
        table_image = page_image.crop((left_px, top_px, right_px, bottom_px))

        # Create filename with title if available
        if title:
            sanitized_title = sanitize_filename(title, max_length=80)
            base_filename = f"page_{page_num:03d}_{sanitized_title}"
        else:
            base_filename = f"page_{page_num:03d}_table_{i:03d}"

        # Handle duplicate filenames by adding a counter
        if base_filename in filename_counts:
            filename_counts[base_filename] += 1
            output_filename = f"{base_filename}_{filename_counts[base_filename]}.png"
        else:
            filename_counts[base_filename] = 0
            output_filename = f"{base_filename}.png"

        output_filepath = output_path / output_filename
        table_image.save(output_filepath, 'PNG')

        print(f"  Saved: {output_filename} ({table_image.size[0]}x{table_image.size[1]} px)")

    print(f"\nDone! Extracted {len(tables)} tables to {output_dir}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract table images from PDF using bounding box coordinates'
    )
    parser.add_argument(
        'pdf_file',
        help='Path to PDF file'
    )
    parser.add_argument(
        'bbox_json',
        help='Path to JSON file with bounding box data'
    )
    parser.add_argument(
        'output_dir',
        help='Directory to save extracted table images'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        help='Maximum number of pages (must match bbox extraction)'
    )

    args = parser.parse_args()

    extract_tables_from_pdf(args.pdf_file, args.bbox_json, args.output_dir, args.max_pages)


if __name__ == '__main__':
    main()
