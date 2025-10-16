import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

# Define paths
shape_dir = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files')
colleges_path = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv')
output_dir = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures')

# Load 1940 county shapefile (only needed columns)
print("Loading 1940 county boundaries...")
shapefile_path = shape_dir / 'nhgis0003_shapefile_tl2008_us_county_1940' / 'US_county_1940_conflated.shp'
counties_gdf = gpd.read_file(shapefile_path, columns=['ICPSRST', 'ICPSRCTY', 'STATENAM', 'ICPSRNAM', 'geometry'])
print(f"Loaded {len(counties_gdf)} counties")

# Simplify geometries for faster plotting
print("Simplifying geometries...")
counties_gdf['geometry'] = counties_gdf['geometry'].simplify(tolerance=500)

# Load colleges with county assignments
print("Loading colleges with county assignments...")
colleges_df = pd.read_csv(colleges_path)

# Count colleges per county (drop NA values)
print("Counting colleges per county...")
colleges_clean = colleges_df.dropna(subset=['ICPSRST', 'ICPSRCTY'])
college_counts = colleges_clean.groupby(['ICPSRST', 'ICPSRCTY']).size().reset_index(name='college_count')
print(f"Counties with colleges: {len(college_counts)}")
print(f"Max colleges in a county: {college_counts['college_count'].max()}")

# Convert data types to match before merging
college_counts['ICPSRST'] = college_counts['ICPSRST'].astype(int)
college_counts['ICPSRCTY'] = college_counts['ICPSRCTY'].astype(int)
counties_gdf['ICPSRST'] = counties_gdf['ICPSRST'].astype(int)
counties_gdf['ICPSRCTY'] = counties_gdf['ICPSRCTY'].astype(int)

# Merge counts with county shapefile
print("Merging data...")
counties_with_counts = counties_gdf.merge(
    college_counts,
    on=['ICPSRST', 'ICPSRCTY'],
    how='left'
)

# Fill NaN (counties with no colleges) with 0
counties_with_counts['college_count'] = counties_with_counts['college_count'].fillna(0)

print(f"\nSummary:")
print(f"  Counties with data: {len(counties_with_counts)}")
print(f"  Counties with colleges: {(counties_with_counts['college_count'] > 0).sum()}")
print(f"  Max colleges: {counties_with_counts['college_count'].max()}")

# Create figure
print("\nCreating plot...")
fig, ax = plt.subplots(1, 1, figsize=(20, 12))

# Plot choropleth with log scale for better visualization
counties_with_counts['college_count_plot'] = counties_with_counts['college_count'].replace(0, np.nan)

counties_with_counts.plot(
    column='college_count',
    ax=ax,
    legend=True,
    cmap='YlOrRd',
    edgecolor='gray',
    linewidth=0.05,
    vmin=0,
    vmax=35,
    legend_kwds={
        'label': 'Number of Colleges',
        'orientation': 'vertical',
        'shrink': 0.5
    },
    missing_kwds={'color': 'lightgray'}
)

ax.set_title('College Intensity by County (1940 Boundaries)', fontsize=16, fontweight='bold')
ax.axis('off')

plt.tight_layout()

# Save figure
output_path = output_dir / 'college_intensity_heatmap_1940.png'
print(f"Saving to {output_path}...")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Done!")

# Top 10 counties
top_counties = counties_with_counts.nlargest(10, 'college_count')[['STATENAM', 'ICPSRNAM', 'college_count']]
print("\nTop 10 counties by college count:")
print(top_counties.to_string(index=False))
