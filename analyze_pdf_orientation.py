#!/usr/bin/env python3
"""
Diagnostic script to analyze PDF orientation and table layout.
"""

from pathlib import Path
from PyPDF2 import PdfReader

def analyze_pdf(pdf_path):
    """
    Analyze PDF orientation and existing rotation.
    """
    reader = PdfReader(pdf_path)

    print(f"\n{'='*60}")
    print(f"File: {pdf_path.name}")
    print(f"Total pages: {len(reader.pages)}")
    print(f"{'='*60}")

    for i, page in enumerate(reader.pages):
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)

        # Get current rotation if any
        rotation = page.get("/Rotate", 0)

        # Determine orientation
        orientation = "Landscape" if width > height else "Portrait" if height > width else "Square"

        print(f"Page {i+1}:")
        print(f"  Dimensions: {width:.1f} x {height:.1f}")
        print(f"  Current Rotation: {rotation}°")
        print(f"  Orientation: {orientation}")

        # Calculate what it would be after 90° rotation
        if rotation == 90 or rotation == 270:
            print(f"  Note: Already rotated, effective dimensions: {height:.1f} x {width:.1f}")

def main():
    source_dir = Path("/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/scans/cleaned_scans")

    # Get first few PDFs to analyze
    pdf_files = list(source_dir.glob("*.pdf"))[:3]

    print(f"Analyzing {len(pdf_files)} sample PDF files...\n")

    for pdf_file in pdf_files:
        try:
            analyze_pdf(pdf_file)
        except Exception as e:
            print(f"Error analyzing {pdf_file.name}: {e}")

if __name__ == "__main__":
    main()
