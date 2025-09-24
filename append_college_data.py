#!/usr/bin/env python3
"""
Script to append historical college data CSV files together.
Handles different column naming conventions across the files.
"""

import pandas as pd
import os

def append_college_data():
    """Append the four college blue book CSV files together."""

    # File paths
    base_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/"
    files = [
        f"{base_path}college_blue_book_data (1).csv",
        f"{base_path}college_blue_book_data (2).csv",
        f"{base_path}college_blue_book_data (3).csv",
        f"{base_path}college_blue_book_data (4).csv"
    ]

    # Column mapping to standardize headers
    column_mappings = {
        'College_Type': 'College_Type',
        'Category': 'College_Type',
        'College Type': 'College_Type',
        'College_Name': 'College_Name',
        'Name': 'College_Name',
        'College Name': 'College_Name',
        'City': 'City',
        'Location': 'City',
        'Map_Location': 'Map_Location',
        'Map': 'Map_Location',
        'Census_1940': 'Census_1940',
        'Census 1940': 'Census_1940',
        'Founded_Year': 'Founded_Year',
        'Founded Year': 'Founded_Year',
        'Student_Capacity': 'Student_Capacity',
        'Capacity': 'Student_Capacity',
        'Enrollment_M': 'Male_Enrollment',
        'Student_Enrollment_M': 'Male_Enrollment',
        'Male_Enrollment': 'Male_Enrollment',
        'Male Enrollment': 'Male_Enrollment',
        'Enrollment_W': 'Female_Enrollment',
        'Student_Enrollment_W': 'Female_Enrollment',
        'Female_Enrollment': 'Female_Enrollment',
        'Female Enrollment': 'Female_Enrollment',
        'Recognized_By': 'Recognized_By',
        'Recognized By': 'Recognized_By'
    }

    dataframes = []

    for i, file_path in enumerate(files, 1):
        print(f"Processing file {i}: {os.path.basename(file_path)}")

        try:
            # Read CSV with error handling for malformed lines
            df = pd.read_csv(file_path, on_bad_lines='skip')
        except Exception as e:
            print(f"  - Error reading {file_path}: {e}")
            print("  - Trying with different options...")
            try:
                # Try with quoting and error handling
                df = pd.read_csv(file_path, quoting=1, on_bad_lines='skip')
            except Exception as e2:
                print(f"  - Still failed: {e2}")
                continue

        # Rename columns to standardize
        df = df.rename(columns=column_mappings)

        # Add source file column
        df['Source_File'] = f"college_blue_book_data ({i}).csv"

        dataframes.append(df)
        print(f"  - Loaded {len(df)} rows")

    # Concatenate all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True, sort=False)

    # Reorder columns for consistency
    standard_columns = [
        'State', 'College_Type', 'Number', 'College_Name', 'Gender', 'City',
        'Map_Location', 'Census_1940', 'Founded_Year', 'Control',
        'Student_Capacity', 'Male_Enrollment', 'Female_Enrollment',
        'Recognized_By', 'Source_File'
    ]

    # Keep only columns that exist in the combined dataframe
    available_columns = [col for col in standard_columns if col in combined_df.columns]
    combined_df = combined_df[available_columns]

    # Save combined data to the original data directory
    output_path = f"{base_path}combined_college_blue_book_data.csv"
    combined_df.to_csv(output_path, index=False)

    print(f"\nCombined data saved to: {output_path}")
    print(f"Total rows: {len(combined_df)}")
    print(f"Total columns: {len(combined_df.columns)}")
    print(f"Columns: {list(combined_df.columns)}")

    # Data quality analysis
    print("\n=== DATA QUALITY ANALYSIS ===")

    # Check for duplicates
    duplicates = combined_df.duplicated()
    print(f"Duplicate rows: {duplicates.sum()}")

    # Check for missing values in key columns
    key_columns = ['State', 'College_Name', 'Founded_Year']
    for col in key_columns:
        if col in combined_df.columns:
            missing = combined_df[col].isna().sum()
            print(f"Missing {col}: {missing} ({missing/len(combined_df)*100:.1f}%)")

    # Check for potential duplicate colleges (same name, different rows)
    if 'College_Name' in combined_df.columns:
        name_counts = combined_df['College_Name'].value_counts()
        potential_dups = name_counts[name_counts > 1]
        if len(potential_dups) > 0:
            print(f"Colleges with duplicate names: {len(potential_dups)}")
            print("Top duplicates:")
            for name, count in potential_dups.head().items():
                print(f"  {name}: {count} entries")

    # Check enrollment data quality
    enrollment_cols = ['Male_Enrollment', 'Female_Enrollment']
    for col in enrollment_cols:
        if col in combined_df.columns:
            non_numeric = pd.to_numeric(combined_df[col], errors='coerce').isna().sum()
            total_missing = combined_df[col].isna().sum()
            print(f"{col} - Missing: {total_missing}, Non-numeric: {non_numeric}")

    return combined_df

if __name__ == "__main__":
    combined_data = append_college_data()