#!/bin/bash

# Census Data Filtering and Linking Pipeline (Partial - assumes data is already cleaned)
# This script runs only the filtering/merging and analysis steps
#
# Usage:
#   ./run_census_pipeline_partial.sh <input_cleaned_data> <output_linked_data> [treatment_path] [analysis_output]
#
# Arguments:
#   input_cleaned_data:  Path to already-cleaned census data CSV
#   output_linked_data:  Path to save final linked and merged census data CSV
#   treatment_path:      (Optional) Path to county treatment status CSV
#   analysis_output:     (Optional) Path to save pre-18 linking analysis LaTeX table

set -e  # Exit on error

# Check arguments
if [ $# -lt 2 ]; then
    echo "Error: Missing required arguments"
    echo ""
    echo "Usage:"
    echo "  ./run_census_pipeline_partial.sh <input_cleaned_data> <output_linked_data> [treatment_path] [analysis_output]"
    echo ""
    echo "Arguments:"
    echo "  input_cleaned_data:  Path to already-cleaned census data CSV"
    echo "  output_linked_data:  Path to save final linked and merged census data CSV"
    echo "  treatment_path:      (Optional) Path to county treatment status CSV"
    echo "  analysis_output:     (Optional) Path to save pre-18 linking analysis LaTeX table"
    exit 1
fi

# Parse arguments
INPUT_CLEANED=$1
OUTPUT_FINAL=$2
TREATMENT_PATH=${3:-""}
ANALYSIS_OUTPUT=${4:-""}

echo "========================================================================"
echo "CENSUS DATA PROCESSING PIPELINE (PARTIAL)"
echo "========================================================================"
echo "Input (cleaned data):    $INPUT_CLEANED"
echo "Output (final linked):   $OUTPUT_FINAL"
if [ -n "$TREATMENT_PATH" ]; then
    echo "Treatment data:          $TREATMENT_PATH"
fi
if [ -n "$ANALYSIS_OUTPUT" ]; then
    echo "Analysis output:         $ANALYSIS_OUTPUT"
fi
echo ""

# Step 1: Filter and merge
echo "========================================================================"
echo "STEP 1: FILTERING AND MERGING"
echo "========================================================================"
if [ -n "$TREATMENT_PATH" ]; then
    python3 filter_merge_cleaned_data.py "$INPUT_CLEANED" "$OUTPUT_FINAL" "$TREATMENT_PATH"
else
    python3 filter_merge_cleaned_data.py "$INPUT_CLEANED" "$OUTPUT_FINAL"
fi

if [ $? -ne 0 ]; then
    echo "Error: Filtering and merging failed"
    exit 1
fi

echo ""
echo "Filtering and merging completed successfully!"
echo ""

# Step 2: Analyze pre-18 linking
echo "========================================================================"
echo "STEP 2: ANALYZING PRE-18 LINKING"
echo "========================================================================"
if [ -n "$ANALYSIS_OUTPUT" ]; then
    python3 analyze_pre18_linking.py "$INPUT_CLEANED" "$ANALYSIS_OUTPUT"
else
    python3 analyze_pre18_linking.py "$INPUT_CLEANED"
fi

if [ $? -ne 0 ]; then
    echo "Error: Pre-18 linking analysis failed"
    exit 1
fi

echo ""
echo "Pre-18 linking analysis completed successfully!"
echo ""

# Final summary
echo "========================================================================"
echo "PIPELINE COMPLETED SUCCESSFULLY!"
echo "========================================================================"
echo "Final output saved to: $OUTPUT_FINAL"
echo ""
