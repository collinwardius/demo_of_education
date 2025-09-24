import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap
import os
import urllib.request
import zipfile

def load_and_process_data():
    """Load and process the Bowman 1962 college enrollment data"""
    df = pd.read_csv('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/college_population_table_bowman_1962.csv')

    # Clean the data
    df = df[df['State'] != 'D. of C.']  # Remove DC as requested

    # Convert enrollment per capita to numeric (inverse of populations per student) and scale by 100
    df['Enrollment_per_capita_1958'] = (1 / df['Populations_per_Student_1958']) * 100

    # Handle 1890 data - some states have missing data (empty cells)
    df['Populations_per_Student_1890'] = pd.to_numeric(df['Populations_per_Student_1890'], errors='coerce')
    df['Enrollment_per_capita_1890'] = (1 / df['Populations_per_Student_1890']) * 100

    # Create state name mapping for consistency
    state_mapping = {
        'N. Dakota': 'North Dakota',
        'S. Dakota': 'South Dakota',
        'N. Mexico': 'New Mexico',
        'W. Virginia': 'West Virginia',
        'N. H.': 'New Hampshire',
        'N. Carolina': 'North Carolina',
        'S. Carolina': 'South Carolina'
    }

    df['State_Full'] = df['State'].replace(state_mapping)

    return df

def create_bar_charts():
    """Create side-by-side bar charts of college enrollment per capita for 1890 and 1958"""

    # Load data
    df = load_and_process_data()

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 12))

    # Sort data for better visualization
    df_1958 = df.sort_values('Enrollment_per_capita_1958', ascending=True)
    df_1890 = df.dropna(subset=['Enrollment_per_capita_1890']).sort_values('Enrollment_per_capita_1890', ascending=True)

    # Define color scheme
    colors_1958 = plt.cm.Blues(np.linspace(0.3, 0.9, len(df_1958)))
    colors_1890 = plt.cm.Reds(np.linspace(0.3, 0.9, len(df_1890)))

    # Plot 1890 data
    bars1 = ax1.barh(range(len(df_1890)), df_1890['Enrollment_per_capita_1890'],
                     color=colors_1890, edgecolor='black', linewidth=0.5)
    ax1.set_yticks(range(len(df_1890)))
    ax1.set_yticklabels(df_1890['State_Full'], fontsize=8)
    ax1.set_xlabel('Enrollment per Capita', fontsize=12)
    ax1.set_title('College Enrollment per Capita by State - 1890', fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)

    # Plot 1958 data
    bars2 = ax2.barh(range(len(df_1958)), df_1958['Enrollment_per_capita_1958'],
                     color=colors_1958, edgecolor='black', linewidth=0.5)
    ax2.set_yticks(range(len(df_1958)))
    ax2.set_yticklabels(df_1958['State_Full'], fontsize=8)
    ax2.set_xlabel('Enrollment per Capita', fontsize=12)
    ax2.set_title('College Enrollment per Capita by State - 1958', fontsize=14, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)

    # Add overall title
    fig.suptitle('Historical College Enrollment per Capita in the United States\n(Bowman 1962 Data)',
                 fontsize=16, fontweight='bold', y=0.95)

    # Adjust layout
    plt.tight_layout()

    # Create output directory if it doesn't exist
    output_dir = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures'
    os.makedirs(output_dir, exist_ok=True)

    # Save the plot
    output_path = os.path.join(output_dir, 'enrollments_bowman_1962.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"Charts saved to: {output_path}")

    # Print some statistics
    print("\n1958 Enrollment Statistics:")
    print(f"States with data: {df['Enrollment_per_capita_1958'].notna().sum()}")
    max_1958_idx = df['Enrollment_per_capita_1958'].idxmax()
    min_1958_idx = df['Enrollment_per_capita_1958'].idxmin()
    print(f"Highest enrollment per capita: {df.loc[max_1958_idx, 'State']} ({df.loc[max_1958_idx, 'Enrollment_per_capita_1958']:.6f})")
    print(f"Lowest enrollment per capita: {df.loc[min_1958_idx, 'State']} ({df.loc[min_1958_idx, 'Enrollment_per_capita_1958']:.6f})")

    print("\n1890 Enrollment Statistics:")
    valid_1890 = df.dropna(subset=['Enrollment_per_capita_1890'])
    print(f"States with data: {len(valid_1890)}")
    if not valid_1890.empty:
        max_1890_idx = valid_1890['Enrollment_per_capita_1890'].idxmax()
        min_1890_idx = valid_1890['Enrollment_per_capita_1890'].idxmin()
        print(f"Highest enrollment per capita: {valid_1890.loc[max_1890_idx, 'State']} ({valid_1890.loc[max_1890_idx, 'Enrollment_per_capita_1890']:.6f})")
        print(f"Lowest enrollment per capita: {valid_1890.loc[min_1890_idx, 'State']} ({valid_1890.loc[min_1890_idx, 'Enrollment_per_capita_1890']:.6f})")

def create_simple_map_visualization():
    """Create a simple grid-based visualization as an alternative to geographic maps"""

    # Load data
    df = load_and_process_data()

    # Create figure with side-by-side plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))

    # Create scatter plots with state names as markers
    # 1890 plot
    df_1890 = df.dropna(subset=['Enrollment_per_capita_1890'])
    scatter1 = ax1.scatter(range(len(df_1890)), df_1890['Enrollment_per_capita_1890'],
                          c=df_1890['Enrollment_per_capita_1890'], cmap='Reds',
                          s=100, alpha=0.7, edgecolors='black')

    # Add state labels
    for i, (idx, row) in enumerate(df_1890.iterrows()):
        ax1.annotate(row['State'], (i, row['Enrollment_per_capita_1890']),
                    xytext=(5, 5), textcoords='offset points', fontsize=6, rotation=45)

    ax1.set_title('College Enrollment per Capita - 1890', fontsize=14, fontweight='bold')
    ax1.set_xlabel('States (ordered by data availability)', fontsize=12)
    ax1.set_ylabel('Enrollment per Capita', fontsize=12)
    ax1.grid(True, alpha=0.3)
    plt.colorbar(scatter1, ax=ax1, label='Enrollment per Capita')

    # 1958 plot
    scatter2 = ax2.scatter(range(len(df)), df['Enrollment_per_capita_1958'],
                          c=df['Enrollment_per_capita_1958'], cmap='Blues',
                          s=100, alpha=0.7, edgecolors='black')

    # Add state labels
    for i, (idx, row) in enumerate(df.iterrows()):
        ax2.annotate(row['State'], (i, row['Enrollment_per_capita_1958']),
                    xytext=(5, 5), textcoords='offset points', fontsize=6, rotation=45)

    ax2.set_title('College Enrollment per Capita - 1958', fontsize=14, fontweight='bold')
    ax2.set_xlabel('States (ordered by rank)', fontsize=12)
    ax2.set_ylabel('Enrollment per Capita', fontsize=12)
    ax2.grid(True, alpha=0.3)
    plt.colorbar(scatter2, ax=ax2, label='Enrollment per Capita')

    # Add overall title
    fig.suptitle('Historical College Enrollment per Capita in the United States\n(Bowman 1962 Data - Scatter Plot Visualization)',
                 fontsize=16, fontweight='bold', y=0.95)

    # Adjust layout
    plt.tight_layout()

    # Create output directory if it doesn't exist
    output_dir = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures'
    os.makedirs(output_dir, exist_ok=True)

    # Save the plot
    output_path = os.path.join(output_dir, 'enrollments_bowman_1962.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"Visualization saved to: {output_path}")

def download_us_states_shapefile():
    """Download US states shapefile if not already present"""
    shapefile_dir = "us_states_shapefile"
    shapefile_path = os.path.join(shapefile_dir, "cb_2018_us_state_500k.shp")

    if not os.path.exists(shapefile_path):
        print("Downloading US states shapefile...")
        os.makedirs(shapefile_dir, exist_ok=True)

        # Download from US Census Bureau
        url = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_500k.zip"
        zip_path = os.path.join(shapefile_dir, "states.zip")

        urllib.request.urlretrieve(url, zip_path)

        # Extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(shapefile_dir)

        # Remove the zip file
        os.remove(zip_path)
        print("Shapefile downloaded and extracted successfully.")

    return shapefile_path

def create_geographic_maps():
    """Create side-by-side geographic maps of college enrollment per capita for 1890 and 1958"""

    # Load data
    df = load_and_process_data()

    # Download shapefile if needed
    shapefile_path = download_us_states_shapefile()

    # Load US states shapefile
    us_states = gpd.read_file(shapefile_path)

    # Filter out territories, Alaska, and Hawaii - keep only continental US states
    us_states = us_states[~us_states['STUSPS'].isin(['PR', 'VI', 'GU', 'MP', 'AS', 'AK', 'HI'])]

    # Create state name mapping
    state_name_mapping = {
        'N. Dakota': 'ND', 'S. Dakota': 'SD', 'New Mexico': 'NM',
        'W. Virginia': 'WV', 'N. H.': 'NH', 'N. Carolina': 'NC',
        'S. Carolina': 'SC', 'Oklahoma': 'OK', 'Arizona': 'AZ',
        'Utah': 'UT', 'Kansas': 'KS', 'California': 'CA',
        'Wyoming': 'WY', 'Connecticut': 'CT', 'New York': 'NY',
        'Idaho': 'ID', 'Montana': 'MT', 'Nebraska': 'NE',
        'Washington': 'WA', 'Massachusetts': 'MA', 'Oregon': 'OR',
        'Texas': 'TX', 'New Jersey': 'NJ', 'Minnesota': 'MN',
        'Michigan': 'MI', 'Colorado': 'CO', 'Iowa': 'IA',
        'Louisiana': 'LA', 'Illinois': 'IL', 'Wisconsin': 'WI',
        'Indiana': 'IN', 'Ohio': 'OH', 'Arkansas': 'AR',
        'Mississippi': 'MS', 'Nevada': 'NV', 'Pennsylvania': 'PA',
        'Alabama': 'AL', 'Florida': 'FL', 'Kentucky': 'KY',
        'Vermont': 'VT', 'Tennessee': 'TN', 'Missouri': 'MO',
        'Maryland': 'MD', 'Georgia': 'GA', 'Rhode Island': 'RI',
        'Delaware': 'DE', 'Maine': 'ME', 'Virginia': 'VA'
    }

    # Add state codes to dataframe
    df['State_Code'] = df['State'].map(state_name_mapping)

    # Merge data with shapefile
    merged_1958 = us_states.merge(df[['State_Code', 'Enrollment_per_capita_1958']],
                                  left_on='STUSPS', right_on='State_Code', how='left')
    merged_1890 = us_states.merge(df[['State_Code', 'Enrollment_per_capita_1890']],
                                  left_on='STUSPS', right_on='State_Code', how='left')

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    # Define color scheme - using consistent scale for both maps
    all_values = pd.concat([df['Enrollment_per_capita_1890'].dropna(),
                           df['Enrollment_per_capita_1958']]).values
    vmin, vmax = all_values.min(), all_values.max()

    # Plot 1890 map
    merged_1890.plot(column='Enrollment_per_capita_1890',
                     cmap='Reds',
                     legend=True,
                     ax=ax1,
                     missing_kwds={'color': 'lightgray'},
                     edgecolor='black',
                     linewidth=0.5,
                     vmin=vmin,
                     vmax=vmax,
                     legend_kwds={'label': 'Enrollment per Capita', 'shrink': 0.8})
    ax1.set_title('College Enrollment per Capita by State - 1890', fontsize=16, fontweight='bold')
    ax1.axis('off')

    # Plot 1958 map
    merged_1958.plot(column='Enrollment_per_capita_1958',
                     cmap='Blues',
                     legend=True,
                     ax=ax2,
                     missing_kwds={'color': 'lightgray'},
                     edgecolor='black',
                     linewidth=0.5,
                     vmin=vmin,
                     vmax=vmax,
                     legend_kwds={'label': 'Enrollment per Capita', 'shrink': 0.8})
    ax2.set_title('College Enrollment per Capita by State - 1958', fontsize=16, fontweight='bold')
    ax2.axis('off')

    # Add overall title
    fig.suptitle('Historical College Enrollment per Capita in the United States\n(Bowman 1962 Data)',
                 fontsize=18, fontweight='bold', y=0.95)

    # Adjust layout
    plt.tight_layout()

    # Create output directory if it doesn't exist
    output_dir = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures'
    os.makedirs(output_dir, exist_ok=True)

    # Save the plot
    output_path = os.path.join(output_dir, 'enrollments_bowman_1962.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"Geographic maps saved to: {output_path}")

    # Print some statistics
    print("\n1958 Enrollment Statistics:")
    print(f"States with data: {df['Enrollment_per_capita_1958'].notna().sum()}")
    max_1958_idx = df['Enrollment_per_capita_1958'].idxmax()
    min_1958_idx = df['Enrollment_per_capita_1958'].idxmin()
    print(f"Highest enrollment per capita: {df.loc[max_1958_idx, 'State']} ({df.loc[max_1958_idx, 'Enrollment_per_capita_1958']:.6f})")
    print(f"Lowest enrollment per capita: {df.loc[min_1958_idx, 'State']} ({df.loc[min_1958_idx, 'Enrollment_per_capita_1958']:.6f})")

    print("\n1890 Enrollment Statistics:")
    valid_1890 = df.dropna(subset=['Enrollment_per_capita_1890'])
    print(f"States with data: {len(valid_1890)}")
    if not valid_1890.empty:
        max_1890_idx = valid_1890['Enrollment_per_capita_1890'].idxmax()
        min_1890_idx = valid_1890['Enrollment_per_capita_1890'].idxmin()
        print(f"Highest enrollment per capita: {valid_1890.loc[max_1890_idx, 'State']} ({valid_1890.loc[max_1890_idx, 'Enrollment_per_capita_1890']:.6f})")
        print(f"Lowest enrollment per capita: {valid_1890.loc[min_1890_idx, 'State']} ({valid_1890.loc[min_1890_idx, 'Enrollment_per_capita_1890']:.6f})")

def create_change_visualization():
    """Create a visualization showing enrollment change from 1890 to 1958 for each state"""

    # Load data
    df = load_and_process_data()

    # Filter to states that have both 1890 and 1958 data
    df_complete = df.dropna(subset=['Enrollment_per_capita_1890', 'Enrollment_per_capita_1958'])

    # Sort by 1958 enrollment (descending)
    df_complete = df_complete.sort_values('Enrollment_per_capita_1958', ascending=False)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(14, 20))

    # Set up y positions for states
    y_positions = range(len(df_complete))

    # Plot points for 1890 and 1958
    ax.scatter(df_complete['Enrollment_per_capita_1890'], y_positions,
              color='red', s=80, alpha=0.7, label='1890', zorder=3)
    ax.scatter(df_complete['Enrollment_per_capita_1958'], y_positions,
              color='blue', s=80, alpha=0.7, label='1958', zorder=3)

    # Draw arrows from 1890 to 1958
    for i, (idx, row) in enumerate(df_complete.iterrows()):
        ax.annotate('', xy=(row['Enrollment_per_capita_1958'], i),
                   xytext=(row['Enrollment_per_capita_1890'], i),
                   arrowprops=dict(arrowstyle='->', color='gray', alpha=0.6, lw=1.5))

        # Add value labels
        ax.text(row['Enrollment_per_capita_1890'] - 0.05, i,
               f'{row["Enrollment_per_capita_1890"]:.2f}',
               ha='right', va='center', fontsize=8, color='darkred')
        ax.text(row['Enrollment_per_capita_1958'] + 0.05, i,
               f'{row["Enrollment_per_capita_1958"]:.2f}',
               ha='left', va='center', fontsize=8, color='darkblue')

    # Customize the plot
    ax.set_yticks(y_positions)
    ax.set_yticklabels(df_complete['State'], fontsize=10)
    ax.set_xlabel('Enrollment per Capita (per 100 people)', fontsize=12, fontweight='bold')
    ax.set_title('Change in College Enrollment per Capita by State: 1890 → 1958\n(States ordered by 1958 enrollment)',
                fontsize=14, fontweight='bold', pad=20)

    # Add legend
    ax.legend(loc='lower right', fontsize=12)

    # Add grid
    ax.grid(True, alpha=0.3, axis='x')

    # Invert y-axis so highest 1958 enrollment is at top
    ax.invert_yaxis()

    # Adjust layout
    plt.tight_layout()

    # Create output directory if it doesn't exist
    output_dir = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures'
    os.makedirs(output_dir, exist_ok=True)

    # Save the plot
    output_path = os.path.join(output_dir, 'enrollments_bowman_1962.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"Change visualization saved to: {output_path}")

    # Print summary statistics
    print(f"\nStates with complete data (1890 and 1958): {len(df_complete)}")

    # Calculate changes
    df_complete['Change'] = df_complete['Enrollment_per_capita_1958'] - df_complete['Enrollment_per_capita_1890']
    df_complete['Percent_Change'] = ((df_complete['Enrollment_per_capita_1958'] - df_complete['Enrollment_per_capita_1890']) / df_complete['Enrollment_per_capita_1890']) * 100

    print(f"\nLargest increases:")
    top_increases = df_complete.nlargest(5, 'Change')
    for _, row in top_increases.iterrows():
        print(f"  {row['State']}: {row['Change']:.5f} ({row['Percent_Change']:.1f}% increase)")

    print(f"\nLargest decreases:")
    top_decreases = df_complete.nsmallest(5, 'Change')
    for _, row in top_decreases.iterrows():
        print(f"  {row['State']}: {row['Change']:.5f} ({row['Percent_Change']:.1f}% change)")

if __name__ == "__main__":
    # Create the change visualization
    create_change_visualization()