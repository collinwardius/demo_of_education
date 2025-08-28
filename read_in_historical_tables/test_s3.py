#!/usr/bin/env python3
"""
PDF Table Detection using Amazon Textract
Detects which pages contain tables
"""

import boto3
import json

s3BucketName = "historical-education-college-tables"
documentName = "test_table_detect_pdf.pdf"

# Specify region explicitly (Textract is only available in certain regions)
textract = boto3.client('textract', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

# First, let's verify the S3 object exists and check bucket region
try:
    # Check bucket region
    bucket_location = s3.get_bucket_location(Bucket=s3BucketName)
    bucket_region = bucket_location['LocationConstraint'] or 'us-east-1'
    print(f"Bucket region: {bucket_region}")
    
    s3.head_object(Bucket=s3BucketName, Key=documentName)
    print(f"✓ S3 object {documentName} found in bucket {s3BucketName}")
    
    # If bucket is in different region, recreate clients
    if bucket_region != 'us-east-1':
        print(f"Switching to bucket region: {bucket_region}")
        textract = boto3.client('textract', region_name=bucket_region)
        s3 = boto3.client('s3', region_name=bucket_region)
    
except Exception as e:
    print(f"✗ S3 object check failed: {e}")
    exit(1)

# For multi-page PDFs, use async analysis
import time

print("Starting asynchronous document analysis...")
job = textract.start_document_analysis(
    DocumentLocation={
        'S3Object': {
            'Bucket': s3BucketName,
            'Name': documentName
        }
    },
    FeatureTypes=["TABLES"]
)

job_id = job['JobId']
print(f"Job ID: {job_id}")

# Wait for job completion
print("Waiting for analysis to complete...")
while True:
    response = textract.get_document_analysis(JobId=job_id)
    status = response['JobStatus']
    print(f"Status: {status}")
    
    if status in ['SUCCEEDED', 'FAILED']:
        break
    
    time.sleep(5)

if status == 'FAILED':
    print("Analysis failed!")
    exit(1)

# Get all pages if there are multiple result pages
all_blocks = response['Blocks']
next_token = response.get('NextToken')

while next_token:
    print("Getting additional results...")
    response_next = textract.get_document_analysis(JobId=job_id, NextToken=next_token)
    all_blocks.extend(response_next['Blocks'])
    next_token = response_next.get('NextToken')

# Update response to include all blocks
response['Blocks'] = all_blocks

# Find pages with tables
pages_with_tables = set()

# Look through all blocks to find tables
for block in response['Blocks']:
    if block['BlockType'] == 'TABLE':
        page = block.get('Page', 1)
        pages_with_tables.add(page)

# Sort and display results
if pages_with_tables:
    sorted_pages = sorted(pages_with_tables)
    print(f"Pages with tables: {sorted_pages}")
    print(f"Total pages with tables: {len(sorted_pages)}")
else:
    print("No tables found in the document")

# Show total number of blocks processed
print(f"Total blocks processed: {len(response['Blocks'])}")

# Show document metadata
document_metadata = response.get('DocumentMetadata', {})
if 'Pages' in document_metadata:
    print(f"Total pages in document: {document_metadata['Pages']}")