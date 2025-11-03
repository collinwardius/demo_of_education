#!/bin/bash

# Process funding tables PDFs using master_program.py
# Source directory: /Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/scans/funding_tables
# Output directory: /Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/extracted_scans_funding

# AWS Configuration
S3_BUCKET="historical-education-college-tables"
AWS_ROLE_ARN="arn:aws:iam::672670075294:role/TextractRole"
AWS_REGION="us-east-2"

# Directories
INPUT_DIR="/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/scans/funding_tables"
OUTPUT_DIR="/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/extracted_scans_funding"
JSON_DIR="${OUTPUT_DIR}/textract_json"
LOG_FILE="${OUTPUT_DIR}/processing_log.txt"

# Create output directories if they don't exist
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${JSON_DIR}"

# Start logging
echo "========================================" | tee -a "${LOG_FILE}"
echo "Processing started: $(date)" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"

# Change to table_pipeline directory
cd /Users/cjwardius/Documents/GitHub/demo_of_education/table_pipeline

# Process each PDF file
echo "" | tee -a "${LOG_FILE}"
echo "Processing: bi_survey1916_1918_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/bi_survey1916_1918_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/bi_survey1916_1918_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/bi_survey1916_1918_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: bi_survey1916_1918_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: bi_survey1918_1920_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/bi_survey1918_1920_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/bi_survey1918_1920_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/bi_survey1918_1920_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: bi_survey1918_1920_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: bi_survey1920_1922_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/bi_survey1920_1922_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/bi_survey1920_1922_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/bi_survey1920_1922_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: bi_survey1920_1922_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: bi_survey1924_1926_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/bi_survey1924_1926_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/bi_survey1924_1926_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/bi_survey1924_1926_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: bi_survey1924_1926_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: bi_survey1926_1928_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/bi_survey1926_1928_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/bi_survey1926_1928_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/bi_survey1926_1928_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: bi_survey1926_1928_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: bi_survey1928_1930_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/bi_survey1928_1930_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/bi_survey1928_1930_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/bi_survey1928_1930_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: bi_survey1928_1930_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: bi_survey1930_1932_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/bi_survey1930_1932_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/bi_survey1930_1932_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/bi_survey1930_1932_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: bi_survey1930_1932_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: bi_survey1936_1938_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/bi_survey1936_1938_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/bi_survey1936_1938_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/bi_survey1936_1938_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: bi_survey1936_1938_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: commis_1913_1914_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/commis_1913_1914_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/commis_1913_1914_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/commis_1913_1914_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: commis_1913_1914_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "Processing: commis_1915_1916_funding_tables.pdf" | tee -a "${LOG_FILE}"
python3 master_program.py \
  "${INPUT_DIR}/commis_1915_1916_funding_tables.pdf" \
  "${S3_BUCKET}" \
  "${AWS_ROLE_ARN}" \
  --output "${OUTPUT_DIR}/commis_1915_1916_funding_tables_extracted.csv" \
  --json-output "${JSON_DIR}/commis_1915_1916_funding_tables.json" \
  --region "${AWS_REGION}" 2>&1 | tee -a "${LOG_FILE}"
echo "Completed: commis_1915_1916_funding_tables.pdf (Exit code: $?)" | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"
echo "All funding tables have been processed!" | tee -a "${LOG_FILE}"
echo "Processing completed: $(date)" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"
echo "Log saved to: ${LOG_FILE}" | tee -a "${LOG_FILE}"
