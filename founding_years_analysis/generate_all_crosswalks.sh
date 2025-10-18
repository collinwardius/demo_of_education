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
target_years=(1900 1910 1920 1930)

# Loop through each target year and generate crosswalk
for year in "${target_years[@]}"; do
    echo "Processing $year → 1940 crosswalk..."
    python3 create_county_crosswalk.py --target_year $year --base_year 1940 --overlap_threshold 70

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
