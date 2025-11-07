#!/bin/bash
#SBATCH --job-name=trend_college
#SBATCH --output=state_data_%j.log
#SBATCH --error=state_data_%j.err
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=2:00:00
#SBATCH --account=csd992
#SBATCH --constraint=lustre
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=cjwardius@gmail.com

# Trend College Attainment Analysis - SLURM Submission Script
#
# Usage:
# sbatch submit_trend_analysis.sh
#
# This script runs trend_college_attainment.py on the linked census data
# and generates output figures in the specified directory.

echo "========================================================================"
echo "SLURM JOB INFORMATION"
echo "========================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Job Name: $SLURM_JOB_NAME"
echo "Node: $SLURM_NODELIST"
echo "Start Time: $(date)"
echo "Working Directory: $(pwd)"
echo ""

# Load required modules IN ORDER (cpu first, then anaconda)
module purge
module load cpu/0.15.4
module load anaconda3/2020.11

# Verify pandas is available
echo "Testing pandas import..."
python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to import pandas"
    exit 1
fi

echo "Pandas imported successfully"
echo ""

# Define input and output paths
INPUT_DATA="/home/cwardius/data/1940_full_count.csv"
OUTPUT_DIR="/home/cwardius/data"

echo "========================================================================"
echo "SCRIPT PARAMETERS"
echo "========================================================================"
echo "Input Data: $INPUT_DATA"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the trend analysis script
echo "========================================================================"
echo "RUNNING TREND ANALYSIS"
echo "========================================================================"
echo "Command: python state_level_attainment.py $INPUT_DATA $OUTPUT_DIR"
echo ""

python state_level_attainment.py "$INPUT_DATA" --output "$OUTPUT_DIR"

EXIT_CODE=$?

echo ""
echo "========================================================================"
echo "JOB COMPLETION"
echo "========================================================================"
echo "Exit Code: $EXIT_CODE"
echo "End Time: $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Code completed successfully"
else
    echo "ERROR: Code failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
