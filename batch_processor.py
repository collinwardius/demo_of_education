#!/usr/bin/env python3
"""
Batch Document Processor for Historical Education Data
Processes multiple documents through the complete Textract -> Clean -> Review pipeline
"""

import argparse
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import subprocess
import sys
import time

from simple_textract import SimpleTextractExtractor
from data_cleaner import HistoricalDataCleaner
from review_interface import ReviewInterfaceGenerator

class BatchProcessor:
    def __init__(self, output_dir: str = "batch_results", aws_region: str = "us-east-1"):
        """Initialize batch processor."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.textract_extractor = SimpleTextractExtractor(aws_region)
        self.data_cleaner = HistoricalDataCleaner()
        self.review_generator = ReviewInterfaceGenerator()
        
        # Setup logging
        self.setup_logging()
        
        # Track processing statistics
        self.stats = {
            'total_documents': 0,
            'successful_extractions': 0,
            'successful_cleanings': 0,
            'total_tables_found': 0,
            'total_rows_extracted': 0,
            'total_rows_needing_review': 0,
            'processing_start_time': None,
            'processing_end_time': None,
            'errors': []
        }
    
    def setup_logging(self):
        """Setup logging for batch processing."""
        log_file = self.output_dir / "batch_processing.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def process_directory(self, input_dir: str, file_patterns: List[str] = None) -> Dict:
        """
        Process all documents in a directory.
        
        Args:
            input_dir: Directory containing documents to process
            file_patterns: List of file patterns to match (default: common image/PDF formats)
            
        Returns:
            Summary statistics and results
        """
        if file_patterns is None:
            file_patterns = ['*.pdf', '*.png', '*.jpg', '*.jpeg', '*.tiff']
        
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        # Find all matching files
        files_to_process = []
        for pattern in file_patterns:
            files_to_process.extend(input_path.glob(pattern))
            files_to_process.extend(input_path.glob(pattern.upper()))
        
        if not files_to_process:
            self.logger.warning(f"No files found matching patterns {file_patterns} in {input_dir}")
            return self.stats
        
        self.logger.info(f"Found {len(files_to_process)} files to process")
        self.stats['total_documents'] = len(files_to_process)
        self.stats['processing_start_time'] = datetime.now().isoformat()
        
        # Process each file
        results = []
        for i, file_path in enumerate(files_to_process, 1):
            self.logger.info(f"Processing file {i}/{len(files_to_process)}: {file_path.name}")
            
            try:
                result = self.process_single_document(str(file_path))
                results.append(result)
                
                if result['extraction_successful']:
                    self.stats['successful_extractions'] += 1
                if result['cleaning_successful']:
                    self.stats['successful_cleanings'] += 1
                
                self.stats['total_tables_found'] += result['tables_found']
                self.stats['total_rows_extracted'] += result['rows_extracted']
                self.stats['total_rows_needing_review'] += result['rows_needing_review']
                
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                self.stats['errors'].append({
                    'file': str(file_path),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        self.stats['processing_end_time'] = datetime.now().isoformat()
        
        # Generate summary reports
        self._generate_batch_summary(results)
        
        self.logger.info("Batch processing complete!")
        return self.stats
    
    def process_single_document(self, file_path: str) -> Dict:
        """
        Process a single document through the complete pipeline.
        
        Returns:
            Dictionary with processing results and statistics
        """
        file_path = Path(file_path)
        base_name = file_path.stem
        
        result = {
            'file_path': str(file_path),
            'base_name': base_name,
            'extraction_successful': False,
            'cleaning_successful': False,
            'review_interface_created': False,
            'tables_found': 0,
            'rows_extracted': 0,
            'rows_needing_review': 0,
            'confidence_average': 0.0,
            'output_files': [],
            'processing_time': 0.0,
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Extract with Textract
            self.logger.info(f"  Step 1: Extracting data with Textract...")
            
            # Create subdirectory for this document
            doc_output_dir = self.output_dir / base_name
            doc_output_dir.mkdir(exist_ok=True)
            
            # Extract data
            textract_response = self.textract_extractor.extract_from_file(str(file_path))
            self.textract_extractor.save_results(str(file_path), textract_response, str(doc_output_dir))
            
            result['extraction_successful'] = True
            
            # Find the extracted table CSV
            table_csv = None
            for output_file in doc_output_dir.glob("*table*.csv"):
                if "with_headers" in output_file.name:
                    table_csv = output_file
                    break
            
            if not table_csv:
                table_csv = next(doc_output_dir.glob("*table*.csv"), None)
            
            if not table_csv:
                self.logger.warning(f"  No table CSV found for {base_name}")
                return result
            
            result['output_files'].append(str(table_csv))
            
            # Count tables and rows
            tables = self.textract_extractor.extract_tables_simple(textract_response)
            result['tables_found'] = len(tables)
            
            if tables:
                result['rows_extracted'] = sum(len(table) for table in tables if table)
            
            # Step 2: Clean and validate data
            self.logger.info(f"  Step 2: Cleaning and validating data...")
            
            df = pd.read_csv(table_csv)
            cleaned_df = self.data_cleaner.clean_dataframe(df, base_name)
            
            # Save cleaned data
            cleaned_csv = doc_output_dir / f"{base_name}_cleaned.csv"
            cleaned_df.to_csv(cleaned_csv, index=False)
            result['output_files'].append(str(cleaned_csv))
            
            # Generate validation report
            validation_report_path = doc_output_dir / f"{base_name}_validation_report.json"
            validation_report = self.data_cleaner.generate_validation_report(cleaned_df, str(validation_report_path))
            result['output_files'].append(str(validation_report_path))
            
            # Update statistics
            result['cleaning_successful'] = True
            result['rows_needing_review'] = validation_report['summary']['needs_review']
            result['confidence_average'] = validation_report['summary']['average_confidence']
            
            # Export for review
            review_csv = doc_output_dir / f"{base_name}_for_review.csv"
            self.data_cleaner.export_for_review(cleaned_df, str(review_csv))
            result['output_files'].append(str(review_csv))
            
            # Step 3: Generate review interface
            self.logger.info(f"  Step 3: Generating review interface...")
            
            interface_path = doc_output_dir / f"{base_name}_review_interface.html"
            self.review_generator.generate_review_interface(
                str(cleaned_csv),
                str(validation_report_path),
                str(interface_path),
                str(file_path)  # Original image for reference
            )
            
            result['review_interface_created'] = True
            result['output_files'].append(str(interface_path))
            
            self.logger.info(f"  ✅ Successfully processed {base_name}")
            
        except Exception as e:
            result['errors'].append(str(e))
            self.logger.error(f"  ❌ Error processing {base_name}: {e}")
        
        finally:
            result['processing_time'] = time.time() - start_time
        
        return result
    
    def _generate_batch_summary(self, results: List[Dict]):
        """Generate comprehensive summary reports for the batch."""
        
        # Create main summary report
        summary_report = {
            'batch_statistics': self.stats,
            'individual_results': results,
            'recommendations': self._generate_recommendations(results)
        }
        
        summary_path = self.output_dir / "batch_processing_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary_report, f, indent=2, default=str)
        
        # Create CSV summary for easy analysis
        df_results = pd.DataFrame(results)
        csv_summary_path = self.output_dir / "batch_results_summary.csv"
        df_results.to_csv(csv_summary_path, index=False)
        
        # Create priority review list
        priority_files = [
            r for r in results 
            if r['cleaning_successful'] and r['rows_needing_review'] > 0
        ]
        priority_files.sort(key=lambda x: x['rows_needing_review'], reverse=True)
        
        priority_df = pd.DataFrame(priority_files)
        if not priority_df.empty:
            priority_csv = self.output_dir / "priority_review_list.csv"
            priority_df[['base_name', 'rows_needing_review', 'confidence_average', 
                        'tables_found', 'rows_extracted']].to_csv(priority_csv, index=False)
        
        # Create master review interface index
        self._create_master_index(results)
        
        self.logger.info(f"Summary reports saved to {self.output_dir}")
    
    def _generate_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations based on batch processing results."""
        recommendations = []
        
        successful_extractions = len([r for r in results if r['extraction_successful']])
        total_files = len(results)
        
        if successful_extractions < total_files * 0.8:
            recommendations.append("Consider preprocessing images for better OCR quality - contrast adjustment, noise reduction")
        
        high_review_rate = sum(r['rows_needing_review'] for r in results) / max(sum(r['rows_extracted'] for r in results), 1)
        if high_review_rate > 0.2:
            recommendations.append("High percentage of rows need review - consider tuning validation thresholds")
        
        avg_confidence = sum(r['confidence_average'] for r in results if r['cleaning_successful']) / max(len([r for r in results if r['cleaning_successful']]), 1)
        if avg_confidence < 0.85:
            recommendations.append("Low average confidence - may need manual preprocessing or different extraction approach")
        
        files_with_no_tables = len([r for r in results if r['tables_found'] == 0])
        if files_with_no_tables > 0:
            recommendations.append(f"{files_with_no_tables} files had no tables detected - verify document quality and content")
        
        return recommendations
    
    def _create_master_index(self, results: List[Dict]):
        """Create a master HTML index of all review interfaces."""
        
        successful_results = [r for r in results if r['review_interface_created']]
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Batch Processing Results - Master Index</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .stats {{ background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .file-list {{ border-collapse: collapse; width: 100%; }}
                .file-list th, .file-list td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .file-list th {{ background-color: #f2f2f2; }}
                .high-priority {{ background-color: #ffebee; }}
                .medium-priority {{ background-color: #fff3e0; }}
                .btn {{ padding: 8px 16px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }}
                .btn:hover {{ background: #1976d2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Batch Processing Results</h1>
                
                <div class="stats">
                    <h3>Summary Statistics</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                        <div><strong>Total Documents:</strong> {self.stats['total_documents']}</div>
                        <div><strong>Successful Extractions:</strong> {self.stats['successful_extractions']}</div>
                        <div><strong>Total Tables Found:</strong> {self.stats['total_tables_found']}</div>
                        <div><strong>Total Rows Extracted:</strong> {self.stats['total_rows_extracted']}</div>
                        <div><strong>Rows Needing Review:</strong> {self.stats['total_rows_needing_review']}</div>
                    </div>
                </div>
                
                <h3>📋 Review Interfaces</h3>
                <table class="file-list">
                    <thead>
                        <tr>
                            <th>Document</th>
                            <th>Tables Found</th>
                            <th>Rows Extracted</th>
                            <th>Rows Need Review</th>
                            <th>Avg Confidence</th>
                            <th>Review Interface</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for result in successful_results:
            # Find the review interface file
            interface_file = None
            for output_file in result['output_files']:
                if 'review_interface.html' in output_file:
                    interface_file = Path(output_file).relative_to(self.output_dir)
                    break
            
            # Determine priority class
            priority_class = ""
            if result['rows_needing_review'] > result['rows_extracted'] * 0.2:
                priority_class = "high-priority"
            elif result['rows_needing_review'] > 0:
                priority_class = "medium-priority"
            
            confidence_pct = f"{result['confidence_average']:.1%}" if result['confidence_average'] else "N/A"
            
            html_content += f"""
                        <tr class="{priority_class}">
                            <td>{result['base_name']}</td>
                            <td>{result['tables_found']}</td>
                            <td>{result['rows_extracted']}</td>
                            <td>{result['rows_needing_review']}</td>
                            <td>{confidence_pct}</td>
                            <td><a href="{interface_file}" class="btn" target="_blank">Open Review</a></td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-radius: 4px;">
                    <h4>🎯 Next Steps</h4>
                    <ol>
                        <li><strong>Priority Review:</strong> Start with red-highlighted files (highest review percentage)</li>
                        <li><strong>Use Review Interfaces:</strong> Click "Open Review" to access individual document review pages</li>
                        <li><strong>Save Changes:</strong> Use the save functionality in each review interface to track corrections</li>
                        <li><strong>Export Data:</strong> Download corrected CSV files when review is complete</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
        
        master_index_path = self.output_dir / "index.html"
        with open(master_index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Master index created: {master_index_path}")

def main():
    parser = argparse.ArgumentParser(description='Batch process historical education documents')
    parser.add_argument('input_dir', help='Directory containing documents to process')
    parser.add_argument('--output-dir', '-o', default='batch_results', 
                       help='Output directory for results (default: batch_results)')
    parser.add_argument('--file-patterns', nargs='+', 
                       default=['*.pdf', '*.png', '*.jpg', '*.jpeg', '*.tiff'],
                       help='File patterns to match (default: common image/PDF formats)')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    # Initialize batch processor
    processor = BatchProcessor(output_dir=args.output_dir, aws_region=args.region)
    
    try:
        print(f"🚀 Starting batch processing...")
        print(f"   Input directory: {args.input_dir}")
        print(f"   Output directory: {args.output_dir}")
        print(f"   File patterns: {args.file_patterns}")
        
        # Process all documents
        stats = processor.process_directory(args.input_dir, args.file_patterns)
        
        # Print final summary
        print(f"\n✅ Batch processing complete!")
        print(f"   📊 Processed: {stats['successful_extractions']}/{stats['total_documents']} documents")
        print(f"   📋 Found: {stats['total_tables_found']} tables, {stats['total_rows_extracted']} rows")
        print(f"   🔍 Need review: {stats['total_rows_needing_review']} rows")
        print(f"   🌐 Open: {args.output_dir}/index.html to start reviewing")
        
        if stats['errors']:
            print(f"   ⚠️  {len(stats['errors'])} files had errors - check batch_processing.log")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())