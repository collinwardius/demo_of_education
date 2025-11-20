#!/usr/bin/env python3
"""
College Table Annotation Tool
=============================
A simple web-based interface for annotating college table images with:
- Rotation degrees (for image alignment correction)
- Column names (for table structure documentation)
- Inheritance from previous table (for multi-page tables)

Usage:
    python 5_annotate_college_tables.py --input-dir /path/to/college_tables/png

The tool will:
1. Start a local web server at http://localhost:5000
2. Display each table image for annotation
3. Save annotations to college_table_annotations.json
4. Allow you to navigate between images and inherit column data
"""

import argparse
import json
import os
import subprocess
import platform
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import webbrowser
from threading import Timer

app = Flask(__name__)

# Global state
IMAGE_DIR = None
IMAGE_FILES = []
ANNOTATION_FILE = None
annotations = {}


def load_annotations():
    """Load existing annotations from JSON file."""
    global annotations
    if ANNOTATION_FILE.exists():
        with open(ANNOTATION_FILE, 'r') as f:
            annotations = json.load(f)
    else:
        annotations = {}


def save_annotations():
    """Save annotations to JSON file."""
    with open(ANNOTATION_FILE, 'w') as f:
        json.dump(annotations, f, indent=2)


def get_image_files(directory):
    """Get all PNG files from directory, sorted by filename."""
    image_dir = Path(directory)
    if not image_dir.exists():
        raise ValueError(f"Directory does not exist: {directory}")

    files = sorted([f.name for f in image_dir.glob("*.png")])
    if not files:
        raise ValueError(f"No PNG files found in: {directory}")

    return files


@app.route('/')
def index():
    """Render the main annotation interface."""
    return render_template('annotate.html')


@app.route('/directory')
def directory():
    """Render the directory overview page."""
    return render_template('directory.html')


@app.route('/api/images')
def get_images():
    """Get list of all images and their annotation status."""
    image_data = []
    for idx, filename in enumerate(IMAGE_FILES):
        is_annotated = filename in annotations
        annotation_info = None
        if is_annotated:
            annotation_info = {
                'rotation_degrees': annotations[filename].get('rotation_degrees', 0),
                'column_names': annotations[filename].get('column_names', []),
                'inherited_from': annotations[filename].get('inherited_from'),
                'status': annotations[filename].get('status', 'annotated'),
                'annotated_date': annotations[filename].get('annotated_date')
            }

        image_data.append({
            'index': idx,
            'filename': filename,
            'annotated': is_annotated,
            'annotation': annotation_info
        })

    return jsonify({
        'images': image_data,
        'total': len(IMAGE_FILES),
        'annotated_count': len(annotations)
    })


@app.route('/api/image/<int:index>')
def get_image_data(index):
    """Get data for a specific image by index."""
    if index < 0 or index >= len(IMAGE_FILES):
        return jsonify({'error': 'Invalid image index'}), 404

    filename = IMAGE_FILES[index]
    annotation = annotations.get(filename, {})

    # Get previous image data for inheritance
    previous_data = None
    if index > 0:
        prev_filename = IMAGE_FILES[index - 1]
        if prev_filename in annotations:
            previous_data = {
                'filename': prev_filename,
                'rotation_degrees': annotations[prev_filename].get('rotation_degrees', 0),
                'column_names': annotations[prev_filename].get('column_names', [])
            }

    return jsonify({
        'index': index,
        'filename': filename,
        'total': len(IMAGE_FILES),
        'annotation': annotation,
        'previous': previous_data
    })


@app.route('/api/save', methods=['POST'])
def save_annotation():
    """Save annotation for an image."""
    data = request.json
    filename = data.get('filename')

    if not filename or filename not in IMAGE_FILES:
        return jsonify({'error': 'Invalid filename'}), 400

    # Parse column names (split by comma if string)
    column_names = data.get('column_names', [])
    if isinstance(column_names, str):
        column_names = [col.strip() for col in column_names.split(',') if col.strip()]

    # Create annotation entry
    annotations[filename] = {
        'rotation_degrees': float(data.get('rotation_degrees', 0)),
        'column_names': column_names,
        'inherited_from': data.get('inherited_from'),
        'status': data.get('status', 'annotated'),
        'annotated_date': datetime.now().isoformat()
    }

    # Save to file
    save_annotations()

    return jsonify({
        'success': True,
        'annotated_count': len(annotations),
        'total': len(IMAGE_FILES)
    })


@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_annotation(filename):
    """Delete annotation for an image."""
    if filename in annotations:
        del annotations[filename]
        save_annotations()
        return jsonify({'success': True})
    return jsonify({'error': 'Annotation not found'}), 404


@app.route('/api/exempt', methods=['POST'])
def mark_exempt():
    """Mark an image as exempt from annotation."""
    data = request.json
    filename = data.get('filename')

    if not filename or filename not in IMAGE_FILES:
        return jsonify({'error': 'Invalid filename'}), 400

    # Create exempt annotation entry
    annotations[filename] = {
        'rotation_degrees': 0,
        'column_names': [],
        'inherited_from': None,
        'status': 'exempt',
        'annotated_date': datetime.now().isoformat()
    }

    # Save to file
    save_annotations()

    return jsonify({
        'success': True,
        'annotated_count': len(annotations),
        'total': len(IMAGE_FILES)
    })


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve image files."""
    return send_from_directory(IMAGE_DIR, filename)


def open_browser(port=8080):
    """Open the browser to the app URL, preferring Chrome on macOS."""
    url = f'http://localhost:{port}'

    # Try to open Chrome on macOS
    if platform.system() == 'Darwin':
        try:
            subprocess.run(['open', '-a', 'Google Chrome', url], check=True)
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Chrome not found, fall back to default browser
            pass

    # Fall back to default browser
    webbrowser.open(url)


def main():
    """Main entry point."""
    global IMAGE_DIR, IMAGE_FILES, ANNOTATION_FILE

    parser = argparse.ArgumentParser(
        description='Annotate college table images with rotation and column names'
    )
    parser.add_argument(
        '--input-dir',
        required=True,
        help='Directory containing PNG images of college tables'
    )
    parser.add_argument(
        '--output-file',
        default='college_table_annotations.json',
        help='Output JSON file for annotations (default: college_table_annotations.json)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port for web server (default: 8080)'
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not automatically open browser'
    )

    args = parser.parse_args()

    # Set global variables
    IMAGE_DIR = Path(args.input_dir)
    ANNOTATION_FILE = Path(args.output_file)

    # Load images
    try:
        IMAGE_FILES = get_image_files(IMAGE_DIR)
        print(f"Found {len(IMAGE_FILES)} PNG images in {IMAGE_DIR}")
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    # Load existing annotations
    load_annotations()
    print(f"Loaded {len(annotations)} existing annotations from {ANNOTATION_FILE}")

    # Start web server
    print(f"\nStarting annotation tool on http://localhost:{args.port}")
    print("Press Ctrl+C to stop the server and save annotations\n")

    # Open browser after a short delay
    if not args.no_browser:
        Timer(1.5, lambda: open_browser(args.port)).start()

    try:
        app.run(host='localhost', port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        save_annotations()
        print(f"Annotations saved to {ANNOTATION_FILE}")
        print(f"Total annotated: {len(annotations)}/{len(IMAGE_FILES)}")

    return 0


if __name__ == '__main__':
    exit(main())
