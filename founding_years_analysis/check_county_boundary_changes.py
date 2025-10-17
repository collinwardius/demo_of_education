import geopandas as gpd
import pandas as pd
import numpy as np

# Load the 1900 and 1940 county shapefiles
print("Loading shapefiles...")
counties_1900 = gpd.read_file("/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files/nhgis0004_shapefile_tl2000_us_county_1900/US_county_1900.shp")
counties_1940 = gpd.read_file("/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files/nhgis0004_shapefile_tl2000_us_county_1940/US_county_1940.shp")

print(f"1900 counties: {len(counties_1900)}")
print(f"1940 counties: {len(counties_1940)}")

# Ensure both are in the same CRS
if counties_1900.crs != counties_1940.crs:
    print("Reprojecting to match CRS...")
    counties_1900 = counties_1900.to_crs(counties_1940.crs)

# Calculate areas for both time periods
print("\nCalculating areas...")
counties_1940['area_1940'] = counties_1940.geometry.area
counties_1900['area_1900'] = counties_1900.geometry.area

# Check what ID columns are available (GISJOIN is standard in NHGIS files)
print("\n1940 columns:", counties_1940.columns.tolist())
print("1900 columns:", counties_1900.columns.tolist())

# Determine which ID column to use (GISJOIN is most reliable)
# NHGIS typically uses GISJOIN, but we'll check for common alternatives
id_cols_to_try = ['GISJOIN', 'NHGISST', 'GEOID', 'FIPS', 'COUNTYICP']
id_col_1940 = None
id_col_1900 = None

for col in id_cols_to_try:
    if col in counties_1940.columns and id_col_1940 is None:
        id_col_1940 = col
    if col in counties_1900.columns and id_col_1900 is None:
        id_col_1900 = col

print(f"\nUsing ID column for 1940: {id_col_1940}")
print(f"Using ID column for 1900: {id_col_1900}")

# Perform spatial intersection
print("\nPerforming spatial intersection (this may take a while)...")
intersection = gpd.overlay(counties_1940, counties_1900, how='intersection', 
                          keep_geom_type=False)

# Calculate intersection areas
intersection['intersection_area'] = intersection.geometry.area

print(f"\nIntersection dataframe has {len(intersection)} pieces")
print("Intersection columns:", intersection.columns.tolist())

# After overlay, columns will have suffixes (_1 for 1940, _2 for 1900)
id_1940_in_intersection = id_col_1940 + '_1' if id_col_1940 + '_1' in intersection.columns else id_col_1940
id_1900_in_intersection = id_col_1900 + '_2' if id_col_1900 + '_2' in intersection.columns else id_col_1900

print(f"Using intersection columns: {id_1940_in_intersection} and {id_1900_in_intersection}")

# ANALYSIS 1: 1940 counties as reference (what % of each 1940 county came from one 1900 county?)
print("\nCalculating overlap percentages (1940 as reference)...")
overlap_1940_ref = []

for county_1940_id in counties_1940[id_col_1940].unique():
    # Get all intersection pieces for this 1940 county
    county_intersections = intersection[intersection[id_1940_in_intersection] == county_1940_id]
    
    if len(county_intersections) > 0:
        # Find the 1900 county with maximum overlap
        max_overlap = county_intersections['intersection_area'].max()
        
        # Get the total area of this 1940 county
        total_area_1940 = counties_1940[counties_1940[id_col_1940] == county_1940_id]['area_1940'].iloc[0]
        max_overlap_pct = (max_overlap / total_area_1940) * 100
        
        # Count how many 1900 counties this 1940 county overlaps with
        num_source_counties = county_intersections[id_1900_in_intersection].nunique()

        overlap_1940_ref.append({
            'county_1940_id': county_1940_id,
            'max_overlap_pct': max_overlap_pct,
            'num_source_counties': num_source_counties
        })

overlap_1940_df = pd.DataFrame(overlap_1940_ref)

# ANALYSIS 2: 1900 counties as reference (what % of each 1900 county went to one 1940 county?)
print("Calculating overlap percentages (1900 as reference)...")
overlap_1900_ref = []

for county_1900_id in counties_1900[id_col_1900].unique():
    # Get all intersection pieces for this 1900 county
    county_intersections = intersection[intersection[id_1900_in_intersection] == county_1900_id]
    
    if len(county_intersections) > 0:
        # Find the 1940 county with maximum overlap
        max_overlap = county_intersections['intersection_area'].max()
        
        # Get the total area of this 1900 county
        total_area_1900 = counties_1900[counties_1900[id_col_1900] == county_1900_id]['area_1900'].iloc[0]
        max_overlap_pct = (max_overlap / total_area_1900) * 100
        
        # Count how many 1940 counties this 1900 county became
        num_target_counties = county_intersections[id_1940_in_intersection].nunique()

        overlap_1900_ref.append({
            'county_1900_id': county_1900_id,
            'max_overlap_pct': max_overlap_pct,
            'num_target_counties': num_target_counties
        })

overlap_1900_df = pd.DataFrame(overlap_1900_ref)

# Calculate statistics for different thresholds
print("\n" + "="*60)
print("COUNTY BOUNDARY OVERLAP ANALYSIS (1900 vs 1940)")
print("="*60)

print("\n" + "-"*60)
print("ANALYSIS 1: 1940 Counties as Reference")
print("(What % of each 1940 county came from a single 1900 county?)")
print("-"*60)

total_1940 = len(overlap_1940_df)
threshold_99_1940 = (overlap_1940_df['max_overlap_pct'] >= 99).sum()
threshold_95_1940 = (overlap_1940_df['max_overlap_pct'] >= 95).sum()
threshold_90_1940 = (overlap_1940_df['max_overlap_pct'] >= 90).sum()
threshold_80_1940 = (overlap_1940_df['max_overlap_pct'] >= 80).sum()

print(f"\nTotal 1940 counties analyzed: {total_1940}")
print(f"\nCounties with 99%+ overlap with a single 1900 county: {threshold_99_1940} ({threshold_99_1940/total_1940*100:.1f}%)")
print(f"Counties with 95%+ overlap with a single 1900 county: {threshold_95_1940} ({threshold_95_1940/total_1940*100:.1f}%)")
print(f"Counties with 90%+ overlap with a single 1900 county: {threshold_90_1940} ({threshold_90_1940/total_1940*100:.1f}%)")
print(f"Counties with 80%+ overlap with a single 1900 county: {threshold_80_1940} ({threshold_80_1940/total_1940*100:.1f}%)")

# Additional statistics
merged_counties = (overlap_1940_df['num_source_counties'] > 1).sum()
print(f"\nCounties formed from multiple 1900 counties (mergers): {merged_counties} ({merged_counties/total_1940*100:.1f}%)")

print("\n" + "-"*60)
print("ANALYSIS 2: 1900 Counties as Reference")
print("(What % of each 1900 county went to a single 1940 county?)")
print("-"*60)

total_1900 = len(overlap_1900_df)
threshold_99_1900 = (overlap_1900_df['max_overlap_pct'] >= 99).sum()
threshold_95_1900 = (overlap_1900_df['max_overlap_pct'] >= 95).sum()
threshold_90_1900 = (overlap_1900_df['max_overlap_pct'] >= 90).sum()
threshold_80_1900 = (overlap_1900_df['max_overlap_pct'] >= 80).sum()

print(f"\nTotal 1900 counties analyzed: {total_1900}")
print(f"\nCounties with 99%+ overlap with a single 1940 county: {threshold_99_1900} ({threshold_99_1900/total_1900*100:.1f}%)")
print(f"Counties with 95%+ overlap with a single 1940 county: {threshold_95_1900} ({threshold_95_1900/total_1900*100:.1f}%)")
print(f"Counties with 90%+ overlap with a single 1940 county: {threshold_90_1900} ({threshold_90_1900/total_1900*100:.1f}%)")
print(f"Counties with 80%+ overlap with a single 1940 county: {threshold_80_1900} ({threshold_80_1900/total_1900*100:.1f}%)")

# Additional statistics
split_counties = (overlap_1900_df['num_target_counties'] > 1).sum()
print(f"\nCounties split into multiple 1940 counties: {split_counties} ({split_counties/total_1900*100:.1f}%)")

print("\n" + "="*60)
print("INTERPRETATION")
print("="*60)
print("If 1900 counties were SPLIT into multiple 1940 counties:")
print("  - Analysis 1 (1940 ref) would show HIGH overlap %")
print("  - Analysis 2 (1900 ref) would show LOW overlap %")
print(f"  - Actual splits detected: {split_counties}")
print("\nIf 1900 counties were MERGED into fewer 1940 counties:")
print("  - Analysis 1 (1940 ref) would show LOW overlap %")
print("  - Analysis 2 (1900 ref) would show HIGH overlap %")
print(f"  - Actual mergers detected: {merged_counties}")
print("\nIf boundaries stayed the same:")
print("  - Both analyses would show HIGH overlap (95%+)")
print("="*60)

# Optional: Identify specific counties with major changes
print("\n" + "="*60)
print("COUNTIES WITH MAJOR CHANGES (< 80% overlap)")
print("="*60)

major_changes_1940 = overlap_1940_df[overlap_1940_df['max_overlap_pct'] < 80]
print(f"\n1940 counties with <80% overlap (likely mergers): {len(major_changes_1940)}")
if len(major_changes_1940) > 0:
    print(major_changes_1940[['county_1940_id', 'max_overlap_pct', 'num_source_counties']].head(10))

major_changes_1900 = overlap_1900_df[overlap_1900_df['max_overlap_pct'] < 80]
print(f"\n1900 counties with <80% overlap (likely splits): {len(major_changes_1900)}")
if len(major_changes_1900) > 0:
    print(major_changes_1900[['county_1900_id', 'max_overlap_pct', 'num_target_counties']].head(10))

# Generate LaTeX table
print("\n" + "="*60)
print("GENERATING LATEX TABLE")
print("="*60)

latex_output = r"""\begin{table}[htbp]
\centering
\caption{County Boundary Stability Between 1900 and 1940}
\label{tab:county_overlap}
\begin{tabular}{lcc}
\hline\hline
& \multicolumn{2}{c}{Reference Period} \\
\cline{2-3}
Overlap Threshold & 1940 Counties & 1900 Counties \\
\hline
"""

# Add data rows
latex_output += f"Total Counties & {total_1940} & {total_1900} \\\\\n"
latex_output += "\\hline\n"
latex_output += f"99\\% or more overlap & {threshold_99_1940} ({threshold_99_1940/total_1940*100:.1f}\\%) & {threshold_99_1900} ({threshold_99_1900/total_1900*100:.1f}\\%) \\\\\n"
latex_output += f"95\\% or more overlap & {threshold_95_1940} ({threshold_95_1940/total_1940*100:.1f}\\%) & {threshold_95_1900} ({threshold_95_1900/total_1900*100:.1f}\\%) \\\\\n"
latex_output += f"90\\% or more overlap & {threshold_90_1940} ({threshold_90_1940/total_1940*100:.1f}\\%) & {threshold_90_1900} ({threshold_90_1900/total_1900*100:.1f}\\%) \\\\\n"
latex_output += f"80\\% or more overlap & {threshold_80_1940} ({threshold_80_1940/total_1940*100:.1f}\\%) & {threshold_80_1900} ({threshold_80_1900/total_1900*100:.1f}\\%) \\\\\n"

latex_output += r"""\hline\hline
\end{tabular}
\begin{tablenotes}
\small
\item Notes: The 1940 Counties column shows the percentage of 1940 counties that overlap with a single 1900 county at the specified threshold. The 1900 Counties column shows the percentage of 1900 counties that overlap with a single 1940 county.
\end{tablenotes}
\end{table}
"""

# Save to file
output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables/county_boundary_overlap.tex"
with open(output_path, 'w') as f:
    f.write(latex_output)

print(f"\nLaTeX table saved to: {output_path}")
print("\nTable preview:")
print(latex_output)