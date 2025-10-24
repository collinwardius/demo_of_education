import pandas as pd
import geopandas as gpd
from pathlib import Path

# Define paths
input_path = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv')
output_path = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/county_treatment_status.csv')

# Load the colleges with counties data
print("Loading colleges with counties...")
colleges_df = pd.read_csv(input_path)
print(f"Loaded {len(colleges_df)} colleges")


# Clean the data - remove any rows without county assignments
colleges_df = colleges_df.dropna(subset=['ICPSRST', 'ICPSRCTY'])
print(f"Colleges with county assignments: {len(colleges_df)}")

# Convert Founded_Year to numeric, handling any non-numeric values
colleges_df['Founded_Year'] = pd.to_numeric(colleges_df['Founded_Year'], errors='coerce')
print(f"Colleges with valid founding year: {colleges_df['Founded_Year'].notna().sum()}")

# Create county-level aggregation
print("\nAggregating at county level...")

# Group by county
county_groups = colleges_df.groupby(['ICPSRST', 'ICPSRCTY', 'ICPSRNAM', 'STATENAM'])

# Initialize list to store county-level data
county_data = []

for (icpsrst, icpsrcty, icpsrnam, statenam), group in county_groups:
    # Count colleges founded before 1900
    colleges_before_1900 = group[group['Founded_Year'] < 1900]
    has_college = 1 if len(colleges_before_1900) > 0 else 0

    # Count colleges founded between 1900 and 1940 (inclusive)
    colleges_1900_1940 = group[(group['Founded_Year'] >= 1900) & (group['Founded_Year'] <= 1940)]
    num_colleges_1900_1940 = len(colleges_1900_1940)

    # Treated: had zero colleges before 1900 AND exactly 1 college founded between 1900-1940
    treated = 1 if (has_college == 0 and num_colleges_1900_1940 == 1) else 0

    # Year and name (conditional on treated)
    year_founding = colleges_1900_1940.iloc[0]['Founded_Year'] if treated == 1 else None
    name = colleges_1900_1940.iloc[0]['College_Name'] if treated == 1 else None
    college_type = colleges_1900_1940.iloc[0]['College_Type'] if treated == 1 else None

    county_data.append({
        'ICPSRST': icpsrst,
        'ICPSRCTY': icpsrcty,
        'ICPSRNAM': icpsrnam,
        'STATENAM': statenam,
        'has_college': has_college,
        'treated': treated,
        'year_founding': year_founding,
        'name': name,
        'college_type': college_type
    })

# Create DataFrame
county_df = pd.DataFrame(county_data)

# Save to CSV
county_df.to_csv(output_path, index=False)
print(f"\nSaved county-level data to: {output_path}")

# Print summary statistics
print("\nSummary Statistics:")
print(f"Total counties with colleges: {len(county_df)}")
print(f"Counties with colleges before 1900: {county_df['has_college'].sum()}")
print(f"Counties treated (exactly 1 college 1900-1940): {county_df['treated'].sum()}")

# Show distribution of treated counties
print("\nFirst few treated counties:")
treated_counties = county_df[county_df['treated'] == 1]
print(treated_counties.head(10).to_string())
