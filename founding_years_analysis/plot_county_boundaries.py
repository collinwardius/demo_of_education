import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

# Define paths
shape_dir = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files')
output_dir = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures')

# Years to plot
years = [1900, 1910, 1920, 1930, 1940]

# Create figure with subfigures
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
axes = axes.flatten()

# Plot each year
for idx, year in enumerate(years):
    # Load shapefile
    shapefile_path = shape_dir / f'nhgis0003_shapefile_tl2008_us_county_{year}' / f'US_county_{year}_conflated.shp'
    gdf = gpd.read_file(shapefile_path)

    # Plot
    ax = axes[idx]
    gdf.plot(ax=ax, color='lightblue', edgecolor='black', linewidth=0.3)
    ax.set_title(f'US Counties - {year}', fontsize=14, fontweight='bold')
    ax.axis('off')

    print(f"Loaded {year}: {len(gdf)} counties")

# Remove the extra subplot
axes[-1].axis('off')

plt.tight_layout()

# Save figure
output_path = output_dir / 'historical_county_boundaries.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\nFigure saved to: {output_path}")

plt.show()
