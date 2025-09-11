# PDF Table Extraction Pipeline

A complete pipeline for extracting tables from PDF documents using Amazon S3, Amazon Textract, and Python. The pipeline uploads PDFs to S3, analyzes them with Textract, and exports the extracted tables to CSV files.

## 🏗️ Architecture Overview

```
PDF File → S3 Upload → Textract Analysis → JSON Results → CSV Export
```

## 📁 File Structure

### `master_program.py` - Main Pipeline Controller
The orchestrator that runs all three components in sequence. This is the primary file you'll use.

**Key Features:**
- Complete end-to-end pipeline execution
- Command-line interface with comprehensive options
- Error handling and progress reporting
- Support for page range extraction
- Automatic file naming and organization

### `pdf_to_s3_uploader.py` - S3 Upload Component
Handles uploading PDF files to Amazon S3 buckets.

**Key Features:**
- Single file or batch directory uploads
- PDF validation before upload
- AWS credential validation
- Comprehensive error handling for S3 operations

### `s3_textract_async.py` - Textract Analysis Component  
Manages Amazon Textract document analysis using asynchronous processing.

**Key Features:**
- Automatic SNS/SQS setup for job notifications
- Support for both text detection and document analysis
- Configurable feature extraction (TABLES, FORMS, etc.)
- Result pagination handling
- Automatic cleanup of AWS resources

### `extract_table_raw.py` - CSV Export Component
Processes Textract JSON results and converts tables to CSV format.

**Key Features:**
- Header row detection and flagging
- Page range processing for multi-document extraction
- Data standardization and padding
- Multiple output format support

## 🚀 Quick Start

### Prerequisites
1. **AWS Account** with appropriate permissions
2. **Python 3.7+** with required packages:
   ```bash
   pip install boto3 pandas
   ```
3. **AWS Credentials** configured via:
   - AWS CLI: `aws configure`
   - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - IAM roles (if running on EC2)

4. **AWS IAM Role Setup** (Critical - see detailed setup below):
   - Create an IAM role that Textract can assume
   - Configure proper permissions and trust relationships
   - Note your actual AWS account ID for the role ARN

### Basic Usage

```bash
# Process entire PDF
python3 master_program.py document.pdf my-s3-bucket arn:aws:iam::YOUR_ACCOUNT:role/TextractRole

# Process specific pages
python3 master_program.py document.pdf my-s3-bucket arn:aws:iam::YOUR_ACCOUNT:role/TextractRole --page-ranges "1-3,5-7"

# Custom output file
python3 master_program.py document.pdf my-s3-bucket arn:aws:iam::YOUR_ACCOUNT:role/TextractRole --output my_tables.csv
```

### Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `pdf_file` | Path to PDF file (required) | `document.pdf` |
| `s3_bucket` | S3 bucket name (required) | `my-documents-bucket` |
| `aws_role_arn` | IAM role ARN (required) | `arn:aws:iam::123456789:role/TextractRole` |
| `--page-ranges, -p` | Page ranges to extract | `"1-3,4-6,7-10"` |
| `--output, -o` | Output CSV path | `results.csv` |
| `--region, -r` | AWS region | `us-east-1` |

## 🔑 AWS IAM Role Setup (REQUIRED)

**This is the most critical setup step.** The pipeline requires a properly configured IAM role for Textract to access your S3 bucket and manage notifications.

### Step-by-Step Role Creation

1. **Go to AWS IAM Console** → Roles → Create Role

2. **Select Trusted Entity:**
   - Choose "AWS Service"
   - Select "Textract" from the service list
   - Click "Next"

3. **Attach Permissions Policy:**
   Create a custom policy with these permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "textract:StartDocumentAnalysis",
           "textract:GetDocumentAnalysis",
           "s3:GetObject",
           "s3:PutObject",
           "sns:CreateTopic",
           "sns:DeleteTopic", 
           "sns:Publish",
           "sqs:CreateQueue",
           "sqs:DeleteQueue",
           "sqs:ReceiveMessage",
           "sqs:DeleteMessage",
           "sqs:SetQueueAttributes"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

4. **Name Your Role:** e.g., "TextractDocumentProcessingRole"

5. **Note the Role ARN:** It will look like:
   ```
   arn:aws:iam::YOUR_ACCOUNT_ID:role/TextractDocumentProcessingRole
   ```

6. **Important:** Replace `YOUR_ACCOUNT_ID` with your actual 12-digit AWS account number

### Trust Relationship Verification
Ensure your role trusts the Textract service. The trust policy should include:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "textract.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## ⚠️ Common Pitfalls & Solutions

### 1. AWS IAM Role Issues (MOST COMMON)
**Error:** `InvalidParameterException` or `AccessDenied`

**Solutions:**
- **Use correct Account ID:** Replace `123` in ARN with your actual AWS account number
- **Verify role exists:** Check IAM console for the role
- **Required permissions:**
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "textract:StartDocumentAnalysis",
          "textract:GetDocumentAnalysis",
          "s3:GetObject",
          "s3:PutObject",
          "sns:CreateTopic",
          "sns:DeleteTopic", 
          "sns:Publish",
          "sqs:CreateQueue",
          "sqs:DeleteQueue",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:SetQueueAttributes"
        ],
        "Resource": "*"
      }
    ]
  }
  ```
- **Trust relationship:** Role must trust `textract.amazonaws.com`

### 2. S3 Bucket Issues
**Error:** `NoSuchBucket` or `AccessDenied`

**Solutions:**
- Ensure bucket exists in the correct region
- Verify your AWS credentials have S3 permissions
- Check bucket policies don't block your access
- Ensure bucket name follows AWS naming conventions

### 3. AWS Credentials
**Error:** `NoCredentialsError`

**Solutions:**
- Run `aws configure` to set up credentials
- Set environment variables:
  ```bash
  export AWS_ACCESS_KEY_ID=your_access_key
  export AWS_SECRET_ACCESS_KEY=your_secret_key
  ```
- If on EC2, ensure instance has appropriate IAM role

### 4. File Path Issues
**Error:** File not found or permission errors

**Solutions:**
- Use absolute paths when possible
- Ensure PDF file exists and is readable
- Check file permissions: `chmod 644 your_file.pdf`
- Verify file is actually a PDF (not renamed)

### 5. Network/Timeout Issues
**Error:** Connection timeouts or service unavailable

**Solutions:**
- Check internet connectivity
- Verify AWS service status
- Try different AWS region if persistent issues
- Ensure no firewall blocking AWS APIs

### 6. Large File Processing
**Error:** Processing timeout or memory issues

**Solutions:**
- Break large documents into smaller page ranges
- Use `--page-ranges` option for selective processing
- Ensure sufficient disk space for temporary files
- Consider processing during off-peak hours

### 7. Python Dependencies
**Error:** `ModuleNotFoundError`

**Solutions:**
```bash
pip install boto3 pandas argparse pathlib
# Or if using conda:
conda install boto3 pandas
```

## 📊 Output Files

The pipeline generates several files:

1. **`{document_name}_textract_results.json`** - Raw Textract analysis results
2. **`{document_name}_extracted_tables.csv`** - Main CSV output with extracted tables
3. **`{document_name}_extracted_tables_pages_X_to_Y.csv`** - Page range specific files (if using --page-ranges)

### CSV Format
- First column: Header indicator (1 = header row, 0 = data row)
- Remaining columns: Table data from PDF
- Empty cells padded for consistent column count

## 🔧 Advanced Usage

### Individual Component Usage

**Upload only:**
```bash
python3 pdf_to_s3_uploader.py document.pdf my-bucket
```

**Textract only (requires file already in S3):**
```bash
python3 s3_textract_async.py arn:aws:iam::123:role/TextractRole my-bucket document.pdf
```

**Extract only (requires JSON file):**
```bash
python3 extract_table_raw.py --json-file results.json --output tables.csv
```

### Batch Processing
```bash
# Upload multiple PDFs
python3 pdf_to_s3_uploader.py --dir ./pdf_directory my-bucket

# Process multiple documents with a script
for pdf in *.pdf; do
  python3 master_program.py "$pdf" my-bucket arn:aws:iam::123:role/TextractRole
done
```

## 🐛 Troubleshooting

1. **Enable verbose logging:** Add print statements to see where processing stops
2. **Check AWS CloudTrail:** View API calls and errors in AWS console
3. **Validate JSON:** Ensure Textract JSON is valid before CSV extraction
4. **Test components individually:** Run each script separately to isolate issues
5. **Check AWS service limits:** Textract has concurrent job limits

## 💡 Tips for Best Results

- **PDF Quality:** Higher resolution PDFs yield better table extraction
- **Table Structure:** Well-defined table borders improve accuracy  
- **Page Selection:** Use page ranges to focus on relevant sections
- **File Organization:** Use descriptive output filenames for batch processing
- **Cost Optimization:** Monitor AWS usage, especially for large document sets

## 🆘 Support

For issues:
1. Check error messages against common pitfalls above
2. Verify AWS permissions and credentials
3. Test with a simple, single-page PDF first
4. Check AWS documentation for service-specific requirements