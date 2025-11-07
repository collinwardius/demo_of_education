import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd

def create_junior_colleges_map():
    """Create a map showing junior colleges by founding period."""

    # Load data
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv"
    df = pd.read_csv(data_path)

    # Filter for junior colleges only
    df_junior = df[df['College_Type'] == 'Junior Colleges'].copy()

    # Clean founding years
    df_junior['founding_year'] = pd.to_numeric(df_junior['Founded_Year'], errors='coerce')
    df_junior = df_junior[df_junior['founding_year'].notna()].copy()

    # Clean latitude and longitude
    df_junior['latitude'] = pd.to_numeric(df_junior['latitude'], errors='coerce')
    df_junior['longitude'] = pd.to_numeric(df_junior['longitude'], errors='coerce')
    df_junior = df_junior[df_junior['latitude'].notna() & df_junior['longitude'].notna()].copy()

    # Categorize by founding period
    df_junior['period'] = 'Other'
    df_junior.loc[df_junior['founding_year'] <= 1900, 'period'] = 'Open as of 1900'
    df_junior.loc[(df_junior['founding_year'] > 1900) & (df_junior['founding_year'] <= 1940), 'period'] = 'Opened 1900-1940'

    # Filter for the two periods we want to plot
    df_plot = df_junior[df_junior['period'].isin(['Open as of 1900', 'Opened 1900-1940'])].copy()

    print(f"Total junior colleges with valid coordinates: {len(df_junior)}")
    print(f"Junior colleges open as of 1900: {len(df_plot[df_plot['period'] == 'Open as of 1900'])}")
    print(f"Junior colleges opened 1900-1940: {len(df_plot[df_plot['period'] == 'Opened 1900-1940'])}")

    # Create the map
    fig, ax = plt.subplots(figsize=(16, 10))

    # Load US states shapefile from naturalearth
    try:
        # Try to load from naturalearth data
        us_states = gpd.read_file('https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip')
        # Filter to continental US (exclude Alaska, Hawaii, territories)
        continental = us_states[~us_states['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'MP', 'AS'])]
        continental.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.5)
    except:
        print("Could not load US states shapefile, continuing without map background")

    # Define colors
    colors = {
        'Open as of 1900': '#d62728',  # red
        'Opened 1900-1940': '#1f77b4'  # blue
    }

    # Plot each period
    for period in ['Open as of 1900', 'Opened 1900-1940']:
        period_data = df_plot[df_plot['period'] == period]
        ax.scatter(period_data['longitude'], period_data['latitude'],
                  c=colors[period], label=period, alpha=0.7, s=50, edgecolors='black', linewidth=0.5, zorder=5)

    # Set map boundaries (continental US)
    ax.set_xlim(-125, -66)
    ax.set_ylim(24, 50)

    # Add labels and title
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title('Junior Colleges by Founding Period\n(Colleges existing as of 1944)',
                fontsize=16, fontweight='bold')

    # Add legend
    ax.legend(fontsize=11, loc='lower right', framealpha=0.9)

    # Set aspect ratio to approximate US map proportions
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()

    # Save the figure
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "junior_colleges_map_by_period.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\nMap saved to: {output_path}")

def create_junior_colleges_control_map():
    """Create a map showing junior colleges by control type (public vs private)."""

    # Load data
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv"
    df = pd.read_csv(data_path)

    # Filter for junior colleges only
    df_junior = df[df['College_Type'] == 'Junior Colleges'].copy()

    # Clean founding years
    df_junior['founding_year'] = pd.to_numeric(df_junior['Founded_Year'], errors='coerce')
    df_junior = df_junior[df_junior['founding_year'].notna()].copy()

    # Clean latitude and longitude
    df_junior['latitude'] = pd.to_numeric(df_junior['latitude'], errors='coerce')
    df_junior['longitude'] = pd.to_numeric(df_junior['longitude'], errors='coerce')
    df_junior = df_junior[df_junior['latitude'].notna() & df_junior['longitude'].notna()].copy()

    # Categorize by control type
    public_controls = ['City', 'Dist.', 'State', 'Local']
    df_junior['control_category'] = 'Private'
    df_junior.loc[df_junior['Control'].isin(public_controls), 'control_category'] = 'Public'

    print(f"\nTotal junior colleges with valid coordinates: {len(df_junior)}")
    print(f"Public junior colleges: {len(df_junior[df_junior['control_category'] == 'Public'])}")
    print(f"Private junior colleges: {len(df_junior[df_junior['control_category'] == 'Private'])}")

    # Show breakdown of control types
    print(f"\nControl type breakdown:")
    print(df_junior['Control'].value_counts())

    # Create the map
    fig, ax = plt.subplots(figsize=(16, 10))

    # Load US states shapefile
    try:
        us_states = gpd.read_file('https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip')
        # Filter to continental US (exclude Alaska, Hawaii, territories)
        continental = us_states[~us_states['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'MP', 'AS'])]
        continental.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.5)
    except:
        print("Could not load US states shapefile, continuing without map background")

    # Define colors
    colors = {
        'Public': '#2ca02c',   # green
        'Private': '#ff7f0e'   # orange
    }

    # Plot each control type
    for control_type in ['Private', 'Public']:  # Plot private first so public is on top
        control_data = df_junior[df_junior['control_category'] == control_type]
        ax.scatter(control_data['longitude'], control_data['latitude'],
                  c=colors[control_type], label=control_type, alpha=0.7, s=50,
                  edgecolors='black', linewidth=0.5, zorder=5)

    # Set map boundaries (continental US)
    ax.set_xlim(-125, -66)
    ax.set_ylim(24, 50)

    # Add labels and title
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title('Junior Colleges by Control Type\n(Colleges existing as of 1944)',
                fontsize=16, fontweight='bold')

    # Add legend
    ax.legend(fontsize=11, loc='lower right', framealpha=0.9)

    # Set aspect ratio to approximate US map proportions
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()

    # Save the figure
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "junior_colleges_map_by_control.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\nControl type map saved to: {output_path}")

if __name__ == "__main__":
    create_junior_colleges_map()
    create_junior_colleges_control_map()
