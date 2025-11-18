"""
Share of Professional Workers by Region and Cohort

This script creates a visualization showing the share of people in professional
occupations by age cohort and region using pre-aggregated state-level data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse


def map_state_to_region(state_name):
    """
    Map state names to Census regions.

    Parameters:
    -----------
    state_name : str
        Full state name

    Returns:
    --------
    str
        Region name: 'Northeast', 'Midwest', 'South', 'West', or 'Other'
    """
    regions = {
        # Northeast
        'Northeast': ['Connecticut', 'Maine', 'Massachusetts', 'New Hampshire', 'Rhode Island',
                     'Vermont', 'New Jersey', 'New York', 'Pennsylvania'],

        # Midwest
        'Midwest': ['Illinois', 'Indiana', 'Iowa', 'Kansas', 'Michigan', 'Minnesota',
                   'Missouri', 'Nebraska', 'North Dakota', 'Ohio', 'South Dakota', 'Wisconsin'],

        # South
        'South': ['Alabama', 'Arkansas', 'Delaware', 'District of Columbia', 'Florida',
                 'Georgia', 'Kentucky', 'Louisiana', 'Maryland', 'Mississippi', 'North Carolina',
                 'Oklahoma', 'South Carolina', 'Tennessee', 'Texas', 'Virginia', 'West Virginia'],

        # West
        'West': ['Alaska', 'Arizona', 'California', 'Colorado', 'Hawaii', 'Idaho',
                'Montana', 'Nevada', 'New Mexico', 'Oregon', 'Utah', 'Washington', 'Wyoming']
    }

    for region, states in regions.items():
        if state_name in states:
            return region

    return 'Other'


def aggregate_to_regions(df, exclude_other=False, include_managers=False):
    """
    Aggregate state-level occupation data to regional level.

    Parameters:
    -----------
    df : pd.DataFrame
        State-level data with columns: state, cohort_5year, occ_Professionals, total_count
    exclude_other : bool
        If True, exclude "Other" occupation category from denominator
    include_managers : bool
        If True, add managers to professionals in numerator

    Returns:
    --------
    pd.DataFrame
        Regional aggregates with professional share
    """
    # Map states to regions
    df['region'] = df['state'].apply(map_state_to_region)

    # Filter out 'Other' region if any
    df = df[df['region'] != 'Other']

    # Define occupation categories
    occ_categories = ['occ_Professionals', 'occ_Farmers', 'occ_Managers', 'occ_Clerical',
                      'occ_Sales', 'occ_Craftsmen', 'occ_Operatives', 'occ_Service Workers',
                      'occ_Laborers']

    if exclude_other:
        # Calculate total excluding "Other" category
        df = df.copy()
        df['total_count_excl_other'] = df[occ_categories].sum(axis=1)

        # Aggregate by region and cohort
        agg_dict = {
            'occ_Professionals': 'sum',
            'total_count': ('total_count_excl_other', 'sum')
        }

        if include_managers:
            agg_dict['occ_Managers'] = 'sum'

        regional_data = df.groupby(['region', 'cohort_5year']).agg(
            occ_Professionals=('occ_Professionals', 'sum'),
            occ_Managers=('occ_Managers', 'sum') if include_managers else ('occ_Professionals', lambda x: 0),
            total_count=('total_count_excl_other', 'sum')
        ).reset_index()
    else:
        # Aggregate by region and cohort (including Other)
        regional_data = df.groupby(['region', 'cohort_5year']).agg(
            occ_Professionals=('occ_Professionals', 'sum'),
            occ_Managers=('occ_Managers', 'sum') if include_managers else ('occ_Professionals', lambda x: 0),
            total_count=('total_count', 'sum')
        ).reset_index()

    # Calculate professional share (as percentage)
    if include_managers:
        regional_data['professional_share'] = ((regional_data['occ_Professionals'] + regional_data['occ_Managers']) /
                                              regional_data['total_count']) * 100
    else:
        regional_data['professional_share'] = (regional_data['occ_Professionals'] /
                                              regional_data['total_count']) * 100

    return regional_data


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Create professional occupation share by region figure from state-level data.'
    )
    parser.add_argument('input', type=str, nargs='?',
                       default="/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/data_from_cluster/state_cohort_attainment_income.csv",
                       help='Path to input state-level CSV file')
    parser.add_argument('--output', type=str,
                       default="/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures",
                       help='Directory to save output figures')
    parser.add_argument('--cohort-min', type=int, default=1890,
                       help='Minimum cohort year to include (default: 1890)')
    parser.add_argument('--cohort-max', type=int, default=1935,
                       help='Maximum cohort year to include (default: 1935)')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    print(f"Reading state-level data from {args.input}...")

    # Read the state-level data
    df = pd.read_csv(args.input)

    print(f"Loaded {len(df):,} state-cohort observations")
    print(f"States: {df['state'].nunique()}")
    print(f"Cohort range: {df['cohort_5year'].min()} - {df['cohort_5year'].max()}")

    # Check if occupation columns exist
    if 'occ_Professionals' not in df.columns:
        print("\nERROR: 'occ_Professionals' column not found in data.")
        print("Available columns:", df.columns.tolist())
        print("\nPlease run state_level_attainment.py first to generate occupation data.")
        exit(1)

    # Filter to specified cohort range
    df = df[(df['cohort_5year'] >= args.cohort_min) &
            (df['cohort_5year'] <= args.cohort_max)]

    print(f"\nFiltered to cohorts {args.cohort_min}-{args.cohort_max}")
    print(f"Remaining observations: {len(df):,}")

    # Define consistent colors for regions (matching other scripts)
    region_colors = {
        'Northeast': '#1f77b4',  # blue
        'Midwest': '#ff7f0e',    # orange
        'South': '#2ca02c',      # green
        'West': '#d62728'        # red
    }

    # Define the three figure configurations
    figure_configs = [
        {
            'exclude_other': False,
            'include_managers': False,
            'filename': 'professional_share_by_cohort_region.png',
            'title': 'Share of Professional Workers by High School Cohort and Region',
            'description': 'Base case: Professional share (including Other category)'
        },
        {
            'exclude_other': True,
            'include_managers': False,
            'filename': 'professional_share_by_cohort_region_excl_other.png',
            'title': 'Share of Professional Workers by High School Cohort and Region\n(Excluding "Other" Occupation Category)',
            'description': 'Excluding "Other" occupation category from denominator'
        },
        {
            'exclude_other': True,
            'include_managers': True,
            'filename': 'professional_share_by_cohort_region_with_managers.png',
            'title': 'Share of Professional and Manager Workers by High School Cohort and Region\n(Excluding "Other" Occupation Category)',
            'description': 'Including managers with professionals in numerator, excluding "Other" from denominator'
        }
    ]

    # Generate all three figures
    for i, config in enumerate(figure_configs, 1):
        print(f"\n{'='*60}")
        print(f"Figure {i}/3: {config['description']}")
        print('='*60)

        # Aggregate to regions with current configuration
        print("\nAggregating to regions...")
        regional_data = aggregate_to_regions(df,
                                            exclude_other=config['exclude_other'],
                                            include_managers=config['include_managers'])

        # Sort by region and cohort
        regional_data = regional_data.sort_values(['region', 'cohort_5year'])

        print(f"Processed {len(regional_data):,} regional 5-year cohort bins")

        # Calculate overall professional share
        if config['include_managers']:
            total_professionals = df['occ_Professionals'].sum() + df['occ_Managers'].sum()
            label = "professional + manager"
        else:
            total_professionals = df['occ_Professionals'].sum()
            label = "professional"

        total_population = df['total_count'].sum()
        overall_professional_share = (total_professionals / total_population) * 100
        print(f"Overall {label} share: {overall_professional_share:.2f}%")

        # Print by region
        print("\nBy Region:")
        for region in ['Northeast', 'Midwest', 'South', 'West']:
            region_data = regional_data[regional_data['region'] == region]
            if len(region_data) > 0:
                total_prof = region_data['occ_Professionals'].sum()
                if config['include_managers']:
                    total_prof += region_data['occ_Managers'].sum()
                total_pop = region_data['total_count'].sum()
                prof_share = (total_prof / total_pop) * 100 if total_pop > 0 else 0
                print(f"  {region}: {prof_share:.2f}% {label} ({total_prof:,} of {total_pop:,})")

        # Create plot: Professional share by region
        fig, ax = plt.subplots(figsize=(12, 6))

        for region in ['Northeast', 'Midwest', 'South', 'West']:
            region_data = regional_data[regional_data['region'] == region]
            if len(region_data) > 0:
                ax.plot(region_data['cohort_5year'], region_data['professional_share'],
                       linewidth=2, marker='o', markersize=5, label=region,
                       color=region_colors[region])

        ax.set_xlabel('High School Cohort (5-Year Bins)', fontsize=12)
        ax.set_ylabel('Professional Share (%)', fontsize=12)
        ax.set_title(f'{config["title"]}, {args.cohort_min}-{args.cohort_max}',
                    fontsize=14)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)

        # Format y-axis as percentage
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))

        plt.tight_layout()

        # Save figure
        output_path = os.path.join(args.output, config['filename'])
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\nFigure saved to: {output_path}")

        plt.close()

    print("\n" + "="*60)
    print("All 3 figures generated successfully!")
    print("="*60)
