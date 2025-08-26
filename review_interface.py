#!/usr/bin/env python3
"""
Research Assistant Review Interface Generator
Creates an HTML interface for reviewing and correcting Textract data
"""

import pandas as pd
import json
from pathlib import Path
import argparse
from datetime import datetime
import base64

class ReviewInterfaceGenerator:
    def __init__(self):
        """Initialize the review interface generator."""
        self.template_css = """
        <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header {
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .summary-stats {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            border-left: 4px solid #2196f3;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }
        
        .stat-box {
            background: white;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
            border: 1px solid #ddd;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2196f3;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 12px;
        }
        
        .data-table th {
            background-color: #f0f0f0;
            padding: 8px;
            border: 1px solid #ddd;
            text-align: left;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .data-table td {
            padding: 6px 8px;
            border: 1px solid #ddd;
            vertical-align: top;
        }
        
        .needs-review {
            background-color: #ffebee !important;
        }
        
        .low-confidence {
            background-color: #fff3e0 !important;
        }
        
        .validation-cell {
            max-width: 200px;
            word-wrap: break-word;
            font-size: 10px;
        }
        
        .confidence-score {
            font-weight: bold;
            text-align: center;
        }
        
        .confidence-high { color: #4caf50; }
        .confidence-medium { color: #ff9800; }
        .confidence-low { color: #f44336; }
        
        .editable {
            background-color: #fff;
            border: 1px solid #ddd;
            padding: 2px 4px;
            min-width: 60px;
            font-family: inherit;
            font-size: inherit;
        }
        
        .editable:focus {
            outline: 2px solid #2196f3;
            background-color: #e3f2fd;
        }
        
        .save-btn {
            background-color: #4caf50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 20px 5px;
        }
        
        .save-btn:hover {
            background-color: #45a049;
        }
        
        .export-btn {
            background-color: #2196f3;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 20px 5px;
        }
        
        .instructions {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            border-left: 4px solid #ff9800;
        }
        
        .legend {
            margin: 20px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 4px;
        }
        
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
        }
        
        .filter-controls {
            margin: 20px 0;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 4px;
        }
        
        .filter-btn {
            margin: 5px;
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background-color: #e0e0e0;
        }
        
        .filter-btn.active {
            background-color: #2196f3;
            color: white;
        }
        
        @media print {
            .save-btn, .export-btn, .filter-controls { display: none; }
            body { margin: 0; }
        }
        </style>
        """
    
    def generate_review_interface(self, csv_file: str, validation_report_file: str, 
                                  output_path: str, original_image_path: str = None):
        """Generate HTML review interface from cleaned data and validation report."""
        
        # Load data
        df = pd.read_csv(csv_file)
        
        with open(validation_report_file, 'r') as f:
            validation_report = json.load(f)
        
        # Generate HTML
        html_content = self._create_html_content(df, validation_report, original_image_path)
        
        # Save HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Review interface created: {output_path}")
        return output_path
    
    def _create_html_content(self, df: pd.DataFrame, validation_report: dict, 
                             original_image_path: str = None) -> str:
        """Create the complete HTML content for the review interface."""
        
        summary = validation_report['summary']
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Data Review Interface - {validation_report.get('source_document', 'Historical Education Data')}</title>
            {self.template_css}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Historical Education Data Review</h1>
                    <p><strong>Document:</strong> {df.iloc[0]['_source_document'] if '_source_document' in df.columns else 'Unknown'}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="instructions">
                    <h3>📋 Instructions for Research Assistants</h3>
                    <ul>
                        <li><strong>Red rows</strong> need review (low confidence or validation flags)</li>
                        <li><strong>Yellow rows</strong> have medium confidence - check if time permits</li>
                        <li><strong>Click on any cell</strong> to edit the data directly</li>
                        <li><strong>Save frequently</strong> using the Save button</li>
                        <li><strong>Pay special attention to:</strong> Number formatting, state names, missing data</li>
                        <li><strong>Common issues:</strong> OCR errors (O→0, l→1), decimal points in large numbers</li>
                    </ul>
                </div>
                
                <div class="summary-stats">
                    <h3>📊 Data Quality Summary</h3>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-value">{summary['total_rows']}</div>
                            <div>Total Rows</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{summary['needs_review']}</div>
                            <div>Need Review</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{summary['review_percentage']}%</div>
                            <div>Review Rate</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value">{summary['average_confidence']:.1%}</div>
                            <div>Avg Confidence</div>
                        </div>
                    </div>
                </div>
                
                <div class="legend">
                    <strong>Legend:</strong>
                    <span class="legend-item needs-review">High Priority Review</span>
                    <span class="legend-item low-confidence">Medium Priority Review</span>
                    <span class="legend-item" style="background-color: white;">Clean Data</span>
                </div>
                
                <div class="filter-controls">
                    <strong>View:</strong>
                    <button class="filter-btn active" onclick="filterRows('all')">All Rows</button>
                    <button class="filter-btn" onclick="filterRows('review')">Needs Review Only</button>
                    <button class="filter-btn" onclick="filterRows('clean')">Clean Data Only</button>
                    <button class="filter-btn" onclick="filterRows('flagged')">Flagged Only</button>
                </div>
                
                {self._generate_original_image_section(original_image_path)}
                
                <div style="overflow-x: auto;">
                    {self._generate_data_table(df)}
                </div>
                
                <div style="margin-top: 30px;">
                    <button class="save-btn" onclick="saveData()">💾 Save Changes</button>
                    <button class="export-btn" onclick="exportData()">📤 Export CSV</button>
                    <button class="export-btn" onclick="window.print()">🖨️ Print</button>
                </div>
                
                <div id="save-status" style="margin-top: 10px; padding: 10px; display: none;"></div>
            </div>
            
            {self._generate_javascript()}
        </body>
        </html>
        """
        
        return html
    
    def _generate_original_image_section(self, image_path: str) -> str:
        """Generate section showing original document image if available."""
        if not image_path or not Path(image_path).exists():
            return ""
        
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            return f"""
            <div style="margin: 20px 0; text-align: center;">
                <h3>📄 Original Document</h3>
                <img src="data:image/png;base64,{image_data}" 
                     style="max-width: 100%; max-height: 600px; border: 1px solid #ddd; border-radius: 4px;"
                     alt="Original document">
            </div>
            """
        except Exception as e:
            return f'<div style="color: #666; font-style: italic;">Original document image not available ({e})</div>'
    
    def _generate_data_table(self, df: pd.DataFrame) -> str:
        """Generate the main data table HTML."""
        
        # Identify metadata columns
        data_cols = [col for col in df.columns if not col.startswith('_')]
        meta_cols = [col for col in df.columns if col.startswith('_')]
        
        # Reorder: key meta columns first, then data, then other meta
        key_meta = ['_needs_review', '_confidence_score', '_validation_flags']
        other_meta = [col for col in meta_cols if col not in key_meta]
        
        ordered_cols = key_meta + data_cols + other_meta
        ordered_cols = [col for col in ordered_cols if col in df.columns]
        
        # Generate table header
        table_html = '<table class="data-table" id="dataTable">\n<thead><tr>\n'
        for col in ordered_cols:
            display_name = col.replace('_', ' ').title() if col.startswith('_') else col.title()
            table_html += f'<th>{display_name}</th>\n'
        table_html += '</tr></thead>\n<tbody>\n'
        
        # Generate table rows
        for idx, row in df.iterrows():
            needs_review = row.get('_needs_review', False)
            confidence = row.get('_confidence_score', 1.0)
            
            # Determine row class
            row_class = ""
            if needs_review:
                row_class = "needs-review"
            elif confidence < 0.9:
                row_class = "low-confidence"
            
            table_html += f'<tr class="{row_class}" data-needs-review="{needs_review}" data-confidence="{confidence}">\n'
            
            for col in ordered_cols:
                value = str(row[col]) if pd.notna(row[col]) else ""
                cell_class = ""
                
                # Special formatting for specific columns
                if col == '_confidence_score':
                    cell_class = "confidence-score "
                    if confidence >= 0.9:
                        cell_class += "confidence-high"
                    elif confidence >= 0.7:
                        cell_class += "confidence-medium"
                    else:
                        cell_class += "confidence-low"
                    value = f"{confidence:.1%}"
                elif col == '_validation_flags':
                    cell_class = "validation-cell"
                elif col.startswith('_'):
                    cell_class = "meta-cell"
                else:
                    # Data cells are editable
                    table_html += f'<td><input type="text" class="editable" value="{value}" data-row="{idx}" data-col="{col}"></td>\n'
                    continue
                
                table_html += f'<td class="{cell_class}">{value}</td>\n'
            
            table_html += '</tr>\n'
        
        table_html += '</tbody>\n</table>\n'
        
        return table_html
    
    def _generate_javascript(self) -> str:
        """Generate JavaScript for interactivity."""
        return """
        <script>
        let changedCells = {};
        
        // Track changes to editable cells
        document.addEventListener('DOMContentLoaded', function() {
            const editableCells = document.querySelectorAll('.editable');
            editableCells.forEach(cell => {
                cell.addEventListener('input', function() {
                    const row = this.dataset.row;
                    const col = this.dataset.col;
                    const key = row + '_' + col;
                    changedCells[key] = {
                        row: parseInt(row),
                        column: col,
                        oldValue: this.defaultValue,
                        newValue: this.value
                    };
                    
                    // Highlight changed cells
                    this.style.backgroundColor = '#e8f5e8';
                    this.style.borderColor = '#4caf50';
                });
            });
        });
        
        // Filter rows based on review status
        function filterRows(filter) {
            const table = document.getElementById('dataTable');
            const rows = table.querySelectorAll('tbody tr');
            
            // Update button states
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            rows.forEach(row => {
                const needsReview = row.dataset.needsReview === 'true';
                const confidence = parseFloat(row.dataset.confidence);
                const hasFlags = row.querySelector('.validation-cell').textContent.trim() !== '';
                
                let show = false;
                switch(filter) {
                    case 'all':
                        show = true;
                        break;
                    case 'review':
                        show = needsReview;
                        break;
                    case 'clean':
                        show = !needsReview && confidence >= 0.9;
                        break;
                    case 'flagged':
                        show = hasFlags;
                        break;
                }
                
                row.style.display = show ? '' : 'none';
            });
        }
        
        // Save changes
        function saveData() {
            const statusDiv = document.getElementById('save-status');
            
            if (Object.keys(changedCells).length === 0) {
                statusDiv.innerHTML = '<div style="color: #ff9800;">No changes to save.</div>';
                statusDiv.style.display = 'block';
                setTimeout(() => statusDiv.style.display = 'none', 3000);
                return;
            }
            
            // Create CSV data
            const changes = Object.values(changedCells);
            const csvData = 'Row,Column,Old Value,New Value,Timestamp\\n' + 
                          changes.map(c => `${c.row},"${c.column}","${c.oldValue}","${c.newValue}","${new Date().toISOString()}"`).join('\\n');
            
            // Save to localStorage
            const saveKey = 'textract_review_' + new Date().getTime();
            localStorage.setItem(saveKey, csvData);
            
            // Download changes file
            const blob = new Blob([csvData], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'review_changes_' + new Date().toISOString().split('T')[0] + '.csv';
            a.click();
            window.URL.revokeObjectURL(url);
            
            statusDiv.innerHTML = '<div style="color: #4caf50;">✅ Changes saved! Download started.</div>';
            statusDiv.style.display = 'block';
            setTimeout(() => statusDiv.style.display = 'none', 5000);
            
            // Reset changed cells tracking
            changedCells = {};
            document.querySelectorAll('.editable').forEach(cell => {
                cell.style.backgroundColor = '';
                cell.style.borderColor = '';
                cell.defaultValue = cell.value;
            });
        }
        
        // Export current data as CSV
        function exportData() {
            const table = document.getElementById('dataTable');
            const rows = Array.from(table.querySelectorAll('tr'));
            
            let csvContent = '';
            
            // Header row
            const headers = Array.from(rows[0].querySelectorAll('th')).map(th => th.textContent);
            csvContent += headers.map(h => `"${h}"`).join(',') + '\\n';
            
            // Data rows
            rows.slice(1).forEach(row => {
                const cells = Array.from(row.querySelectorAll('td'));
                const rowData = cells.map(cell => {
                    const input = cell.querySelector('.editable');
                    const value = input ? input.value : cell.textContent;
                    return `"${value.replace(/"/g, '""')}"`;
                });
                csvContent += rowData.join(',') + '\\n';
            });
            
            // Download CSV
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'reviewed_data_' + new Date().toISOString().split('T')[0] + '.csv';
            a.click();
            window.URL.revokeObjectURL(url);
            
            const statusDiv = document.getElementById('save-status');
            statusDiv.innerHTML = '<div style="color: #2196f3;">📤 Data exported successfully!</div>';
            statusDiv.style.display = 'block';
            setTimeout(() => statusDiv.style.display = 'none', 3000);
        }
        </script>
        """

def main():
    parser = argparse.ArgumentParser(description='Generate HTML review interface for Textract data')
    parser.add_argument('cleaned_csv', help='Path to cleaned CSV file')
    parser.add_argument('validation_report', help='Path to validation report JSON')
    parser.add_argument('--output', '-o', help='Output HTML file path')
    parser.add_argument('--original-image', help='Path to original document image')
    
    args = parser.parse_args()
    
    # Generate output path if not provided
    if not args.output:
        base_name = Path(args.cleaned_csv).stem
        output_dir = Path(args.cleaned_csv).parent
        args.output = output_dir / f"{base_name}_review_interface.html"
    
    # Generate review interface
    generator = ReviewInterfaceGenerator()
    generator.generate_review_interface(
        args.cleaned_csv,
        args.validation_report, 
        args.output,
        args.original_image
    )
    
    print(f"✅ Review interface ready!")
    print(f"   Open in browser: {args.output}")
    print(f"   📋 Research assistants can now review and correct the data")

if __name__ == "__main__":
    main()