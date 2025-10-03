#!/usr/bin/env python3
"""
Extract pages containing state funding of higher education tables from PDF files.
"""

import re
from pypdf import PdfReader, PdfWriter
import argparse
import os
from pathlib import Path

def matches_funding_criteria(text):
    """
    Check if page text contains state funding of higher education content.
    Focus on pages with 'receipts' in table titles.
    """
    text_lower = text.lower()

    # Primary keyword: receipts (commonly used in funding tables)
    has_receipts = 'receipts' in text_lower

    # Table indicators
    table_indicators = ['table', 'column']

    # Check for table structure indicators
    has_table_structure = any(indicator in text_lower for indicator in table_indicators)

    # Look for monetary patterns (dollar amounts)
    has_money_pattern = bool(re.search(r'\$\s*\d+', text)) or bool(re.search(r'\d+\s*dollars?', text_lower))

    # Look for year patterns (1900-1949)
    has_year_pattern = bool(re.search(r'\b19[0-4]\d\b', text))

    # Require receipts keyword plus at least one other indicator
    return has_receipts and (has_table_structure or has_money_pattern or has_year_pattern)

def has_title_or_header(text):
    """
    Check if page has a title or header (indicating it's a new section, not a continuation).
    """
    text_lower = text.lower()

    # Check first 300 characters for title indicators
    first_section = text_lower[:300]

    # Look for common title/header keywords
    title_keywords = ['table', 'chapter', 'section', 'part', 'appendix']

    return any(keyword in first_section for keyword in title_keywords)

def extract_funding_pages(input_pdf_path, output_pdf_path):
    """
    Extract pages with state funding tables from PDF.
    Includes the next page if it has no title/header.
    """
    print(f"Processing: {input_pdf_path}")

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    matching_pages = []
    pages_to_include = set()

    total_pages = len(reader.pages)
    print(f"Total pages: {total_pages}")

    # First pass: identify receipts pages
    for page_num, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text()

            if matches_funding_criteria(text):
                pages_to_include.add(page_num)
                print(f"Page {page_num}: Found state funding-related content")

                # Preview of found text (first 200 chars)
                preview = text.replace('\n', ' ').strip()[:200]
                print(f"  Preview: {preview}...")

        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            continue

    # Second pass: check immediate next page after each receipts page
    for page_num in sorted(pages_to_include.copy()):
        next_page_num = page_num + 1
        if next_page_num <= total_pages and next_page_num not in pages_to_include:
            try:
                next_page = reader.pages[next_page_num - 1]
                next_text = next_page.extract_text()

                if not has_title_or_header(next_text):
                    pages_to_include.add(next_page_num)
                    print(f"Page {next_page_num}: Added as continuation (no title/header)")

            except Exception as e:
                print(f"Error checking page {next_page_num}: {e}")
                continue

    # Add all pages to output in order
    matching_pages = sorted(pages_to_include)
    for page_num in matching_pages:
        writer.add_page(reader.pages[page_num - 1])

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
        print("\nNo pages with state funding-related content found.")
        print("No output PDF created.")
        return None

def main():
    parser = argparse.ArgumentParser(description='Extract state funding-related pages from PDF')
    parser.add_argument('input_pdf', help='Input PDF file path')
    parser.add_argument('output_pdf', help='Output PDF file path')

    args = parser.parse_args()

    if not os.path.exists(args.input_pdf):
        print(f"Error: Input file not found: {args.input_pdf}")
        return 1

    try:
        result = extract_funding_pages(args.input_pdf, args.output_pdf)
        if result is None:
            return 1  # Return 1 to indicate no funding tables found
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
