#!/bin/bash

# Census Data Cleaning and Linking Pipeline
# This script runs the complete pipeline for cleaning and linking census data
#
# Usage:
#   ./run_census_pipeline.sh <input_raw_data> <output_linked_data> [crosswalk_dir] [treatment_path] [analysis_output]
#
# Arguments:
#   input_raw_data:    Path to raw census data CSV
#   output_linked_data: Path to save final linked and merged census data CSV
#   crosswalk_dir:     (Optional) Directory containing county crosswalk files
#   treatment_path:    (Optional) Path to county treatment status CSV
#   analysis_output:   (Optional) Path to save pre-18 linking analysis LaTeX table

set -e  # Exit on error

# Check arguments
if [ $# -lt 2 ]; then
    echo "Error: Missing required arguments"
    echo ""
    echo "Usage:"
    echo "  ./run_census_pipeline.sh <input_raw_data> <output_linked_data> [crosswalk_dir] [treatment_path] [analysis_output]"
    echo ""
    echo "Arguments:"
    echo "  input_raw_data:     Path to raw census data CSV"
    echo "  output_linked_data: Path to save final linked and merged census data CSV"
    echo "  crosswalk_dir:      (Optional) Directory containing county crosswalk files"
    echo "  treatment_path:     (Optional) Path to county treatment status CSV"
    echo "  analysis_output:    (Optional) Path to save pre-18 linking analysis LaTeX table"
    exit 1
fi

# Parse arguments
INPUT_RAW=$1
OUTPUT_FINAL=$2
CROSSWALK_DIR=${3:-""}
TREATMENT_PATH=${4:-""}
ANALYSIS_OUTPUT=${5:-""}

# Generate intermediate file path (cleaned but not yet filtered/merged)
DIR=$(dirname "$OUTPUT_FINAL")
BASENAME=$(basename "$OUTPUT_FINAL" .csv)
OUTPUT_CLEANED="${DIR}/${BASENAME}_temp_cleaned.csv"

echo "========================================================================"
echo "CENSUS DATA PROCESSING PIPELINE"
echo "========================================================================"
echo "Input (raw data):        $INPUT_RAW"
echo "Output (cleaned):        $OUTPUT_CLEANED"
echo "Output (final linked):   $OUTPUT_FINAL"
if [ -n "$CROSSWALK_DIR" ]; then
    echo "Crosswalk directory:     $CROSSWALK_DIR"
fi
if [ -n "$TREATMENT_PATH" ]; then
    echo "Treatment data:          $TREATMENT_PATH"
fi
if [ -n "$ANALYSIS_OUTPUT" ]; then
    echo "Analysis output:         $ANALYSIS_OUTPUT"
fi
echo ""

# Step 1: Clean the census data
echo "========================================================================"
echo "STEP 1: CLEANING CENSUS DATA"
echo "========================================================================"
if [ -n "$CROSSWALK_DIR" ]; then
    python3 clean_census_data.py "$INPUT_RAW" "$OUTPUT_CLEANED" "$CROSSWALK_DIR"
else
    python3 clean_census_data.py "$INPUT_RAW" "$OUTPUT_CLEANED"
fi

if [ $? -ne 0 ]; then
    echo "Error: Data cleaning failed"
    exit 1
fi

echo ""
echo "Cleaning completed successfully!"
echo ""

# Step 2: Filter and merge
echo "========================================================================"
echo "STEP 2: FILTERING AND MERGING"
echo "========================================================================"
if [ -n "$TREATMENT_PATH" ]; then
    python3 filter_merge_cleaned_data.py "$OUTPUT_CLEANED" "$OUTPUT_FINAL" "$TREATMENT_PATH"
else
    python3 filter_merge_cleaned_data.py "$OUTPUT_CLEANED" "$OUTPUT_FINAL"
fi

if [ $? -ne 0 ]; then
    echo "Error: Filtering and merging failed"
    exit 1
fi

echo ""
echo "Filtering and merging completed successfully!"
echo ""

# Step 3: Analyze pre-18 linking
echo "========================================================================"
echo "STEP 3: ANALYZING PRE-18 LINKING"
echo "========================================================================"
if [ -n "$ANALYSIS_OUTPUT" ]; then
    python3 analyze_pre18_linking.py "$OUTPUT_CLEANED" "$ANALYSIS_OUTPUT"
else
    python3 analyze_pre18_linking.py "$OUTPUT_CLEANED"
fi

if [ $? -ne 0 ]; then
    echo "Error: Pre-18 linking analysis failed"
    exit 1
fi

echo ""
echo "Pre-18 linking analysis completed successfully!"
echo ""

# Step 4: Clean up temporary file
echo "========================================================================"
echo "CLEANUP"
echo "========================================================================"
echo "Removing temporary cleaned file: $OUTPUT_CLEANED"
rm "$OUTPUT_CLEANED"
echo "Temporary file removed"
echo ""

# Final summary
echo "========================================================================"
echo "PIPELINE COMPLETED SUCCESSFULLY!"
echo "========================================================================"
echo "Final output saved to: $OUTPUT_FINAL"
echo ""
