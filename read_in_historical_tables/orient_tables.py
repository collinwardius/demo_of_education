#!/usr/bin/env python3
"""
Table Orientation Analysis using Table Transformer
Analyzes orientation of tables on specific PDF pages identified by Textract
"""

import sys
import fitz  # PyMuPDF
from pathlib import Path
import numpy as np
from transformers import AutoImageProcessor, TableTransformerForObjectDetection
import torch
from PIL import Image
from io import BytesIO
import json


def analyze_table_orientation(pdf_path, page_numbers):
    """
    Analyze table orientation for specified pages using Table Transformer
    
    Args:
        pdf_path: Path to PDF file
        page_numbers: List of page numbers (1-indexed) that contain tables
    """
    
    # Initialize Table Transformer model
    print("Loading Table Transformer model...")
    processor = AutoImageProcessor.from_pretrained("microsoft/table-transformer-structure-recognition")
    model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-structure-recognition")
    
    # Open PDF
    pdf_doc = fitz.open(pdf_path)
    
    results = {}
    
    for page_num in page_numbers:
        print(f"\nAnalyzing orientation for page {page_num}...")
        
        # Convert page to image (0-indexed)
        page = pdf_doc[page_num - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(BytesIO(img_data))
        
        # Process with Table Transformer
        inputs = processor(images=image, return_tensors="pt")
        outputs = model(**inputs)
        
        # Analyze the detected table structure for orientation cues
        target_sizes = torch.tensor([image.size[::-1]])
        results_dict = processor.post_process_object_detection(outputs, target_sizes=target_sizes)[0]
        
        # Extract orientation information
        orientation_info = analyze_detection_results(results_dict, image.size)
        results[page_num] = orientation_info
        
        print(f"Page {page_num} orientation: {orientation_info['orientation']}")
        print(f"Confidence: {orientation_info['confidence']:.2f}")
        
    pdf_doc.close()
    return results


def analyze_detection_results(detection_results, image_size):
    """
    Analyze Table Transformer detection results to determine table orientation
    """
    
    boxes = detection_results["boxes"].detach().cpu().numpy()
    scores = detection_results["scores"].detach().cpu().numpy()
    labels = detection_results["labels"].detach().cpu().numpy()
    
    # Filter for high-confidence detections
    high_conf_indices = scores > 0.5
    boxes = boxes[high_conf_indices]
    scores = scores[high_conf_indices]
    labels = labels[high_conf_indices]
    
    if len(boxes) == 0:
        return {
            'orientation': 'unknown',
            'confidence': 0.0,
            'reason': 'No high-confidence detections'
        }
    
    # Analyze box dimensions and positions to determine orientation
    width, height = image_size
    
    # Calculate aspect ratios and positions
    box_aspects = []
    box_positions = []
    
    for box in boxes:
        x1, y1, x2, y2 = box
        box_width = x2 - x1
        box_height = y2 - y1
        aspect_ratio = box_width / box_height
        
        # Normalize positions
        center_x = (x1 + x2) / 2 / width
        center_y = (y1 + y2) / 2 / height
        
        box_aspects.append(aspect_ratio)
        box_positions.append((center_x, center_y))
    
    # Determine orientation based on aspect ratios and layout
    avg_aspect = np.mean(box_aspects)
    
    if avg_aspect > 2.0:
        orientation = 'landscape'
        confidence = min(0.9, avg_aspect / 3.0)
        reason = f'Wide tables detected (avg aspect: {avg_aspect:.2f})'
    elif avg_aspect < 0.5:
        orientation = 'portrait'
        confidence = min(0.9, 2.0 / avg_aspect / 4.0)
        reason = f'Tall tables detected (avg aspect: {avg_aspect:.2f})'
    else:
        # Analyze spatial distribution
        positions = np.array(box_positions)
        if len(positions) > 1:
            x_spread = np.std(positions[:, 0])
            y_spread = np.std(positions[:, 1])
            
            if x_spread > y_spread * 1.5:
                orientation = 'landscape'
                confidence = 0.7
                reason = 'Horizontally distributed tables'
            elif y_spread > x_spread * 1.5:
                orientation = 'portrait'
                confidence = 0.7
                reason = 'Vertically distributed tables'
            else:
                orientation = 'normal'
                confidence = 0.6
                reason = 'Balanced table layout'
        else:
            orientation = 'normal'
            confidence = 0.5
            reason = f'Single table with normal aspect ratio ({avg_aspect:.2f})'
    
    return {
        'orientation': orientation,
        'confidence': confidence,
        'reason': reason,
        'avg_aspect_ratio': avg_aspect,
        'num_tables_detected': len(boxes)
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python orient_tables.py <detection_json_file>")
        print("Example: python orient_tables.py read_in_historical_tables/document_table_detection.json")
        print("Or: python orient_tables.py document  (will look for document_table_detection.json)")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    
    # Handle both full JSON path or just PDF name
    if input_arg.endswith('.json'):
        json_path = Path(input_arg)
    else:
        # Assume it's a PDF name, construct the detection file path
        pdf_name = Path(input_arg).stem
        json_path = Path('read_in_historical_tables') / f"{pdf_name}_table_detection.json"
    
    if not json_path.exists():
        print(f"Error: Detection results file not found: {json_path}")
        print("Run table_detector.py first to generate detection results")
        sys.exit(1)
    
    # Load detection results
    with open(json_path, 'r') as f:
        detection_data = json.load(f)
    
    pdf_path = detection_data['pdf_path']
    page_numbers = [p['page_number'] for p in detection_data['pages_with_tables']]
    
    if not page_numbers:
        print("No pages with tables found in detection results")
        sys.exit(0)
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' not found")
        sys.exit(1)
    
    print(f"Analyzing table orientation in: {Path(pdf_path).name}")
    print(f"Loading detection results from: {json_path}")
    print(f"Pages to analyze: {', '.join(map(str, page_numbers))}")
    
    try:
        results = analyze_table_orientation(pdf_path, page_numbers)
        
        # Summary
        print("\n" + "=" * 60)
        print("TABLE ORIENTATION ANALYSIS SUMMARY")
        print("=" * 60)
        
        for page_num, info in results.items():
            print(f"\nPage {page_num}:")
            print(f"  Orientation: {info['orientation'].upper()}")
            print(f"  Confidence: {info['confidence']:.2f}")
            print(f"  Reason: {info['reason']}")
            print(f"  Tables detected: {info['num_tables_detected']}")
            print(f"  Avg aspect ratio: {info['avg_aspect_ratio']:.2f}")
            
    except ImportError as e:
        print(f"Error: Missing required dependencies")
        print(f"Install with: pip install transformers torch pillow")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing orientation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()