import geopandas as gpd
import pandas as pd
from pathlib import Path

# Define paths
shape_dir = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files')
colleges_path = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_coordinates.csv')
output_path = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv')

# Load 1940 county shapefile
print("Loading 1940 county boundaries...")
shapefile_path = shape_dir / 'nhgis0003_shapefile_tl2008_us_county_1940' / 'US_county_1940_conflated.shp'
counties_gdf = gpd.read_file(shapefile_path)
print(f"Loaded {len(counties_gdf)} counties")

# Load colleges
print("\nLoading colleges with coordinates...")
colleges_df = pd.read_csv(colleges_path)
print(f"Loaded {len(colleges_df)} colleges")

# Create GeoDataFrame from colleges (filter out any missing coordinates)
colleges_df_clean = colleges_df.dropna(subset=['latitude', 'longitude'])
print(f"Colleges with valid coordinates: {len(colleges_df_clean)}")

colleges_gdf = gpd.GeoDataFrame(
    colleges_df_clean,
    geometry=gpd.points_from_xy(colleges_df_clean.longitude, colleges_df_clean.latitude),
    crs='EPSG:4326'  # WGS84
)

# Reproject colleges to match county shapefile CRS
print("\nReprojecting coordinates...")
colleges_gdf = colleges_gdf.to_crs(counties_gdf.crs)

# Spatial join to find which county each college is in
print("\nPerforming spatial join...")
colleges_with_counties = gpd.sjoin(
    colleges_gdf,
    counties_gdf[['ICPSRST', 'ICPSRCTY', 'ICPSRNAM', 'STATENAM', 'STATE', 'COUNTY', 'geometry']],
    how='left',
    predicate='within'
)

# Drop geometry column for CSV output
colleges_with_counties_df = colleges_with_counties.drop(columns=['geometry', 'index_right'])

# Save to CSV
colleges_with_counties_df.to_csv(output_path, index=False)
print(f"\nSaved results to: {output_path}")

# Print summary statistics
matched = colleges_with_counties_df['ICPSRCTY'].notna().sum()
unmatched = colleges_with_counties_df['ICPSRCTY'].isna().sum()
print(f"\nMatching summary:")
print(f"  Colleges matched to counties: {matched}")
print(f"  Colleges not matched: {unmatched}")

# Show a few examples
print("\nFirst few colleges with county assignments:")
print(colleges_with_counties_df[['College_Name', 'City', 'State', 'STATENAM', 'ICPSRNAM']].head(10))
