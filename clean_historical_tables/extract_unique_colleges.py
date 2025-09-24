#!/usr/bin/env python3
"""
Script to extract unique college names and their associated states from the appended dataset.
"""

import pandas as pd
import os
from pathlib import Path

def extract_unique_colleges(input_file: str, output_folder: str):
    """
    Extract unique college names with their states from the appended dataset.
    
    Args:
        input_file: Path to the appended CSV file
        output_folder: Folder to save the output files
    """
    
    print(f"Reading data from: {input_file}")
    
    # Read the appended dataset
    try:
        df = pd.read_csv(input_file)
        print(f"Dataset loaded successfully. Shape: {df.shape}")
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Check if required columns exist
    required_columns = ['college', 'state']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Remove rows where college name is missing
    df_clean = df.dropna(subset=['college']).copy()
    print(f"Rows with college data: {len(df_clean):,}")
    
    # Extract unique colleges with their state information, sorted by state then college
    unique_colleges = df_clean.groupby(['state', 'college']).size().reset_index(name='record_count')
    unique_colleges = unique_colleges.sort_values(['state', 'college'])
    
    print(f"Unique college-state combinations: {len(unique_colleges):,}")
    
    # Create summary statistics
    colleges_by_state = unique_colleges.groupby('state').size().reset_index(name='college_count')
    colleges_by_state = colleges_by_state.sort_values('college_count', ascending=False)
    
    print(f"States represented: {len(colleges_by_state):,}")
    
    # Save results
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)
    
    # 1. Unique colleges with states (sorted by state, then college)
    colleges_output = output_folder / "unique_colleges_by_state.csv"
    unique_colleges.to_csv(colleges_output, index=False)
    print(f"Saved unique colleges by state to: {colleges_output}")
    
    # Skip creating colleges_by_state_summary.csv file
    
    # Skip creating college_extraction_report.md
    
    return unique_colleges, colleges_by_state

def create_college_report(unique_colleges, colleges_by_state, output_folder):
    """Create a markdown report summarizing the college data."""
    
    report_path = output_folder / "college_extraction_report.md"
    
    markdown_content = []
    markdown_content.append("# College Extraction Report")
    markdown_content.append("")
    markdown_content.append(f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    markdown_content.append("")
    
    # Summary statistics
    markdown_content.append("## Summary Statistics")
    markdown_content.append("")
    markdown_content.append(f"- **Total unique college-state combinations:** {len(unique_colleges):,}")
    markdown_content.append(f"- **States represented:** {len(colleges_by_state):,}")
    markdown_content.append("")
    
    # Top states by number of colleges
    markdown_content.append("## States by Number of Colleges")
    markdown_content.append("")
    markdown_content.append("| Rank | State | Number of Colleges |")
    markdown_content.append("|------|-------|-------------------|")
    
    for i, (_, row) in enumerate(colleges_by_state.iterrows(), 1):
        markdown_content.append(f"| {i} | {row['state']} | {row['college_count']:,} |")
    
    markdown_content.append("")
    
    # Sample of colleges by state
    markdown_content.append("## Sample of Colleges by State (First 20)")
    markdown_content.append("")
    markdown_content.append("| State | College Name | Records |")
    markdown_content.append("|-------|--------------|---------|")
    
    for _, row in unique_colleges.head(20).iterrows():
        state = row['state']
        college = row['college']
        records = row['record_count']
        markdown_content.append(f"| {state} | {college} | {records:,} |")
    
    markdown_content.append("")
    
    # Data files generated
    markdown_content.append("## Generated Files")
    markdown_content.append("")
    markdown_content.append("1. **unique_colleges_by_state.csv** - All unique college-state combinations sorted by state then college name")
    markdown_content.append("2. **college_extraction_report.md** - This report")
    markdown_content.append("")
    
    # Write report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))
    
    print(f"College extraction report saved to: {report_path}")

def main():
    """Main function to run the college extraction."""
    
    # Define paths
    input_file = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/cleaned_appended_college_data.csv"
    output_folder = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data"
    
    print("Starting college extraction...")
    print(f"Input file: {input_file}")
    print(f"Output folder: {output_folder}")
    print("-" * 50)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return
    
    # Extract unique colleges
    result = extract_unique_colleges(input_file, output_folder)
    
    if result:
        unique_colleges, colleges_by_state = result
        print("-" * 50)
        print("Extraction completed successfully!")
        print(f"Results saved to: {output_folder}")
    else:
        print("Extraction failed!")

if __name__ == "__main__":
    main()