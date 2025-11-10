# Table Extraction Pipeline with AWS Textract

## Overview

This workflow uses AWS Textract to automatically detect tables in PDF documents, extract their bounding boxes and titles, and save each table as both an image (PNG) and structured data (CSV) with descriptive filenames.

All outputs are organized into a clean directory structure: `json/`, `png/`, and `csv/` subdirectories.

## What Was Created

### 1. `extract_tables_master.py` ⭐ **MAIN PROGRAM**
Master program that orchestrates the complete workflow.

**Features:**
- Single command to run entire extraction pipeline
- Automatically creates organized output directory structure (json/, png/, csv/)
- Runs all three extraction steps in sequence
- Provides clear progress reporting
- Supports skipping individual steps (--skip-bbox, --skip-png, --skip-csv)

**This is the primary program you should use for most workflows.**

### 2. `extract_table_bboxes_simple.py`
Extracts table bounding boxes and metadata from PDFs using AWS Textract.

**Features:**
- Splits large PDFs to process only specified pages (cost-effective testing)
- Uploads PDFs to S3 temporarily
- Uses Textract's async table detection API
- Polls for job completion (simplified version without SNS/SQS)
- Extracts table titles and associates them with tables
- **Saves ALL Textract blocks** (11,000+ blocks including CELL and WORD data)
- Outputs comprehensive JSON with complete table metadata

**Key Metadata Captured:**
- Table bounding boxes (normalized coordinates)
- Polygon coordinates (4 corner points)
- Table titles (detected via `TABLE_TITLE` blocks)
- Page numbers
- Confidence scores
- **All CELL blocks** with RowIndex, ColumnIndex, and text content
- **All WORD blocks** for detailed text extraction

### 3. `extract_tables_from_bboxes.py`
Extracts table images from PDFs using bounding box coordinates.

**Features:**
- Reads JSON output from the bbox extraction script
- Converts PDF pages to high-resolution images (300 DPI)
- Crops each table using bounding box coordinates
- Creates descriptive filenames using table titles
- Handles duplicate titles by adding counters (`_1`, `_2`, etc.)
- Sanitizes titles for filesystem compatibility

### 4. `extract_table_text_to_csv.py`
Extracts table text content and exports to CSV files.

**Features:**
- Reads saved Textract blocks from JSON (no additional API calls)
- Extracts cell text organized by row and column
- Handles merged cells (RowSpan, ColumnSpan)
- Creates CSV files with same naming convention as PNG files
- Preserves table structure and reading order

## AWS Textract Metadata Available

Textract provides extensive metadata, **all of which is now captured**:

### Table-Level Metadata ✅
- **Bounding Box**: Normalized coordinates (left, top, width, height)
- **Polygon**: 4 corner points for precise boundaries
- **Confidence**: Detection confidence score (0-100%)
- **Entity Types**: `STRUCTURED_TABLE` vs semi-structured
- **Row/Column Count**: Table dimensions

### Title & Footer Metadata ✅
- **TABLE_TITLE blocks**: Text appearing above tables
- **TABLE_FOOTER blocks**: Footnotes and sources below tables
- Both include text content, position, and confidence

### Cell-Level Metadata ✅ **NOW CAPTURED**
- **Cell position**: RowIndex, ColumnIndex
- **Cell spans**: RowSpan, ColumnSpan for merged cells
- **Cell text**: Actual text content in each cell
- **Cell confidence**: Per-cell confidence scores

### Word-Level Metadata ✅ **NOW CAPTURED**
- **Individual words**: Text, position, confidence
- **Text type**: PRINTED vs HANDWRITING
- **Reading order**: How elements relate spatially

## Quick Start (Recommended Method)

### Using the Master Program

This is the simplest way to extract all table data:

```bash
python3 extract_tables_master.py \
  <pdf_file> \
  <output_directory> \
  <s3_bucket_name> \
  --max-pages <num_pages> \
  --region <aws_region>
```

**Example:**
```bash
python3 extract_tables_master.py \
  "/path/to/biennial_20_22.pdf" \
  "/path/to/output/biennial_20_22" \
  historical-education-college-tables \
  --max-pages 20 \
  --region us-east-2
```

**Output Structure:**
```
biennial_20_22/
├── json/
│   └── biennial_20_22_textract.json  (Complete Textract results: 11MB)
├── png/
│   ├── page_008_contents.png
│   ├── page_011_table_1_-school_and_college_enrollment_in_1921-22.png
│   ├── page_012_table_3_-gifts_and_bequests_to_education,_1912-1922.png
│   └── ... (16 total PNG files)
└── csv/
    ├── page_008_contents.csv
    ├── page_011_table_1_-school_and_college_enrollment_in_1921-22.csv
    ├── page_012_table_3_-gifts_and_bequests_to_education,_1912-1922.csv
    └── ... (16 total CSV files)
```

**What Happens:**
1. ✅ Creates output directory structure (json/, png/, csv/)
2. ✅ Runs Textract to extract all table metadata
3. ✅ Saves complete JSON with 11,000+ blocks
4. ✅ Extracts PNG images of each table
5. ✅ Extracts CSV data of each table
6. ✅ All files use matching names for easy comparison

**Skip Flags:**
```bash
# Only extract PNG and CSV (use existing JSON)
--skip-bbox

# Skip PNG extraction
--skip-png

# Skip CSV extraction
--skip-csv
```

## Advanced Usage (Individual Programs)

You can also run the programs individually for more control:

### Step 1: Extract Table Bounding Boxes and Metadata

```bash
python3 extract_table_bboxes_simple.py \
  "<pdf_path>" \
  <s3_bucket_name> \
  --output <output_json> \
  --max-pages <num_pages> \
  --region <aws_region>
```

**Example:**
```bash
python3 extract_table_bboxes_simple.py \
  "/path/to/biennial_20_22.pdf" \
  historical-education-college-tables \
  --output biennial_20_22_textract.json \
  --max-pages 20 \
  --region us-east-2
```

**Output JSON Structure:**
```json
{
  "pdf_file": "biennial_20_22.pdf",
  "s3_bucket": "historical-education-college-tables",
  "s3_key": "temp/temp_pages_1762722061.pdf",
  "job_id": "1683f2b7...",
  "total_tables": 16,
  "tables": [
    {
      "id": "bca99b5d-1d24-497c-827a-fc8a8752dbd6",
      "page": 8,
      "confidence": 99.853515625,
      "title": "CONTENTS",
      "title_confidence": 97.802734375,
      "bounding_box": {
        "left": 0.115,
        "top": 0.358,
        "width": 0.777,
        "height": 0.237
      },
      "polygon": [...],
      "cell_ids": [...]
    }
  ],
  "all_blocks": [
    {
      "BlockType": "CELL",
      "RowIndex": 1,
      "ColumnIndex": 1,
      "Text": "Kindergartens",
      "Confidence": 99.5,
      ...
    },
    ...
  ]
}
```

### Step 2: Extract Table Images

```bash
python3 extract_tables_from_bboxes.py \
  "<pdf_path>" \
  <bbox_json> \
  <output_directory> \
  --max-pages <num_pages>
```

**Example:**
```bash
python3 extract_tables_from_bboxes.py \
  "/path/to/biennial_20_22.pdf" \
  biennial_20_22_textract.json \
  "/path/to/output/png" \
  --max-pages 20
```

### Step 3: Extract Table Text to CSV

```bash
python3 extract_table_text_to_csv.py \
  <bbox_json> \
  <output_directory>
```

**Example:**
```bash
python3 extract_table_text_to_csv.py \
  biennial_20_22_textract.json \
  "/path/to/output/csv"
```

## Requirements

### Python Packages
```bash
pip install boto3 pypdf pdf2image pillow
```

### System Requirements
- `poppler-utils` (for pdf2image)
  - macOS: `brew install poppler`
  - Ubuntu: `apt-get install poppler-utils`

### AWS Requirements
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- S3 bucket for temporary storage
- IAM permissions:
  - `textract:StartDocumentAnalysis`
  - `textract:GetDocumentAnalysis`
  - `s3:PutObject`
  - `s3:GetObject`

## How It Works

### PDF Splitting (Cost Optimization)
When `--max-pages` is specified:
1. Uses PyPDF to extract only the first N pages
2. Creates a temporary PDF in `/tmp/`
3. Uploads only this smaller PDF to S3
4. Processes with Textract (lower cost)
5. Cleans up temporary file after processing

### Title Association Algorithm
1. Collects all `TABLE_TITLE` blocks from Textract
2. For each `TABLE` block:
   - Finds titles on the same page
   - Filters titles positioned above the table (title.top < table.top)
   - Selects the closest title (highest top value below table)
3. Associates title text with the table

### CSV Extraction Algorithm
1. Reads all blocks from saved JSON file (no additional API calls)
2. For each table:
   - Gets all CELL blocks via relationships
   - Builds 2D grid using RowIndex and ColumnIndex
   - Handles merged cells by filling spanned positions
   - Extracts text from child WORD blocks
3. Exports grid to CSV

### Filename Sanitization
- Removes invalid characters: `< > : " / \ | ? *`
- Replaces spaces and periods with underscores
- Removes consecutive underscores
- Truncates to 80 characters max
- Converts to lowercase
- Handles duplicates with numeric suffixes

## Test Results

### Test Document: `biennial_20_22.pdf` (First 20 pages)

**Input:**
- PDF: 151 MB, 20 pages processed
- Processing time: ~30 seconds total

**Results:**
- **16 tables detected**
- **14 titles extracted**
- **2 tables without titles** (fallback naming used)
- **11,262 total blocks saved** (CELL, WORD, LINE, PAGE, TABLE, TABLE_TITLE)
- **3,376 CELL blocks** with text content
- **4,936 WORD blocks** for detailed text

**Example Titles Detected:**
- "CONTENTS"
- "TABLE 1.-School and college enrollment in 1921-22"
- "TABLE 2.-School enrollment and estimated cost in 1921-22"
- "TABLE 7.-Enrollment in certain types of schools, by States, 1921-22"
- "TABLE 9.-Survivals of the class entering in 1911..."
- "BIENNIAL SURVEY OF EDUCATION, 1920-1922"
- "STATISTICAL SURVEY OF EDUCATION"

**Confidence Scores:**
- Most tables: 99-100% confidence
- Lowest: 72.8% (small embedded table)

**CSV Extraction:**
- Table sizes range from 9 rows × 2 columns to 60 rows × 12 columns
- All cell text successfully extracted
- Merged cells handled correctly

## Cost Considerations

### Textract Pricing (as of 2024)
- Document Analysis: $1.50 per 1,000 pages
- Feature: Tables included in base price

### Cost Optimization Strategies
1. **Use `--max-pages`** to test on small samples first (20 pages = ~$0.03)
2. **One-time extraction**: All data (bboxes, images, text) from single Textract run
3. **Cache JSON results**: Save complete JSON to avoid reprocessing
4. **S3 lifecycle policies**: Auto-delete temporary files after 1 day

**Example Costs:**
- 20 pages: ~$0.03
- 100 pages: ~$0.15
- 1,000 pages: ~$1.50

**Note:** The master program runs Textract **only once** and extracts everything from the saved JSON, so there are no additional API costs for PNG/CSV extraction.

## Comparison: PNG vs CSV

For each table, you get both visual and structured data:

**PNG (Visual)**
- High-resolution image (300 DPI)
- Preserves exact layout and formatting
- Good for visual verification
- File sizes: 23KB - 1.7MB

**CSV (Structured)**
- Machine-readable text data
- Easy to import into spreadsheets/databases
- Good for data analysis
- File sizes: 290B - 4.5KB

This allows you to **visually compare** the PNG against the extracted CSV data to verify Textract's accuracy.

## Troubleshooting

### Issue: "InvalidS3ObjectException"
**Cause**: Region mismatch or IAM permissions
**Solution**:
- Ensure `--region` matches S3 bucket region
- Verify IAM role has S3 GetObject permission

### Issue: Textract job times out
**Cause**: Large PDFs take time to process
**Solution**:
- Start with `--max-pages 20` for testing
- Wait longer (can take 30+ seconds for complex pages)

### Issue: Missing table titles
**Cause**: Textract didn't detect title, or title is below table
**Solution**:
- Check if title exists visually in PDF
- Titles must be above tables to be associated
- Falls back to `page_{page}_table_{number}` naming

### Issue: Duplicate filenames
**Cause**: Multiple tables with same title
**Solution**: Automatic - script adds `_1`, `_2` suffixes

### Issue: "This JSON file doesn't contain 'all_blocks'"
**Cause**: JSON file created with old version of script
**Solution**: Re-run `extract_table_bboxes_simple.py` to generate new JSON with all blocks

### Issue: Empty CSV cells
**Cause**: Textract couldn't read text in that cell
**Solution**: Check PNG image to see if cell is actually empty or unreadable in source

## References

- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [Textract Table Detection Guide](https://docs.aws.amazon.com/textract/latest/dg/how-it-works-tables.html)
- [PyPDF Documentation](https://pypdf.readthedocs.io/)
- [pdf2image Documentation](https://github.com/Belval/pdf2image)

## Authors

Created for the Demo of Education historical data extraction project.
