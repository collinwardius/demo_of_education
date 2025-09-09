# Table Header Extraction Instructions

## Context
This document describes the requirements for extracting nested table headers from Amazon Textract JSON output and converting them to flattened CSV column names.

## Source Data
- **File**: `bi_survey1916_1918 (1)/analyzeDocResponse.json` (216.5MB)
- **Content**: Textract analysis of a 155-page historical document about universities, colleges, and professional schools from 1916-1918
- **Structure**: Contains TABLE blocks with nested CELL blocks that have complex header hierarchies

## Requirements

### 1. Focus on Headers Only (Initial Phase)
- Start small by extracting only the table headers, not the data
- Focus on the first table to begin with
- Headers are frequently nested and complex

### 2. Header Nesting Patterns
Headers can be nested in multiple ways:
- **Column spanning**: Headers can span 2-7+ columns (e.g., "Total Professors" spanning "Men" and "Women")
- **Row spanning**: Headers can span 2-5+ rows vertically
- **Multi-level hierarchy**: Could have 2, 3, or more header row levels

### 3. Desired Output Format
Convert nested headers to flattened column names using underscore concatenation:

**Example Input Structure:**
```
Total Professors
    Men
    Women
```

**Example Output:**
- `total_professors_men`
- `total_professors_women`

### 4. Text Processing
- Convert to lowercase
- Replace spaces with underscores
- Remove punctuation as needed
- Create clean, descriptive variable names

### 5. JSON Structure Details
Each CELL block contains:
- `RowIndex`: Position in table rows
- `ColumnIndex`: Position in table columns  
- `RowSpan`: How many rows the cell spans
- `ColumnSpan`: How many columns the cell spans
- `Text`: The actual header text content

### 6. Final Deliverable
- Python script that processes the JSON file
- Outputs CSV with flattened header names
- Handles complex multi-dimensional header spanning
- Creates unique column names preserving hierarchical meaning

## Implementation Approach
1. Find first TABLE block in JSON
2. Extract all header CELL blocks (typically rows 1-3)
3. Map the hierarchy by analyzing span relationships
4. Trace parent-child relationships for each final column
5. Generate concatenated names with underscores
6. Output as CSV header row