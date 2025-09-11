#!/usr/bin/env python3

import boto3
import os
import sys
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

def upload_pdf_to_s3(pdf_file_path, bucket_name, s3_key=None):
    """
    Upload a PDF file to Amazon S3
    
    Args:
        pdf_file_path (str): Path to the PDF file
        bucket_name (str): Name of the S3 bucket
        s3_key (str, optional): S3 object key. If None, uses the filename
    
    Returns:
        bool: True if upload successful, False otherwise
    """
    
    # Validate PDF file exists
    if not os.path.exists(pdf_file_path):
        print(f"Error: File {pdf_file_path} does not exist")
        return False
    
    # Validate it's a PDF file
    if not pdf_file_path.lower().endswith('.pdf'):
        print(f"Error: File {pdf_file_path} is not a PDF file")
        return False
    
    # Set S3 key if not provided
    if s3_key is None:
        s3_key = Path(pdf_file_path).name
    
    try:
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Upload file
        print(f"Uploading {pdf_file_path} to s3://{bucket_name}/{s3_key}...")
        s3_client.upload_file(pdf_file_path, bucket_name, s3_key)
        
        print(f"✓ Successfully uploaded {pdf_file_path} to S3")
        print(f"  S3 URI: s3://{bucket_name}/{s3_key}")
        return True
        
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your credentials.")
        print("You can set them via:")
        print("  - AWS CLI: aws configure")
        print("  - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("  - IAM roles (if running on EC2)")
        return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"Error: Bucket '{bucket_name}' does not exist")
        elif error_code == 'AccessDenied':
            print(f"Error: Access denied to bucket '{bucket_name}'. Check your permissions.")
        else:
            print(f"Error uploading file: {e}")
        return False
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def upload_multiple_pdfs(pdf_directory, bucket_name, s3_prefix=""):
    """
    Upload all PDF files from a directory to S3
    
    Args:
        pdf_directory (str): Directory containing PDF files
        bucket_name (str): Name of the S3 bucket
        s3_prefix (str): Optional prefix for S3 keys
    """
    pdf_files = list(Path(pdf_directory).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to upload")
    
    success_count = 0
    for pdf_file in pdf_files:
        s3_key = f"{s3_prefix}{pdf_file.name}" if s3_prefix else pdf_file.name
        if upload_pdf_to_s3(str(pdf_file), bucket_name, s3_key):
            success_count += 1
        print()  # Add spacing between uploads
    
    print(f"Upload complete: {success_count}/{len(pdf_files)} files uploaded successfully")

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Single file: python pdf_to_s3_uploader.py <pdf_file> <bucket_name> [s3_key]")
        print("  Directory:   python pdf_to_s3_uploader.py --dir <pdf_directory> <bucket_name> [s3_prefix]")
        print()
        print("Examples:")
        print("  python pdf_to_s3_uploader.py document.pdf my-bucket")
        print("  python pdf_to_s3_uploader.py document.pdf my-bucket custom/path/document.pdf")
        print("  python pdf_to_s3_uploader.py --dir ./pdfs my-bucket reports/")
        sys.exit(1)
    
    if sys.argv[1] == "--dir":
        # Directory upload
        if len(sys.argv) < 4:
            print("Error: Directory upload requires <pdf_directory> <bucket_name>")
            sys.exit(1)
        
        pdf_directory = sys.argv[2]
        bucket_name = sys.argv[3]
        s3_prefix = sys.argv[4] if len(sys.argv) > 4 else ""
        
        upload_multiple_pdfs(pdf_directory, bucket_name, s3_prefix)
    
    else:
        # Single file upload
        pdf_file = sys.argv[1]
        bucket_name = sys.argv[2]
        s3_key = sys.argv[3] if len(sys.argv) > 3 else None
        
        upload_pdf_to_s3(pdf_file, bucket_name, s3_key)

if __name__ == "__main__":
    main()