# Historical Education Data Extractor using Amazon Textract

This script extracts structured data from historical education documents, census records, and statistical reports using Amazon Textract. It's specifically optimized for educational research data commonly found in historical documents.

## Features

- **Historical Document Processing**: Optimized for older documents with varying quality
- **Education-Focused**: Automatically identifies and processes education-related tables
- **Stata Integration**: Exports data in Stata-compatible CSV format with proper variable names
- **Data Validation**: Filters tables based on education keywords and data patterns
- **Metadata Generation**: Creates metadata files documenting column types and extraction details

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure AWS Credentials
Set up your AWS credentials using one of these methods:

#### Option A: AWS CLI
```bash
aws configure
```

#### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

#### Option C: IAM Role (if running on EC2)
Attach an IAM role with Textract permissions to your EC2 instance.

### 3. Required AWS Permissions
Your AWS user/role needs the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText",
                "textract:AnalyzeDocument"
            ],
            "Resource": "*"
        }
    ]
}
```

## Usage

### Basic Usage
```bash
# Process a single image
python historical_education_textract.py path/to/historical_document.png

# Process all images in a directory
python historical_education_textract.py path/to/documents/

# Specify output directory
python historical_education_textract.py input.jpg --output-dir data/extracted
```

### Command Line Options
- `input_path`: Path to image file or directory containing images
- `--output-dir`, `-o`: Output directory for extracted data (default: `data/clean`)
- `--region`: AWS region (default: `us-east-1`)

## Supported File Types
- PNG
- JPEG/JPG  
- TIFF
- PDF

## Output Files

For each processed document, the script generates:

1. **`*_education_data.csv`**: Stata-compatible CSV file with cleaned data
2. **`*_education_data_raw.csv`**: Raw extracted data for examination
3. **`*_education_data_metadata.json`**: Metadata about columns and extraction

### Example Output Structure
```
data/clean/
├── census_1940_education_data.csv
├── census_1940_education_data_raw.csv
├── census_1940_education_data_metadata.json
└── historical_education_extraction.log
```

## Integration with Existing Analysis

The extracted CSV files are designed to work seamlessly with your existing Stata and R analysis:

### Stata Integration
```stata
// Import extracted data
import delimited "data/clean/historical_doc_education_data.csv", clear

// The variable names are already Stata-compatible
describe
summarize
```

### R Integration
```r
# Load extracted data
library(readr)
education_data <- read_csv("data/clean/historical_doc_education_data.csv")

# Merge with existing data
combined_data <- merge(existing_data, education_data, by="state")
```

## Data Quality Features

### Automatic Table Detection
- Identifies education-related tables using keyword matching
- Filters based on presence of years, enrollment numbers, and percentages
- Skips irrelevant tables automatically

### Data Cleaning
- Removes OCR artifacts and formatting inconsistencies
- Converts numeric data appropriately (handles commas, percentages)
- Creates Stata-compatible variable names
- Identifies column types (year, geography, enrollment, percentage, etc.)

### Quality Thresholds
- Minimum confidence threshold of 50% for cell extraction
- Word-level confidence threshold of 60%
- Validates tables contain education-related content

## Common Use Cases

### Historical Census Data
Extract education statistics from historical census tabulations:
```bash
python historical_education_textract.py census_tables/1940_education.png
```

### University Statistics
Process historical university enrollment reports:
```bash
python historical_education_textract.py university_reports/ --output-dir data/university_data
```

### State Education Reports
Extract data from state-level education reports:
```bash
python historical_education_textract.py state_reports/california_1930s.jpg
```

## Troubleshooting

### Common Issues

1. **No tables detected**: Ensure the document contains clear tabular data with education-related keywords
2. **Poor extraction quality**: Try preprocessing the image (contrast adjustment, noise reduction)
3. **AWS permissions error**: Verify your AWS credentials and permissions
4. **Empty output**: Check the log file for processing details and errors

### Improving Results

- **Image Quality**: Higher resolution images (300+ DPI) work better
- **Contrast**: Ensure good contrast between text and background  
- **Orientation**: Images should be properly oriented (not rotated)
- **Format**: PNG and TIFF typically work better than JPEG for documents

## Cost Considerations

Amazon Textract pricing (as of 2024):
- Detect Document Text: $1.50 per 1,000 pages
- Analyze Document (Tables): $15.00 per 1,000 pages

For large document collections, consider batch processing during off-peak hours.

## Example Workflow

```bash
# 1. Place historical documents in a folder
mkdir historical_docs
cp *.png historical_docs/

# 2. Process all documents
python historical_education_textract.py historical_docs/ --output-dir data/clean

# 3. Use in Stata analysis
stata-mp
> use "data/clean/document1_education_data.csv", clear
> merge 1:1 state using "data/usa_00013"
> analyze...
```