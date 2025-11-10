#!/usr/bin/env python3
"""
Master program to extract tables from PDFs using AWS Textract.

This program orchestrates the complete workflow:
1. Extract table bounding boxes and metadata from PDF (saves to json/)
2. Extract table images as PNGs (saves to png/)
3. Extract table text as CSVs (saves to csv/)

All outputs are organized in subdirectories within a specified output directory.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def create_output_structure(output_dir: str) -> dict:
    """
    Create output directory structure.

    Args:
        output_dir: Base output directory

    Returns:
        Dictionary with paths to subdirectories
    """
    base_path = Path(output_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    subdirs = {
        'json': base_path / 'json',
        'csv': base_path / 'csv',
        'png': base_path / 'png'
    }

    for name, path in subdirs.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

    return subdirs


def run_command(cmd: list, description: str):
    """
    Run a subprocess command and handle errors.

    Args:
        cmd: Command and arguments as list
        description: Description of what the command does
    """
    print(f"\n{'='*60}")
    print(f"Step: {description}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"\nERROR: {description} failed with exit code {result.returncode}")
        sys.exit(1)

    print(f"\n✓ {description} completed successfully")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Master program to extract tables from PDFs using AWS Textract',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python3 extract_tables_master.py \\
    /path/to/document.pdf \\
    /path/to/output/directory \\
    historical-education-college-tables \\
    --max-pages 20 \\
    --region us-east-2

This will create:
  /path/to/output/directory/json/    - Textract results (JSON)
  /path/to/output/directory/png/     - Table images
  /path/to/output/directory/csv/     - Table data
        """
    )

    parser.add_argument(
        'pdf_file',
        help='Path to PDF file to process'
    )
    parser.add_argument(
        'output_dir',
        help='Base directory for all outputs (will create json/, csv/, png/ subdirs)'
    )
    parser.add_argument(
        'bucket_name',
        help='S3 bucket name for temporary storage'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        help='Maximum number of pages to process (optional, for testing)'
    )
    parser.add_argument(
        '--region',
        default='us-east-2',
        help='AWS region (default: us-east-2)'
    )
    parser.add_argument(
        '--skip-bbox',
        action='store_true',
        help='Skip bounding box extraction (use existing JSON file)'
    )
    parser.add_argument(
        '--skip-png',
        action='store_true',
        help='Skip PNG extraction'
    )
    parser.add_argument(
        '--skip-csv',
        action='store_true',
        help='Skip CSV extraction'
    )

    args = parser.parse_args()

    # Get the directory where this script is located
    script_dir = Path(__file__).parent

    print(f"\n{'='*60}")
    print("Table Extraction Master Program")
    print(f"{'='*60}")
    print(f"PDF: {args.pdf_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"S3 bucket: {args.bucket_name}")
    if args.max_pages:
        print(f"Max pages: {args.max_pages}")
    print(f"Region: {args.region}")

    # Create output directory structure
    print(f"\n{'='*60}")
    print("Creating Output Directory Structure")
    print(f"{'='*60}")
    subdirs = create_output_structure(args.output_dir)

    # Determine JSON filename from PDF
    pdf_name = Path(args.pdf_file).stem
    json_filename = f"{pdf_name}_textract.json"
    json_path = subdirs['json'] / json_filename

    # Step 1: Extract bounding boxes and metadata
    if not args.skip_bbox:
        cmd = [
            'python3',
            str(script_dir / 'extract_table_bboxes_simple.py'),
            args.pdf_file,
            args.bucket_name,
            '--output', str(json_path),
            '--region', args.region
        ]

        if args.max_pages:
            cmd.extend(['--max-pages', str(args.max_pages)])

        run_command(cmd, "Extract table bounding boxes and metadata (Textract)")
    else:
        print(f"\nSkipping bounding box extraction (using existing JSON)")
        if not json_path.exists():
            print(f"ERROR: JSON file not found: {json_path}")
            sys.exit(1)

    # Step 2: Extract PNG images
    if not args.skip_png:
        cmd = [
            'python3',
            str(script_dir / 'extract_tables_from_bboxes.py'),
            args.pdf_file,
            str(json_path),
            str(subdirs['png'])
        ]

        if args.max_pages:
            cmd.extend(['--max-pages', str(args.max_pages)])

        run_command(cmd, "Extract table images (PNG)")
    else:
        print(f"\nSkipping PNG extraction")

    # Step 3: Extract CSV data
    if not args.skip_csv:
        cmd = [
            'python3',
            str(script_dir / 'extract_table_text_to_csv.py'),
            str(json_path),
            str(subdirs['csv'])
        ]

        run_command(cmd, "Extract table text (CSV)")
    else:
        print(f"\nSkipping CSV extraction")

    # Summary
    print(f"\n{'='*60}")
    print("Extraction Complete!")
    print(f"{'='*60}")
    print(f"\nOutputs saved to: {args.output_dir}")
    print(f"  JSON: {subdirs['json']}")
    print(f"  PNG:  {subdirs['png']}")
    print(f"  CSV:  {subdirs['csv']}")
    print()


if __name__ == '__main__':
    main()
