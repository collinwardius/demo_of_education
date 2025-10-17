#!/bin/bash

# Generate county crosswalks from multiple census years to 1900
# Using 70% overlap threshold

echo "========================================="
echo "Generating County Crosswalks"
echo "Base year: 1900"
echo "Overlap threshold: 70%"
echo "========================================="
echo ""

# Array of target years
target_years=(1910 1920 1930 1940)

# Loop through each target year and generate crosswalk
for year in "${target_years[@]}"; do
    echo "Processing $year → 1900 crosswalk..."
    python3 create_county_crosswalk.py --target_year $year --base_year 1900 --overlap_threshold 70

    if [ $? -eq 0 ]; then
        echo "✓ Successfully generated crosswalk for $year"
    else
        echo "✗ Error generating crosswalk for $year"
        exit 1
    fi
    echo ""
    echo "========================================="
    echo ""
done

echo "All crosswalks generated successfully!"
echo ""
echo "Output files created in:"
echo "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files/"
echo "  - county_crosswalk_1910_to_1900.csv"
echo "  - county_crosswalk_1920_to_1900.csv"
echo "  - county_crosswalk_1930_to_1900.csv"
echo "  - county_crosswalk_1940_to_1900.csv"
