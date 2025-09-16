#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import argparse

# Import the modules directly
from pdf_to_s3_uploader import upload_pdf_to_s3
from s3_textract_async import S3TextractProcessor, ProcessType
from extract_table_raw import extract_raw_table_data, process_and_save_data

class TablePipelineProcessor:
    def __init__(self, aws_role_arn, s3_bucket, aws_region='us-east-2'):
        """
        Initialize the table processing pipeline
        
        Args:
            aws_role_arn (str): IAM role ARN for Textract to access S3 and SNS
            s3_bucket (str): S3 bucket for document storage
            aws_region (str): AWS region for processing
        """
        self.aws_role_arn = aws_role_arn
        self.s3_bucket = s3_bucket
        self.aws_region = aws_region
    
    def process_pdf_pipeline(self, pdf_file_path, page_ranges_str=None, output_csv_path=None, json_output_path=None):
        """
        Complete pipeline: PDF upload -> Textract analysis -> CSV extraction
        
        Args:
            pdf_file_path (str): Path to the PDF file to process
            page_ranges_str (str): Page ranges in format "1-3,4-6" (optional)
            output_csv_path (str): Output CSV file path (optional)
            json_output_path (str): Output JSON file path (optional)
        
        Returns:
            str: Path to the generated CSV file if successful, None otherwise
        """
        
        # Step 1: Upload PDF to S3
        print("=" * 60)
        print("STEP 1: UPLOADING PDF TO S3")
        print("=" * 60)
        
        pdf_name = Path(pdf_file_path).name
        s3_key = f"documents/{pdf_name}"
        
        upload_success = upload_pdf_to_s3(pdf_file_path, self.s3_bucket, s3_key)
        if not upload_success:
            print("❌ Failed to upload PDF to S3")
            return None
        
        # Step 2: Run Textract analysis
        print("\n" + "=" * 60)
        print("STEP 2: RUNNING TEXTRACT ANALYSIS")
        print("=" * 60)
        
        # Generate JSON output filename
        document_name = Path(pdf_file_path).stem
        if json_output_path:
            json_output = json_output_path
        else:
            json_output = f"{document_name}_textract_results.json"
        
        try:
            processor = S3TextractProcessor(self.aws_role_arn, self.s3_bucket, s3_key, self.aws_region)
            results = processor.process_document_complete_workflow(
                output_file=json_output,
                process_type=ProcessType.ANALYSIS,
                feature_types=['TABLES', 'FORMS']
            )
            
            if not results or results.get('job_status') != 'SUCCEEDED':
                print("❌ Textract analysis failed")
                return None
                
        except Exception as e:
            print(f"❌ Error during Textract analysis: {e}")
            return None
        
        # Step 3: Extract tables to CSV
        print("\n" + "=" * 60)
        print("STEP 3: EXTRACTING TABLES TO CSV")
        print("=" * 60)
        
        if not output_csv_path:
            output_csv_path = f"{document_name}_extracted_tables.csv"
        
        try:
            if page_ranges_str:
                # Parse page ranges
                page_ranges = []
                ranges_str = page_ranges_str.split(',')
                for range_str in ranges_str:
                    start, end = map(int, range_str.strip().split('-'))
                    page_ranges.append((start, end))
                
                print(f"Extracting page ranges: {page_ranges}")
                table_data_ranges = extract_raw_table_data(json_output, page_ranges=page_ranges)
                
                if isinstance(table_data_ranges, dict):
                    output_files = []
                    for range_name, range_data in table_data_ranges.items():
                        range_output = output_csv_path.replace('.csv', f'_{range_name}.csv')
                        output_file = process_and_save_data(range_data, range_output, range_name)
                        if output_file:
                            output_files.append(output_file)
                    
                    print(f"\n✅ Pipeline completed successfully!")
                    print(f"Generated {len(output_files)} CSV files:")
                    for file_path in output_files:
                        print(f"  📄 {file_path}")
                    return output_files[0] if output_files else None
            else:
                # Extract all pages as one document
                table_data = extract_raw_table_data(json_output)
                if isinstance(table_data, list):
                    output_file = process_and_save_data(table_data, output_csv_path)
                    if output_file:
                        print(f"\n✅ Pipeline completed successfully!")
                        print(f"📄 Generated CSV file: {output_file}")
                        return output_file
                        
        except Exception as e:
            print(f"❌ Error during CSV extraction: {e}")
            return None
        
        print("❌ Pipeline completed but no CSV files were generated")
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Complete PDF table extraction pipeline: PDF -> S3 -> Textract -> CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - process entire PDF
  python master_program.py document.pdf my-bucket arn:aws:iam::123:role/TextractRole

  # Extract specific page ranges
  python master_program.py document.pdf my-bucket arn:aws:iam::123:role/TextractRole --page-ranges "1-3,4-6"

  # Custom output file
  python master_program.py document.pdf my-bucket arn:aws:iam::123:role/TextractRole --output results.csv

Note: The IAM role must have permissions for:
  - s3:GetObject and s3:PutObject on your bucket
  - sns:CreateTopic, sns:DeleteTopic, sns:Publish
  - sqs:CreateQueue, sqs:DeleteQueue, sqs:ReceiveMessage, sqs:DeleteMessage
  - textract:StartDocumentAnalysis, textract:GetDocumentAnalysis
        """
    )
    
    parser.add_argument('pdf_file', help='Path to the PDF file to process')
    parser.add_argument('s3_bucket', help='S3 bucket name for document storage')
    parser.add_argument('aws_role_arn', help='IAM role ARN for Textract access')
    parser.add_argument('--page-ranges', '-p', help='Page ranges as "1-3,4-6,7-10" (optional)')
    parser.add_argument('--output', '-o', help='Output CSV file path (optional)')
    parser.add_argument('--json-output', '-j', help='Output JSON file path (optional)')
    parser.add_argument('--region', '-r', default='us-east-2', help='AWS region (default: us-east-2)')
    
    args = parser.parse_args()
    
    # Validate PDF file exists
    if not os.path.exists(args.pdf_file):
        print(f"❌ Error: PDF file '{args.pdf_file}' not found")
        sys.exit(1)
    
    # Create processor and run pipeline
    processor = TablePipelineProcessor(args.aws_role_arn, args.s3_bucket, args.region)
    
    result = processor.process_pdf_pipeline(
        pdf_file_path=args.pdf_file,
        page_ranges_str=args.page_ranges,
        output_csv_path=args.output,
        json_output_path=args.json_output
    )
    
    if result:
        print(f"\n🎉 Pipeline completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Pipeline failed")
        sys.exit(1)

if __name__ == "__main__":
    main()