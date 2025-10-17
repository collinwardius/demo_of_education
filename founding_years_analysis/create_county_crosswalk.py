import geopandas as gpd
import pandas as pd
import argparse
import os

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Generate county crosswalk between two census years')
parser.add_argument('--target_year', type=int, required=True,
                    help='Target census year (e.g., 1910, 1920, 1930, 1940)')
parser.add_argument('--base_year', type=int, default=1900,
                    help='Base census year to map to (default: 1900)')
parser.add_argument('--overlap_threshold', type=float, default=70.0,
                    help='Minimum overlap percentage to include (default: 70)')
args = parser.parse_args()

target_year = args.target_year
base_year = args.base_year
overlap_threshold = args.overlap_threshold

# Validate years
valid_years = [1900, 1910, 1920, 1930, 1940]
if target_year not in valid_years:
    raise ValueError(f"target_year must be one of {valid_years}, got {target_year}")
if base_year not in valid_years:
    raise ValueError(f"base_year must be one of {valid_years}, got {base_year}")
if target_year <= base_year:
    raise ValueError(f"target_year ({target_year}) must be later than base_year ({base_year})")

print("="*80)
print(f"GENERATING CROSSWALK: {target_year} → {base_year}")
print(f"Overlap threshold: {overlap_threshold}%")
print("="*80)

# Construct file paths
base_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files"
base_year_path = os.path.join(base_dir, f"nhgis0004_shapefile_tl2000_us_county_{base_year}/US_county_{base_year}.shp")
target_year_path = os.path.join(base_dir, f"nhgis0004_shapefile_tl2000_us_county_{target_year}/US_county_{target_year}.shp")

# Validate that files exist
if not os.path.exists(base_year_path):
    raise FileNotFoundError(f"Base year shapefile not found: {base_year_path}")
if not os.path.exists(target_year_path):
    raise FileNotFoundError(f"Target year shapefile not found: {target_year_path}")

# Load the county shapefiles
print(f"\nLoading shapefiles...")
counties_base = gpd.read_file(base_year_path)
counties_target = gpd.read_file(target_year_path)

print(f"{base_year} counties: {len(counties_base)}")
print(f"{target_year} counties: {len(counties_target)}")

# Ensure both are in the same CRS
if counties_base.crs != counties_target.crs:
    print("Reprojecting to match CRS...")
    counties_target = counties_target.to_crs(counties_base.crs)

# Calculate areas for target year counties (the reference)
print(f"\nCalculating areas for {target_year} counties...")
counties_target[f'area_{target_year}'] = counties_target.geometry.area

# Perform spatial intersection
print("\nPerforming spatial intersection (this may take a while)...")
intersection = gpd.overlay(counties_target, counties_base, how='intersection', keep_geom_type=False)

# Calculate intersection areas
print("Calculating intersection areas...")
intersection['intersection_area'] = intersection.geometry.area

print(f"\nTotal intersection pieces: {len(intersection)}")

# Create the crosswalk dataset
print("\nBuilding crosswalk dataset...")
crosswalk_rows = []

for idx, row in intersection.iterrows():
    # Get the target year county's total area
    county_target_area = row[f'area_{target_year}']

    # Calculate what % of the target year county this intersection represents
    overlap_pct = (row['intersection_area'] / county_target_area) * 100

    crosswalk_rows.append({
        # Target year identifiers
        f'gisjoin_{target_year}': row['GISJOIN_1'],
        f'icpsrst_{target_year}': row['ICPSRST_1'],
        f'icpsrcty_{target_year}': row['ICPSRCTY_1'],
        f'county_name_{target_year}': row['ICPSRNAM_1'] if pd.notna(row['ICPSRNAM_1']) else row['NHGISNAM_1'],
        f'state_name_{target_year}': row['STATENAM_1'],

        # Overlap percentage
        'overlap_pct': overlap_pct,

        # Base year identifiers
        f'gisjoin_{base_year}': row['GISJOIN_2'],
        f'icpsrst_{base_year}': row['ICPSRST_2'],
        f'icpsrcty_{base_year}': row['ICPSRCTY_2'],
        f'county_name_{base_year}': row['ICPSRNAM_2'] if pd.notna(row['ICPSRNAM_2']) else row['NHGISNAM_2'],
        f'state_name_{base_year}': row['STATENAM_2']
    })

# Create DataFrame
crosswalk_df = pd.DataFrame(crosswalk_rows)

# Filter to only keep matches with more than the threshold overlap
# This ensures each target year county appears at most once (can't have 2+ sources with >70%)
print(f"\nBefore filtering: {len(crosswalk_df)} rows")
crosswalk_df = crosswalk_df[crosswalk_df['overlap_pct'] > overlap_threshold]
print(f"After filtering (overlap_pct > {overlap_threshold}%): {len(crosswalk_df)} rows")

# Verify that target year gisjoin is unique
gisjoin_target_col = f'gisjoin_{target_year}'
print(f"Unique {target_year} counties in filtered data: {crosswalk_df[gisjoin_target_col].nunique()}")
print(f"Total rows (should match if unique): {len(crosswalk_df)}")
if crosswalk_df[gisjoin_target_col].nunique() == len(crosswalk_df):
    print(f"✓ Confirmed: Each {target_year} county appears exactly once")
else:
    print(f"⚠ Warning: Some {target_year} counties appear multiple times")

# Sort by target year county, then by overlap percentage (descending)
crosswalk_df = crosswalk_df.sort_values([gisjoin_target_col, 'overlap_pct'], ascending=[True, False])

# Display summary statistics
print("\n" + "="*80)
print("CROSSWALK SUMMARY")
print("="*80)
gisjoin_base_col = f'gisjoin_{base_year}'
print(f"\nTotal rows in crosswalk: {len(crosswalk_df)}")
print(f"Unique {target_year} counties: {crosswalk_df[gisjoin_target_col].nunique()}")
print(f"Unique {base_year} counties: {crosswalk_df[gisjoin_base_col].nunique()}")

# Check how many target year counties map to multiple base year counties
multiple_sources = crosswalk_df.groupby(gisjoin_target_col).size()
print(f"\n{target_year} counties mapping to 1 source: {(multiple_sources == 1).sum()}")
print(f"{target_year} counties mapping to 2+ sources: {(multiple_sources > 1).sum()}")
print(f"Max sources for any {target_year} county: {multiple_sources.max()}")

# Show some examples
print("\n" + "="*80)
print(f"EXAMPLE: {target_year} counties with multiple {base_year} sources")
print("="*80)
multi_source_counties = crosswalk_df[crosswalk_df.groupby(gisjoin_target_col)[gisjoin_target_col].transform('size') > 1]
if len(multi_source_counties) > 0:
    example_county = multi_source_counties[gisjoin_target_col].iloc[0]
    example_data = crosswalk_df[crosswalk_df[gisjoin_target_col] == example_county]
    county_name_col = f'county_name_{target_year}'
    state_name_col = f'state_name_{target_year}'
    base_county_name_col = f'county_name_{base_year}'
    base_state_name_col = f'state_name_{base_year}'
    print(f"\nExample: {example_data.iloc[0][county_name_col]}, {example_data.iloc[0][state_name_col]} ({target_year})")
    print(f"Formed from {len(example_data)} {base_year} county/counties:\n")
    for _, ex_row in example_data.iterrows():
        print(f"  - {ex_row[base_county_name_col]}, {ex_row[base_state_name_col]} ({ex_row['overlap_pct']:.2f}%)")
else:
    print(f"\nNo {target_year} counties with multiple {base_year} sources (all have single dominant source)")

# Verify that percentages sum to ~100% for each target year county
print("\n" + "="*80)
print("VALIDATION: Checking overlap percentages sum to ~100%")
print("="*80)
overlap_sums = crosswalk_df.groupby(gisjoin_target_col)['overlap_pct'].sum()
print(f"\nMean sum of overlaps per {target_year} county: {overlap_sums.mean():.2f}%")
print(f"Median sum of overlaps per {target_year} county: {overlap_sums.median():.2f}%")
print(f"Counties with sum < 95%: {(overlap_sums < 95).sum()}")
print(f"Counties with sum > 105%: {(overlap_sums > 105).sum()}")

# Save the crosswalk
output_path = os.path.join(base_dir, f"county_crosswalk_{target_year}_to_{base_year}.csv")
crosswalk_df.to_csv(output_path, index=False)

print("\n" + "="*80)
print(f"Crosswalk saved to: {output_path}")
print("="*80)

# Display first few rows
print("\nFirst 20 rows of crosswalk:")
print(crosswalk_df.head(20).to_string())
