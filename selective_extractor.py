#!/usr/bin/env python3
"""
Selective Page Extractor
Extracts only high-priority pages using the existing Textract pipeline
"""

import fitz  # PyMuPDF
import json
import pandas as pd
from pathlib import Path
import logging
import argparse
from typing import Dict, List
import tempfile
import os
from datetime import datetime

from simple_textract import SimpleTextractExtractor
from data_cleaner import HistoricalDataCleaner
from review_interface import ReviewInterfaceGenerator

class SelectivePageExtractor:
    def __init__(self, aws_region: str = "us-east-1", output_dir: str = "selective_extractions"):
        """Initialize selective page extractor."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize existing pipeline components
        self.textract_extractor = SimpleTextractExtractor(aws_region)
        self.data_cleaner = HistoricalDataCleaner()
        self.review_generator = ReviewInterfaceGenerator()
        
        # Setup logging
        log_file = self.output_dir / "selective_extraction.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Track extraction statistics
        self.stats = {
            'total_pages_to_extract': 0,
            'successful_extractions': 0,
            'tables_extracted': 0,
            'rows_extracted': 0,
            'extraction_start_time': None,
            'extraction_end_time': None,
            'errors': []
        }
    
    def extract_from_filtered_results(self, filtered_results: Dict, 
                                    min_score: float = 0.6,
                                    max_pages: int = 10) -> Dict:
        """
        Extract data from filtered page results.
        
        Args:
            filtered_results: Results from table filter
            min_score: Minimum score for page extraction
            max_pages: Maximum pages to extract
            
        Returns:
            Extraction results with statistics
        """
        pdf_path = Path(filtered_results['pdf_path'])
        pdf_name = pdf_path.stem
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.logger.info(f"Starting selective extraction from: {pdf_name}")
        
        # Filter pages by score
        eligible_pages = [
            p for p in filtered_results['pages_with_tables'] 
            if p['education_score'] >= min_score
        ]
        
        # Limit number of pages
        if max_pages:
            eligible_pages = eligible_pages[:max_pages]
        
        self.stats['total_pages_to_extract'] = len(eligible_pages)
        self.stats['extraction_start_time'] = datetime.now().isoformat()
        
        if not eligible_pages:
            self.logger.warning("No pages meet the extraction criteria")
            return self._create_extraction_summary(pdf_name, [])
        
        self.logger.info(f"Extracting {len(eligible_pages)} pages with scores >= {min_score}")
        
        # Extract each page
        extraction_results = []
        for page_info in eligible_pages:
            try:
                result = self._extract_single_page(pdf_path, page_info, pdf_name)
                extraction_results.append(result)
                
                if result['extraction_successful']:
                    self.stats['successful_extractions'] += 1
                    self.stats['tables_extracted'] += result['tables_found']
                    self.stats['rows_extracted'] += result['rows_extracted']
                
            except Exception as e:
                self.logger.error(f"Error extracting page {page_info['page_number']}: {e}")
                self.stats['errors'].append({
                    'page': page_info['page_number'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        self.stats['extraction_end_time'] = datetime.now().isoformat()
        
        # Create comprehensive results
        final_results = self._create_extraction_summary(pdf_name, extraction_results)
        final_results['source_filter_results'] = filtered_results
        
        # Save results
        self._save_extraction_results(final_results, pdf_name)
        
        self.logger.info(f"Selective extraction complete: {self.stats['successful_extractions']}/{len(eligible_pages)} pages")
        
        return final_results
    
    def _extract_single_page(self, pdf_path: Path, page_info: Dict, pdf_name: str) -> Dict:
        """Extract data from a single page."""
        page_num = page_info['page_number'] - 1  # Convert to 0-based
        
        result = {
            'page_number': page_info['page_number'],
            'education_score': page_info['education_score'],
            'extraction_successful': False,
            'cleaning_successful': False,
            'tables_found': 0,
            'rows_extracted': 0,
            'output_files': [],
            'confidence_scores': [],
            'processing_errors': []
        }
        
        self.logger.info(f"  Processing page {page_info['page_number']} (score: {page_info['education_score']:.2f})")
        
        try:
            # Create temporary file for single page
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Extract page as image
                self._extract_page_as_image(pdf_path, page_num, temp_path)
                
                # Create output directory for this page
                page_output_dir = self.output_dir / pdf_name / f"page_{page_info['page_number']}"
                page_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Run Textract extraction
                textract_response = self.textract_extractor.extract_from_file(temp_path)
                self.textract_extractor.save_results(temp_path, textract_response, str(page_output_dir))
                
                result['extraction_successful'] = True
                
                # Find extracted table files
                table_files = list(page_output_dir.glob("*table*.csv"))
                if table_files:
                    result['tables_found'] = len(table_files)
                    
                    # Process each table through the cleaning pipeline
                    for table_file in table_files:
                        try:
                            # Clean and validate data
                            df = pd.read_csv(table_file)
                            if not df.empty:
                                cleaned_df = self.data_cleaner.clean_dataframe(df, f"{pdf_name}_page_{page_info['page_number']}")
                                
                                # Save cleaned data
                                cleaned_file = page_output_dir / f"{table_file.stem}_cleaned.csv"
                                cleaned_df.to_csv(cleaned_file, index=False)
                                result['output_files'].append(str(cleaned_file))
                                
                                # Generate validation report
                                validation_file = page_output_dir / f"{table_file.stem}_validation.json"
                                validation_report = self.data_cleaner.generate_validation_report(
                                    cleaned_df, str(validation_file)
                                )
                                result['output_files'].append(str(validation_file))
                                
                                # Export for review
                                review_file = page_output_dir / f"{table_file.stem}_for_review.csv"
                                self.data_cleaner.export_for_review(cleaned_df, str(review_file))
                                result['output_files'].append(str(review_file))
                                
                                # Update statistics
                                result['rows_extracted'] += len(cleaned_df)
                                if 'summary' in validation_report:
                                    result['confidence_scores'].append(validation_report['summary'].get('average_confidence', 0.0))
                                
                                result['cleaning_successful'] = True
                                
                        except Exception as e:
                            self.logger.warning(f"    Error cleaning table {table_file.name}: {e}")
                            result['processing_errors'].append(f"Table cleaning: {str(e)}")
                    
                    # Create page-level review interface
                    if result['cleaning_successful']:
                        try:
                            interface_file = page_output_dir / f"page_{page_info['page_number']}_review.html"
                            
                            # Use the first cleaned file for the interface
                            cleaned_files = [f for f in result['output_files'] if '_cleaned.csv' in f]
                            validation_files = [f for f in result['output_files'] if '_validation.json' in f]
                            
                            if cleaned_files and validation_files:
                                self.review_generator.generate_review_interface(
                                    cleaned_files[0],
                                    validation_files[0],
                                    str(interface_file),
                                    temp_path  # Original page image
                                )
                                result['output_files'].append(str(interface_file))
                        
                        except Exception as e:
                            self.logger.warning(f"    Error creating review interface: {e}")
                            result['processing_errors'].append(f"Review interface: {str(e)}")
                
                else:
                    self.logger.warning(f"    No tables found in Textract results for page {page_info['page_number']}")
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        except Exception as e:
            result['processing_errors'].append(str(e))
            raise
        
        return result
    
    def _extract_page_as_image(self, pdf_path: Path, page_num: int, output_path: str):
        """Extract a single page from PDF as high-quality image."""
        doc = fitz.open(str(pdf_path))
        try:
            page = doc[page_num]
            
            # Use high resolution for better OCR
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for high quality
            pix = page.get_pixmap(matrix=mat)
            pix.save(output_path)
            
        finally:
            doc.close()
    
    def _create_extraction_summary(self, pdf_name: str, extraction_results: List[Dict]) -> Dict:
        """Create comprehensive extraction summary."""
        
        summary = {
            'pdf_name': pdf_name,
            'extraction_timestamp': datetime.now().isoformat(),
            'statistics': self.stats.copy(),
            'page_results': extraction_results,
            'summary_metrics': {
                'success_rate': 0.0,
                'total_tables': 0,
                'total_rows': 0,
                'pages_with_data': 0,
                'average_confidence': 0.0
            }
        }
        
        if extraction_results:
            successful_pages = [r for r in extraction_results if r['extraction_successful']]
            pages_with_data = [r for r in extraction_results if r['rows_extracted'] > 0]
            
            summary['summary_metrics']['success_rate'] = len(successful_pages) / len(extraction_results)
            summary['summary_metrics']['total_tables'] = sum(r['tables_found'] for r in extraction_results)
            summary['summary_metrics']['total_rows'] = sum(r['rows_extracted'] for r in extraction_results)
            summary['summary_metrics']['pages_with_data'] = len(pages_with_data)
            
            # Calculate average confidence
            all_confidences = []
            for result in extraction_results:
                all_confidences.extend(result['confidence_scores'])
            
            if all_confidences:
                summary['summary_metrics']['average_confidence'] = sum(all_confidences) / len(all_confidences)
        
        return summary
    
    def _save_extraction_results(self, results: Dict, pdf_name: str):
        """Save comprehensive extraction results."""
        
        # Save main results as JSON
        json_file = self.output_dir / f"{pdf_name}_extraction_results.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Create CSV summary of page results
        if results['page_results']:
            csv_data = []
            for page in results['page_results']:
                csv_data.append({
                    'page_number': page['page_number'],
                    'education_score': page['education_score'],
                    'extraction_successful': page['extraction_successful'],
                    'tables_found': page['tables_found'],
                    'rows_extracted': page['rows_extracted'],
                    'avg_confidence': sum(page['confidence_scores']) / len(page['confidence_scores']) if page['confidence_scores'] else 0.0,
                    'output_files_count': len(page['output_files']),
                    'errors_count': len(page['processing_errors'])
                })
            
            csv_df = pd.DataFrame(csv_data)
            csv_file = self.output_dir / f"{pdf_name}_page_summary.csv"
            csv_df.to_csv(csv_file, index=False)
        
        # Create master index HTML
        self._create_extraction_index(results, pdf_name)
        
        self.logger.info(f"Results saved to {self.output_dir}")
    
    def _create_extraction_index(self, results: Dict, pdf_name: str):
        """Create HTML index of all extracted pages and their review interfaces."""
        
        successful_pages = [p for p in results['page_results'] if p['extraction_successful']]
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Selective Extraction Results - {pdf_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .stats {{ background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .page-list {{ border-collapse: collapse; width: 100%; }}
                .page-list th, .page-list td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .page-list th {{ background-color: #f2f2f2; }}
                .success {{ background-color: #d4edda; }}
                .warning {{ background-color: #fff3cd; }}
                .error {{ background-color: #f8d7da; }}
                .btn {{ padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 2px; }}
                .btn:hover {{ background: #0056b3; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Selective Extraction Results</h1>
                <h2>{pdf_name}</h2>
                
                <div class="stats">
                    <h3>Extraction Summary</h3>
                    <div class="metrics">
                        <div><strong>Pages Extracted:</strong> {len(results['page_results'])}</div>
                        <div><strong>Success Rate:</strong> {results['summary_metrics']['success_rate']:.1%}</div>
                        <div><strong>Total Tables:</strong> {results['summary_metrics']['total_tables']}</div>
                        <div><strong>Total Rows:</strong> {results['summary_metrics']['total_rows']}</div>
                        <div><strong>Average Confidence:</strong> {results['summary_metrics']['average_confidence']:.2f}</div>
                        <div><strong>Pages with Data:</strong> {results['summary_metrics']['pages_with_data']}</div>
                    </div>
                </div>
        """
        
        if successful_pages:
            html_content += """
                <h3>📋 Extracted Pages</h3>
                <table class="page-list">
                    <thead>
                        <tr>
                            <th>Page</th>
                            <th>Score</th>
                            <th>Status</th>
                            <th>Tables</th>
                            <th>Rows</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for page in results['page_results']:
                status_class = (
                    "success" if page['extraction_successful'] and page['rows_extracted'] > 0 else
                    "warning" if page['extraction_successful'] else
                    "error"
                )
                
                status_text = (
                    f"✅ {page['rows_extracted']} rows extracted" if page['rows_extracted'] > 0 else
                    "✅ Extracted (no data)" if page['extraction_successful'] else
                    "❌ Failed"
                )
                
                # Find review interface file
                review_link = ""
                for output_file in page['output_files']:
                    if '_review.html' in output_file:
                        rel_path = Path(output_file).relative_to(self.output_dir)
                        review_link = f'<a href="{rel_path}" class="btn" target="_blank">Review</a>'
                        break
                
                # Find CSV files
                csv_links = ""
                for output_file in page['output_files']:
                    if output_file.endswith('_cleaned.csv'):
                        rel_path = Path(output_file).relative_to(self.output_dir)
                        csv_links += f'<a href="{rel_path}" class="btn" download>CSV</a>'
                
                html_content += f"""
                        <tr class="{status_class}">
                            <td>Page {page['page_number']}</td>
                            <td>{page['education_score']:.2f}</td>
                            <td>{status_text}</td>
                            <td>{page['tables_found']}</td>
                            <td>{page['rows_extracted']}</td>
                            <td>{review_link} {csv_links}</td>
                        </tr>
                """
            
            html_content += """
                    </tbody>
                </table>
            """
        
        html_content += """
                <div style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-radius: 4px;">
                    <h4>📥 Next Steps</h4>
                    <ul>
                        <li><strong>Review Data:</strong> Click "Review" buttons to examine extracted data</li>
                        <li><strong>Download CSV:</strong> Use "CSV" buttons to download cleaned data</li>
                        <li><strong>Validate Results:</strong> Check the validation reports for data quality</li>
                        <li><strong>Combine Data:</strong> Merge multiple page extractions as needed</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        index_file = self.output_dir / f"{pdf_name}_extraction_index.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Extraction index created: {index_file}")


def main():
    parser = argparse.ArgumentParser(description='Extract data from filtered PDF pages')
    parser.add_argument('filtered_results', help='Path to filtered results JSON file')
    parser.add_argument('--min-score', type=float, default=0.6,
                       help='Minimum score for page extraction (default: 0.6)')
    parser.add_argument('--max-pages', type=int, default=10,
                       help='Maximum pages to extract (default: 10)')
    parser.add_argument('--output-dir', '-o', default='selective_extractions',
                       help='Output directory for extractions')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    # Load filtered results
    with open(args.filtered_results, 'r') as f:
        filtered_results = json.load(f)
    
    # Initialize extractor
    extractor = SelectivePageExtractor(
        aws_region=args.region, 
        output_dir=args.output_dir
    )
    
    try:
        print(f"🎯 Starting selective extraction...")
        print(f"   Min score: {args.min_score}")
        print(f"   Max pages: {args.max_pages}")
        
        # Run extraction
        results = extractor.extract_from_filtered_results(
            filtered_results,
            min_score=args.min_score,
            max_pages=args.max_pages
        )
        
        pdf_name = Path(filtered_results['pdf_path']).stem
        
        print(f"✅ Selective extraction complete!")
        print(f"   📊 Success rate: {results['summary_metrics']['success_rate']:.1%}")
        print(f"   📋 Tables extracted: {results['summary_metrics']['total_tables']}")
        print(f"   📝 Rows extracted: {results['summary_metrics']['total_rows']}")
        print(f"   🌐 View results: {args.output_dir}/{pdf_name}_extraction_index.html")
        
        if results['statistics']['errors']:
            print(f"   ⚠️  {len(results['statistics']['errors'])} pages had errors")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())