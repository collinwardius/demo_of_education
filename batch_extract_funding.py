#!/usr/bin/env python3
"""
Batch process all PDF files in cleaned_scans directory to extract state funding tables.
"""

import os
import subprocess
from pathlib import Path

def batch_extract_funding():
    # Path to the cleaned_scans directory
    cleaned_scans_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/scans/cleaned_scans"

    # Output directory for funding tables
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/scans/funding_tables"

    # Path to the extraction script
    script_path = "/Users/cjwardius/Documents/GitHub/demo_of_education/extract_funding_tables.py"

    if not os.path.exists(cleaned_scans_dir):
        print(f"Error: Directory not found: {cleaned_scans_dir}")
        return

    if not os.path.exists(script_path):
        print(f"Error: Script not found: {script_path}")
        return

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Find all PDF files in the directory
    pdf_files = list(Path(cleaned_scans_dir).glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in cleaned_scans directory")
        return

    print(f"Found {len(pdf_files)} PDF files to process:")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    print()

    results = []

    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")

        # Generate output filename in funding_tables directory
        output_name = pdf_file.stem + "_funding_tables.pdf"
        output_path = Path(output_dir) / output_name

        # Run the extraction script
        try:
            result = subprocess.run([
                "python", script_path,
                str(pdf_file),
                str(output_path)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                results.append((pdf_file.name, "SUCCESS", "State funding tables extracted"))
                print(f"✓ Success: {pdf_file.name}")
            else:
                results.append((pdf_file.name, "NO_FUNDING", "No state funding tables found"))
                print(f"✗ No funding tables: {pdf_file.name}")

            # Print any output from the script
            if result.stdout:
                print(result.stdout)

        except Exception as e:
            results.append((pdf_file.name, "ERROR", str(e)))
            print(f"✗ Error processing {pdf_file.name}: {e}")

        print("-" * 50)

    # Summary
    print("\nSUMMARY:")
    print(f"Total files processed: {len(pdf_files)}")

    success_count = sum(1 for _, status, _ in results if status == "SUCCESS")
    no_funding_count = sum(1 for _, status, _ in results if status == "NO_FUNDING")
    error_count = sum(1 for _, status, _ in results if status == "ERROR")

    print(f"Files with state funding tables: {success_count}")
    print(f"Files without state funding tables: {no_funding_count}")
    print(f"Files with errors: {error_count}")

    if success_count > 0:
        print(f"\nFiles with state funding tables extracted to: {output_dir}")
        for filename, status, message in results:
            if status == "SUCCESS":
                print(f"  ✓ {filename}")

    if no_funding_count > 0:
        print("\nFiles without state funding tables:")
        for filename, status, message in results:
            if status == "NO_FUNDING":
                print(f"  - {filename}")

    if error_count > 0:
        print("\nFiles with errors:")
        for filename, status, message in results:
            if status == "ERROR":
                print(f"  ✗ {filename}: {message}")

if __name__ == "__main__":
    batch_extract_funding()
