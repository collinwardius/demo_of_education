#!/usr/bin/env python3
"""
Extract pages containing tuition-related tables from PDF files.
"""

import re
from pypdf import PdfReader, PdfWriter
import argparse
import os
from pathlib import Path

def matches_tuition_criteria(text):
    """
    Check if page text contains tuition-related content.
    """
    text_lower = text.lower()

    # Primary tuition keywords
    tuition_keywords = [
        'tuition', 'fees', 'charges', 'cost', 'expense',
        'room and board', 'boarding', 'laboratory fee',
        'registration fee', 'matriculation', 'diploma fee'
    ]

    # Table indicators
    table_indicators = [
        'table', 'column', 'per year', 'per semester',
        'annual', 'quarterly', '$', 'dollar'
    ]

    # Check for tuition keywords
    has_tuition = any(keyword in text_lower for keyword in tuition_keywords)

    # Check for table structure indicators
    has_table_structure = any(indicator in text_lower for indicator in table_indicators)

    # Look for monetary patterns (dollar amounts)
    has_money_pattern = bool(re.search(r'\$\s*\d+', text)) or bool(re.search(r'\d+\s*dollars?', text_lower))

    # Look for academic year patterns
    has_year_pattern = bool(re.search(r'\b19[0-4]\d\b', text))

    # Require tuition keyword plus at least one other indicator
    return has_tuition and (has_table_structure or has_money_pattern or has_year_pattern)

def extract_tuition_pages(input_pdf_path, output_pdf_path):
    """
    Extract pages with tuition-related tables from PDF.
    """
    print(f"Processing: {input_pdf_path}")

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    matching_pages = []

    total_pages = len(reader.pages)
    print(f"Total pages: {total_pages}")

    for page_num, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text()

            if matches_tuition_criteria(text):
                matching_pages.append(page_num)
                writer.add_page(page)
                print(f"Page {page_num}: Found tuition-related content")

                # Preview of found text (first 200 chars)
                preview = text.replace('\n', ' ').strip()[:200]
                print(f"  Preview: {preview}...")

        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            continue

    if matching_pages:
        # Create output directory if it doesn't exist
        output_path = Path(output_pdf_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)

        print(f"\nExtracted {len(matching_pages)} pages to: {output_pdf_path}")
        print(f"Pages extracted: {matching_pages}")
        return matching_pages
    else:
        print("\nNo pages with tuition-related content found.")
        print("No output PDF created.")
        return None

def main():
    parser = argparse.ArgumentParser(description='Extract tuition-related pages from PDF')
    parser.add_argument('input_pdf', help='Input PDF file path')
    parser.add_argument('output_pdf', help='Output PDF file path')

    args = parser.parse_args()

    if not os.path.exists(args.input_pdf):
        print(f"Error: Input file not found: {args.input_pdf}")
        return 1

    try:
        result = extract_tuition_pages(args.input_pdf, args.output_pdf)
        if result is None:
            return 1  # Return 1 to indicate no tuition tables found
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())