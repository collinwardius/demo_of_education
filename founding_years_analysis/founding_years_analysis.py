import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_secdr_data():
    """Load SECDR main data file."""
    secdr_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/secdr/SECDR_main.dta"
    secdr_df = pd.read_stata(secdr_path)

    print(f"\nLoaded SECDR data: {len(secdr_df)} observations")
    print(f"Years available: {secdr_df['year'].min()} to {secdr_df['year'].max()}")

    return secdr_df

def create_ppexpend_line_graph(secdr_df):
    """Create line graph of weighted average per-pupil expenditure over time."""

    # Filter out missing values for ppexpend_adj and students
    df_filtered = secdr_df[secdr_df['ppexpend_adj'].notna() & secdr_df['students'].notna()].copy()

    print(f"\nCreating per-pupil expenditure graph...")
    print(f"Records with valid ppexpend_adj and students: {len(df_filtered)}")

    # Calculate weighted average by year
    weighted_avg_by_year = []
    years = []

    for year in sorted(df_filtered['year'].unique()):
        year_data = df_filtered[df_filtered['year'] == year]

        # Calculate weighted average: sum(ppexpend_adj * students) / sum(students)
        total_weighted_expenditure = (year_data['ppexpend_adj'] * year_data['students']).sum()
        total_students = year_data['students'].sum()

        if total_students > 0:
            weighted_avg = total_weighted_expenditure / total_students
            weighted_avg_by_year.append(weighted_avg)
            years.append(year)

    # Create the plot
    plt.figure(figsize=(14, 8))

    plt.plot(years, weighted_avg_by_year, linewidth=3, color='#1f77b4',
            alpha=0.8, marker='o', markersize=8)

    plt.title('National Average Per-Pupil Expenditure Over Time\n',
              fontsize=16, fontweight='bold')
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('K-12 Per-Pupil Expenditure (2022 Dollars)', fontsize=12)
    plt.grid(True, alpha=0.3)

    # Format y-axis as currency
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "ppexpend_adj_national_weighted.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Per-pupil expenditure graph saved to: {output_path}")

    # Print summary statistics
    print("\nWeighted Average Per-Pupil Expenditure by Year:")
    for year, avg in zip(years, weighted_avg_by_year):
        print(f"  {year}: ${avg:,.2f}")

def create_k12_expenditure_by_region(secdr_df):
    """Create line graph of average K-12 expenditures by region over time."""

    # Filter out missing values for ppexpend_adj and students, and restrict to 1920-1950
    df_filtered = secdr_df[secdr_df['ppexpend_adj'].notna() &
                           secdr_df['students'].notna() &
                           secdr_df['region'].notna() &
                           (secdr_df['year'] >= 1920) &
                           (secdr_df['year'] <= 1950)].copy()

    print(f"\nCreating K-12 expenditure by region graph...")
    print(f"Records with valid data: {len(df_filtered)}")

    # Define consistent colors for each region
    region_colors = {
        'Northeast': '#1f77b4',  # blue
        'Midwest': '#ff7f0e',    # orange
        'South': '#2ca02c',      # green
        'West': '#d62728'        # red
    }

    # Get all unique regions and years
    regions = sorted(df_filtered['region'].unique())
    years = sorted(df_filtered['year'].unique())

    print(f"Regions: {regions}")
    print(f"Years: {years[0]} to {years[-1]}")

    # Create the plot
    plt.figure(figsize=(14, 8))

    # Calculate and plot weighted average for each region
    for region in regions:
        region_data = df_filtered[df_filtered['region'] == region]

        weighted_avg_by_year = []
        region_years = []

        for year in years:
            year_data = region_data[region_data['year'] == year]

            if len(year_data) > 0:
                # Calculate weighted average: sum(ppexpend_adj * students) / sum(students)
                total_weighted_expenditure = (year_data['ppexpend_adj'] * year_data['students']).sum()
                total_students = year_data['students'].sum()

                if total_students > 0:
                    weighted_avg = total_weighted_expenditure / total_students
                    weighted_avg_by_year.append(weighted_avg)
                    region_years.append(year)

        # Plot the line for this region
        plt.plot(region_years, weighted_avg_by_year, linewidth=2.5,
                color=region_colors.get(region, '#666666'),
                alpha=0.8, marker='o', markersize=6, label=region)

        print(f"\n{region}:")
        print(f"  Years: {len(region_years)}")
        if len(weighted_avg_by_year) > 0:
            print(f"  Average expenditure range: ${min(weighted_avg_by_year):,.0f} - ${max(weighted_avg_by_year):,.0f}")

    plt.title('Average K-12 Per-Student Expenditure by Region\n(Student-weighted, 2022 dollars)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('K-12 Expenditures per Student (2022 dollars)', fontsize=12)
    plt.legend(fontsize=11, loc='upper left')
    plt.grid(True, alpha=0.3)

    # Format y-axis as currency
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "k12_expenditure_by_region.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nK-12 expenditure by region plot saved to: {output_path}")

def create_founding_years_cdf():
    """Create CDF of college founding years for colleges existing as of 1944."""

    # Load data
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv"
    df = pd.read_csv(data_path)

    # Drop junior colleges
    df = df[df['College_Type'] != 'Junior Colleges'].copy()

    # Clean founding years - exclude missing, zero values, and unrealistic dates
    df['founding_year'] = pd.to_numeric(df['Founded_Year'], errors='coerce')
    df_clean = df[(df['founding_year'] >= 1600) & (df['founding_year'].notna())].copy()

    print(f"Total colleges (excluding junior colleges): {len(df)}")
    print(f"Colleges with valid founding years: {len(df_clean)}")
    print(f"Founding year range: {int(df_clean['founding_year'].min())} to {int(df_clean['founding_year'].max())}")

    # Create output directory
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Sort founding years
    founding_years = df_clean['founding_year'].sort_values()

    # Calculate CDF
    n = len(founding_years)
    cdf_values = np.arange(1, n + 1) / n

    # Create CDF plot
    plt.figure(figsize=(14, 8))
    plt.plot(founding_years, cdf_values, linewidth=2, color='darkblue', alpha=0.8)
    plt.fill_between(founding_years, cdf_values, alpha=0.3, color='lightblue')

    plt.title('Cumulative Distribution of College Founding Years\n(Colleges existing as of 1944)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Founding Year', fontsize=12)
    plt.ylabel('Cumulative Proportion', fontsize=12)
    plt.grid(True, alpha=0.3)

    # Add some key percentiles as annotations
    percentiles = [0.25, 0.5, 0.75]
    for p in percentiles:
        year_at_p = founding_years.quantile(p)
        plt.axhline(y=p, color='red', linestyle='--', alpha=0.5)
        plt.axvline(x=year_at_p, color='red', linestyle='--', alpha=0.5)
        plt.annotate(f'{int(p*100)}th percentile: {int(year_at_p)}',
                    xy=(year_at_p, p), xytext=(year_at_p + 10, p + 0.05),
                    fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    plt.tight_layout()
    output_path = Path(output_dir) / "founding_years_cdf.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"CDF plot saved to: {output_path}")

    return df_clean

def create_regional_founding_cdf(df_clean):
    """Create regional CDF of college founding years for colleges existing as of 1944."""

    # Define regional mapping based on state (handling uppercase state names)
    regional_mapping = {
        # Northeast
        'MAINE': 'Northeast', 'NEW HAMPSHIRE': 'Northeast', 'VERMONT': 'Northeast',
        'MASSACHUSETTS': 'Northeast', 'RHODE ISLAND': 'Northeast', 'CONNECTICUT': 'Northeast',
        'NEW YORK': 'Northeast', 'NEW JERSEY': 'Northeast', 'PENNSYLVANIA': 'Northeast',

        # South
        'DELAWARE': 'South', 'MARYLAND': 'South', 'VIRGINIA': 'South', 'WEST VIRGINIA': 'South',
        'KENTUCKY': 'South', 'TENNESSEE': 'South', 'NORTH CAROLINA': 'South', 'SOUTH CAROLINA': 'South',
        'GEORGIA': 'South', 'FLORIDA': 'South', 'ALABAMA': 'South', 'MISSISSIPPI': 'South',
        'ARKANSAS': 'South', 'LOUISIANA': 'South', 'TEXAS': 'South', 'OKLAHOMA': 'South',
        'DISTRICT OF COLUMBIA': 'South',  # DC often grouped with South

        # Midwest
        'OHIO': 'Midwest', 'INDIANA': 'Midwest', 'ILLINOIS': 'Midwest', 'MICHIGAN': 'Midwest',
        'WISCONSIN': 'Midwest', 'MINNESOTA': 'Midwest', 'IOWA': 'Midwest', 'MISSOURI': 'Midwest',
        'NORTH DAKOTA': 'Midwest', 'SOUTH DAKOTA': 'Midwest', 'NEBRASKA': 'Midwest', 'KANSAS': 'Midwest',

        # West
        'MONTANA': 'West', 'WYOMING': 'West', 'COLORADO': 'West', 'NEW MEXICO': 'West',
        'IDAHO': 'West', 'UTAH': 'West', 'NEVADA': 'West', 'ARIZONA': 'West',
        'WASHINGTON': 'West', 'OREGON': 'West', 'CALIFORNIA': 'West', 'ALASKA': 'West', 'HAWAII': 'West'
    }

    # Map regions
    df_clean['region'] = df_clean['State'].map(regional_mapping)

    # Check for unmapped states
    unmapped = df_clean[df_clean['region'].isna()]['State'].unique()
    if len(unmapped) > 0:
        print(f"Unmapped states: {unmapped}")
        # Assign unmapped to 'Other'
        df_clean['region'] = df_clean['region'].fillna('Other')

    # Get regional statistics
    regional_stats = df_clean.groupby('region').agg({
        'founding_year': ['count', 'min', 'max', 'mean']
    }).round(1)
    regional_stats.columns = ['Count', 'Min_Year', 'Max_Year', 'Mean_Year']
    print("\nRegional Statistics:")
    print(regional_stats)

    # Create regional CDF plot
    plt.figure(figsize=(14, 8))

    regions = df_clean['region'].dropna().unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(regions)))

    for i, region in enumerate(sorted(regions)):
        if pd.isna(region):
            continue

        regional_data = df_clean[df_clean['region'] == region]['founding_year'].sort_values()

        if len(regional_data) > 0:
            n = len(regional_data)
            cdf_values = np.arange(1, n + 1) / n

            plt.plot(regional_data, cdf_values, linewidth=2.5,
                    label=f'{region} (n={n})', color=colors[i], alpha=0.8)

    plt.title('Cumulative Distribution of College Founding Years by Region\n(Colleges existing as of 1944)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Founding Year', fontsize=12)
    plt.ylabel('Cumulative Proportion', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11, loc='lower right')

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "founding_years_cdf_regional.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Regional CDF plot saved to: {output_path}")

    # Print some summary statistics
    print(f"\nSummary Statistics:")
    print(f"Overall median founding year: {int(df_clean['founding_year'].median())}")
    print(f"Overall mean founding year: {df_clean['founding_year'].mean():.1f}")

    # Regional medians
    print(f"\nRegional median founding years:")
    for region in sorted(df_clean['region'].dropna().unique()):
        regional_median = df_clean[df_clean['region'] == region]['founding_year'].median()
        print(f"  {region}: {int(regional_median)}")

def create_zoomed_founding_cdf(df_clean):
    """Create zoomed CDF of college founding years from 1800 onwards for colleges existing as of 1944."""

    # Filter for colleges founded from 1800 onwards
    df_1800_plus = df_clean[df_clean['founding_year'] >= 1800].copy()

    print(f"\nColleges founded 1800 or later: {len(df_1800_plus)} (out of {len(df_clean)} total)")

    # Create output directory
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"

    # Overall zoomed CDF - keep percentages relative to ALL colleges, not just 1800+
    founding_years = df_1800_plus['founding_year'].sort_values()
    n_total = len(df_clean)  # Use total count for percentage calculation
    n_1800_plus = len(df_1800_plus)

    # Calculate CDF values relative to total dataset
    pre_1800_proportion = (n_total - n_1800_plus) / n_total
    cdf_values = pre_1800_proportion + np.arange(1, n_1800_plus + 1) / n_total

    plt.figure(figsize=(14, 8))
    plt.plot(founding_years, cdf_values, linewidth=2, color='darkblue', alpha=0.8)
    plt.fill_between(founding_years, cdf_values, alpha=0.3, color='lightblue')

    plt.title('Cumulative Distribution of College Founding Years (1800-1944)\n(Colleges existing as of 1944)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Founding Year', fontsize=12)
    plt.ylabel('Cumulative Proportion', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xlim(1800, 1930)

    # Add some key percentiles as annotations
    percentiles = [0.25, 0.5, 0.75]
    for p in percentiles:
        year_at_p = founding_years.quantile(p)
        plt.axhline(y=p, color='red', linestyle='--', alpha=0.5)
        plt.axvline(x=year_at_p, color='red', linestyle='--', alpha=0.5)
        plt.annotate(f'{int(p*100)}th percentile: {int(year_at_p)}',
                    xy=(year_at_p, p), xytext=(year_at_p + 5, p + 0.05),
                    fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    plt.tight_layout()
    output_path = Path(output_dir) / "founding_years_cdf_1800_plus.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Zoomed CDF plot saved to: {output_path}")

def create_zoomed_regional_founding_cdf(df_clean):
    """Create zoomed regional CDF of college founding years from 1800 onwards for colleges existing as of 1944."""

    # Filter for colleges founded from 1800 onwards
    df_1800_plus = df_clean[df_clean['founding_year'] >= 1800].copy()

    # Map regions (already done in previous function, but ensure it's applied)
    regional_mapping = {
        # Northeast
        'MAINE': 'Northeast', 'NEW HAMPSHIRE': 'Northeast', 'VERMONT': 'Northeast',
        'MASSACHUSETTS': 'Northeast', 'RHODE ISLAND': 'Northeast', 'CONNECTICUT': 'Northeast',
        'NEW YORK': 'Northeast', 'NEW JERSEY': 'Northeast', 'PENNSYLVANIA': 'Northeast',

        # South
        'DELAWARE': 'South', 'MARYLAND': 'South', 'VIRGINIA': 'South', 'WEST VIRGINIA': 'South',
        'KENTUCKY': 'South', 'TENNESSEE': 'South', 'NORTH CAROLINA': 'South', 'SOUTH CAROLINA': 'South',
        'GEORGIA': 'South', 'FLORIDA': 'South', 'ALABAMA': 'South', 'MISSISSIPPI': 'South',
        'ARKANSAS': 'South', 'LOUISIANA': 'South', 'TEXAS': 'South', 'OKLAHOMA': 'South',
        'DISTRICT OF COLUMBIA': 'South',

        # Midwest
        'OHIO': 'Midwest', 'INDIANA': 'Midwest', 'ILLINOIS': 'Midwest', 'MICHIGAN': 'Midwest',
        'WISCONSIN': 'Midwest', 'MINNESOTA': 'Midwest', 'IOWA': 'Midwest', 'MISSOURI': 'Midwest',
        'NORTH DAKOTA': 'Midwest', 'SOUTH DAKOTA': 'Midwest', 'NEBRASKA': 'Midwest', 'KANSAS': 'Midwest',

        # West
        'MONTANA': 'West', 'WYOMING': 'West', 'COLORADO': 'West', 'NEW MEXICO': 'West',
        'IDAHO': 'West', 'UTAH': 'West', 'NEVADA': 'West', 'ARIZONA': 'West',
        'WASHINGTON': 'West', 'OREGON': 'West', 'CALIFORNIA': 'West', 'ALASKA': 'West', 'HAWAII': 'West'
    }

    df_1800_plus['region'] = df_1800_plus['State'].map(regional_mapping)

    # Also map regions for the full dataset to get pre-1800 counts by region
    df_clean['region'] = df_clean['State'].map(regional_mapping)

    # Get regional statistics for 1800+ data
    regional_stats = df_1800_plus.groupby('region').agg({
        'founding_year': ['count', 'min', 'max', 'mean']
    }).round(1)
    regional_stats.columns = ['Count', 'Min_Year', 'Max_Year', 'Mean_Year']
    print("\nRegional Statistics (1800+):")
    print(regional_stats)

    # Create zoomed regional CDF plot
    plt.figure(figsize=(14, 8))

    regions = df_1800_plus['region'].dropna().unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(regions)))

    for i, region in enumerate(sorted(regions)):
        if pd.isna(region):
            continue

        # Get data for this region from 1800+ and calculate relative to total regional count
        regional_data_1800_plus = df_1800_plus[df_1800_plus['region'] == region]['founding_year'].sort_values()
        regional_data_all = df_clean[df_clean['region'] == region]['founding_year']

        if len(regional_data_1800_plus) > 0:
            n_total_regional = len(regional_data_all)
            n_1800_plus_regional = len(regional_data_1800_plus)

            # Calculate pre-1800 proportion for this region
            pre_1800_proportion_regional = (n_total_regional - n_1800_plus_regional) / n_total_regional

            # Calculate CDF values relative to total regional dataset
            cdf_values = pre_1800_proportion_regional + np.arange(1, n_1800_plus_regional + 1) / n_total_regional

            plt.plot(regional_data_1800_plus, cdf_values, linewidth=2.5,
                    label=f'{region} (n={n_total_regional})', color=colors[i], alpha=0.8)

    plt.title('Cumulative Distribution of College Founding Years by Region (1800-1944)\n(Colleges existing as of 1944)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Founding Year', fontsize=12)
    plt.ylabel('Cumulative Proportion', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xlim(1800, 1930)
    plt.legend(fontsize=11, loc='lower right')

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "founding_years_cdf_regional_1800_plus.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Zoomed regional CDF plot saved to: {output_path}")

def create_control_type_founding_cdf(df_clean):
    """Create CDF comparing State vs Non-State controlled colleges founding years for colleges existing as of 1944."""

    # Create control type categories
    df_clean['control_type'] = df_clean['Control'].apply(lambda x: 'State' if x == 'State' else 'Non-State')

    # Get control type statistics
    control_stats = df_clean.groupby('control_type').agg({
        'founding_year': ['count', 'min', 'max', 'mean', 'median']
    }).round(1)
    control_stats.columns = ['Count', 'Min_Year', 'Max_Year', 'Mean_Year', 'Median_Year']
    print("\nControl Type Statistics:")
    print(control_stats)

    # Create control type CDF plot
    plt.figure(figsize=(14, 8))

    control_types = ['State', 'Non-State']
    colors = ['#1f77b4', '#ff7f0e']  # Blue for State, Orange for Non-State

    for i, control_type in enumerate(control_types):
        control_data = df_clean[df_clean['control_type'] == control_type]['founding_year'].sort_values()

        if len(control_data) > 0:
            n = len(control_data)
            cdf_values = np.arange(1, n + 1) / n

            plt.plot(control_data, cdf_values, linewidth=3,
                    label=f'{control_type} (n={n})', color=colors[i], alpha=0.8)

    plt.title('Cumulative Distribution of College Founding Years by Control Type\n(Colleges existing as of 1944, excluding Junior Colleges)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Founding Year', fontsize=12)
    plt.ylabel('Cumulative Proportion', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12, loc='lower right')

    # Add median lines
    for i, control_type in enumerate(control_types):
        control_data = df_clean[df_clean['control_type'] == control_type]['founding_year']
        if len(control_data) > 0:
            median_year = control_data.median()
            plt.axvline(x=median_year, color=colors[i], linestyle='--', alpha=0.7, linewidth=2)
            plt.text(median_year + 5, 0.1 + i*0.1, f'{control_type}\nMedian: {int(median_year)}',
                    fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "founding_years_cdf_control_type.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Control type CDF plot saved to: {output_path}")

    # Print detailed statistics
    print(f"\nDetailed Control Type Statistics:")
    for control_type in control_types:
        control_data = df_clean[df_clean['control_type'] == control_type]['founding_year']
        if len(control_data) > 0:
            print(f"\n{control_type} Colleges:")
            print(f"  Count: {len(control_data)}")
            print(f"  Median founding year: {int(control_data.median())}")
            print(f"  Mean founding year: {control_data.mean():.1f}")
            print(f"  25th percentile: {int(control_data.quantile(0.25))}")
            print(f"  75th percentile: {int(control_data.quantile(0.75))}")

def create_zoomed_control_type_founding_cdf(df_clean):
    """Create zoomed CDF comparing State vs Non-State controlled colleges from 1800 onwards for colleges existing as of 1944."""

    # Filter for colleges founded from 1800 onwards
    df_1800_plus = df_clean[df_clean['founding_year'] >= 1800].copy()

    # Create control type categories
    df_1800_plus['control_type'] = df_1800_plus['Control'].apply(lambda x: 'State' if x == 'State' else 'Non-State')

    print(f"\nControl Type Statistics (1800+):")
    control_stats_1800 = df_1800_plus.groupby('control_type').agg({
        'founding_year': ['count', 'min', 'max', 'mean', 'median']
    }).round(1)
    control_stats_1800.columns = ['Count', 'Min_Year', 'Max_Year', 'Mean_Year', 'Median_Year']
    print(control_stats_1800)

    # Create zoomed control type CDF plot
    plt.figure(figsize=(14, 8))

    control_types = ['State', 'Non-State']
    colors = ['#1f77b4', '#ff7f0e']  # Blue for State, Orange for Non-State

    for i, control_type in enumerate(control_types):
        # Get data for this control type from 1800+ and calculate relative to total control type count
        control_data_1800_plus = df_1800_plus[df_1800_plus['control_type'] == control_type]['founding_year'].sort_values()
        control_data_all = df_clean[df_clean['control_type'] == control_type]['founding_year']

        if len(control_data_1800_plus) > 0:
            n_total_control = len(control_data_all)
            n_1800_plus_control = len(control_data_1800_plus)

            # Calculate pre-1800 proportion for this control type
            pre_1800_proportion_control = (n_total_control - n_1800_plus_control) / n_total_control

            # Calculate CDF values relative to total control type dataset
            cdf_values = pre_1800_proportion_control + np.arange(1, n_1800_plus_control + 1) / n_total_control

            plt.plot(control_data_1800_plus, cdf_values, linewidth=3,
                    label=f'{control_type} (total n={n_total_control})', color=colors[i], alpha=0.8)

    plt.title('Cumulative Distribution of College Founding Years by Control Type (1800-1944)\n(Colleges existing as of 1944, excluding Junior Colleges)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Founding Year', fontsize=12)
    plt.ylabel('Cumulative Proportion', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xlim(1800, 1950)
    plt.legend(fontsize=12, loc='lower right')

    # Add median lines for 1800+ data
    for i, control_type in enumerate(control_types):
        control_data_1800_plus = df_1800_plus[df_1800_plus['control_type'] == control_type]['founding_year']
        if len(control_data_1800_plus) > 0:
            median_year = control_data_1800_plus.median()
            plt.axvline(x=median_year, color=colors[i], linestyle='--', alpha=0.7, linewidth=2)
            plt.text(median_year + 2, 0.2 + i*0.1, f'{control_type}\nMedian: {int(median_year)}',
                    fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "founding_years_cdf_control_type_1800_plus.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Zoomed control type CDF plot saved to: {output_path}")

def create_regional_operating_colleges_by_decade(df_clean):
    """Create figure showing total number of operating colleges per region by decade."""

    # Create decade column
    df_clean['decade'] = (df_clean['founding_year'] // 10) * 10

    # Define decades to analyze (from 1800 to 1940, since these are operating colleges as of 1944)
    decades = list(range(1800, 1950, 10))

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Calculate cumulative count of operating colleges by decade for each region
    operating_by_decade = {region: [] for region in regions}

    for decade in decades:
        for region in regions:
            # Count colleges founded on or before this decade
            count = len(df_clean[(df_clean['region'] == region) & (df_clean['founding_year'] <= decade)])
            operating_by_decade[region].append(count)

    # Create the plot
    plt.figure(figsize=(14, 8))

    colors = plt.cm.Set1(np.linspace(0, 1, len(regions)))

    for i, region in enumerate(regions):
        plt.plot(decades, operating_by_decade[region], linewidth=2.5,
                label=region, color=colors[i], alpha=0.8, marker='o')

    plt.title('Total Number of Operating Colleges by Region and Decade\n(Colleges existing as of 1944)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Decade', fontsize=12)
    plt.ylabel('Number of Operating Colleges', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11, loc='upper left')

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "operating_colleges_by_region_decade.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Operating colleges by region/decade plot saved to: {output_path}")

    # Print summary statistics
    print("\nOperating Colleges by Region in 1940:")
    for region in regions:
        count_1940 = len(df_clean[df_clean['region'] == region])
        print(f"  {region}: {count_1940}")

def create_regional_operating_public_colleges_by_decade(df_clean):
    """Create figure showing total number of operating public (state-controlled) colleges per region by decade."""

    # Filter for state-controlled colleges only
    df_public = df_clean[df_clean['Control'] == 'State'].copy()

    print(f"\nTotal public (state-controlled) colleges: {len(df_public)} (out of {len(df_clean)} total)")

    # Create decade column
    df_public['decade'] = (df_public['founding_year'] // 10) * 10

    # Define decades to analyze (from 1800 to 1940, since these are operating colleges as of 1944)
    decades = list(range(1800, 1950, 10))

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Calculate cumulative count of operating public colleges by decade for each region
    operating_by_decade = {region: [] for region in regions}

    for decade in decades:
        for region in regions:
            # Count public colleges founded on or before this decade
            count = len(df_public[(df_public['region'] == region) & (df_public['founding_year'] <= decade)])
            operating_by_decade[region].append(count)

    # Create the plot
    plt.figure(figsize=(14, 8))

    colors = plt.cm.Set1(np.linspace(0, 1, len(regions)))

    for i, region in enumerate(regions):
        plt.plot(decades, operating_by_decade[region], linewidth=2.5,
                label=region, color=colors[i], alpha=0.8, marker='o')

    plt.title('Total Number of Operating Public Colleges by Region and Decade\n(State-controlled colleges existing as of 1944)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Decade', fontsize=12)
    plt.ylabel('Number of Operating Public Colleges', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11, loc='upper left')

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "operating_public_colleges_by_region_decade.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Operating public colleges by region/decade plot saved to: {output_path}")

    # Print summary statistics
    print("\nOperating Public Colleges by Region in 1940:")
    for region in regions:
        count_1940 = len(df_public[df_public['region'] == region])
        print(f"  {region}: {count_1940}")

def load_and_aggregate_population_data():
    """Load state population data and aggregate to regional level."""

    # Load population data
    pop_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/historical_state_population_by_year.csv"
    pop_df = pd.read_csv(pop_path, names=['state_abbr', 'year', 'population'])

    # Create state abbreviation to full name mapping
    state_abbr_to_name = {
        'ME': 'MAINE', 'NH': 'NEW HAMPSHIRE', 'VT': 'VERMONT', 'MA': 'MASSACHUSETTS',
        'RI': 'RHODE ISLAND', 'CT': 'CONNECTICUT', 'NY': 'NEW YORK', 'NJ': 'NEW JERSEY',
        'PA': 'PENNSYLVANIA',

        'DE': 'DELAWARE', 'MD': 'MARYLAND', 'VA': 'VIRGINIA', 'WV': 'WEST VIRGINIA',
        'KY': 'KENTUCKY', 'TN': 'TENNESSEE', 'NC': 'NORTH CAROLINA', 'SC': 'SOUTH CAROLINA',
        'GA': 'GEORGIA', 'FL': 'FLORIDA', 'AL': 'ALABAMA', 'MS': 'MISSISSIPPI',
        'AR': 'ARKANSAS', 'LA': 'LOUISIANA', 'TX': 'TEXAS', 'OK': 'OKLAHOMA',
        'DC': 'DISTRICT OF COLUMBIA',

        'OH': 'OHIO', 'IN': 'INDIANA', 'IL': 'ILLINOIS', 'MI': 'MICHIGAN',
        'WI': 'WISCONSIN', 'MN': 'MINNESOTA', 'IA': 'IOWA', 'MO': 'MISSOURI',
        'ND': 'NORTH DAKOTA', 'SD': 'SOUTH DAKOTA', 'NE': 'NEBRASKA', 'KS': 'KANSAS',

        'MT': 'MONTANA', 'WY': 'WYOMING', 'CO': 'COLORADO', 'NM': 'NEW MEXICO',
        'ID': 'IDAHO', 'UT': 'UTAH', 'NV': 'NEVADA', 'AZ': 'ARIZONA',
        'WA': 'WASHINGTON', 'OR': 'OREGON', 'CA': 'CALIFORNIA', 'AK': 'ALASKA', 'HI': 'HAWAII'
    }

    # Regional mapping
    regional_mapping = {
        'MAINE': 'Northeast', 'NEW HAMPSHIRE': 'Northeast', 'VERMONT': 'Northeast',
        'MASSACHUSETTS': 'Northeast', 'RHODE ISLAND': 'Northeast', 'CONNECTICUT': 'Northeast',
        'NEW YORK': 'Northeast', 'NEW JERSEY': 'Northeast', 'PENNSYLVANIA': 'Northeast',

        'DELAWARE': 'South', 'MARYLAND': 'South', 'VIRGINIA': 'South', 'WEST VIRGINIA': 'South',
        'KENTUCKY': 'South', 'TENNESSEE': 'South', 'NORTH CAROLINA': 'South', 'SOUTH CAROLINA': 'South',
        'GEORGIA': 'South', 'FLORIDA': 'South', 'ALABAMA': 'South', 'MISSISSIPPI': 'South',
        'ARKANSAS': 'South', 'LOUISIANA': 'South', 'TEXAS': 'South', 'OKLAHOMA': 'South',
        'DISTRICT OF COLUMBIA': 'South',

        'OHIO': 'Midwest', 'INDIANA': 'Midwest', 'ILLINOIS': 'Midwest', 'MICHIGAN': 'Midwest',
        'WISCONSIN': 'Midwest', 'MINNESOTA': 'Midwest', 'IOWA': 'Midwest', 'MISSOURI': 'Midwest',
        'NORTH DAKOTA': 'Midwest', 'SOUTH DAKOTA': 'Midwest', 'NEBRASKA': 'Midwest', 'KANSAS': 'Midwest',

        'MONTANA': 'West', 'WYOMING': 'West', 'COLORADO': 'West', 'NEW MEXICO': 'West',
        'IDAHO': 'West', 'UTAH': 'West', 'NEVADA': 'West', 'ARIZONA': 'West',
        'WASHINGTON': 'West', 'OREGON': 'West', 'CALIFORNIA': 'West', 'ALASKA': 'West', 'HAWAII': 'West'
    }

    # Map abbreviations to full state names
    pop_df['state_name'] = pop_df['state_abbr'].map(state_abbr_to_name)

    # Map states to regions
    pop_df['region'] = pop_df['state_name'].map(regional_mapping)

    # Aggregate population by region and year
    regional_pop = pop_df.groupby(['region', 'year'])['population'].sum().reset_index()

    print(f"\nLoaded population data from {pop_df['year'].min()} to {pop_df['year'].max()}")
    print(f"Regions with population data: {sorted(regional_pop['region'].dropna().unique())}")

    return regional_pop

def create_colleges_per_capita_by_decade(df_clean, regional_pop):
    """Create figure showing colleges per hundred thousand residents by region and decade."""

    # Define decades to analyze (from 1900 to 1940, since population data starts at 1900)
    decades = list(range(1900, 1950, 10))

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Calculate colleges per hundred thousand residents by decade for each region
    per_capita_by_decade = {region: [] for region in regions}

    for decade in decades:
        for region in regions:
            # Count colleges founded on or before this decade
            college_count = len(df_clean[(df_clean['region'] == region) & (df_clean['founding_year'] <= decade)])

            # Get population for this region at this decade
            pop_data = regional_pop[(regional_pop['region'] == region) & (regional_pop['year'] == decade)]

            if len(pop_data) > 0:
                population = pop_data['population'].values[0]
                # Calculate per hundred thousand residents
                per_capita = (college_count / population) * 100000
                per_capita_by_decade[region].append(per_capita)
            else:
                per_capita_by_decade[region].append(None)

    # Create the plot
    plt.figure(figsize=(14, 8))

    colors = plt.cm.Set1(np.linspace(0, 1, len(regions)))

    for i, region in enumerate(regions):
        # Filter out None values
        valid_decades = [d for d, v in zip(decades, per_capita_by_decade[region]) if v is not None]
        valid_values = [v for v in per_capita_by_decade[region] if v is not None]

        if len(valid_values) > 0:
            plt.plot(valid_decades, valid_values, linewidth=2.5,
                    label=region, color=colors[i], alpha=0.8, marker='o')

    plt.title('Colleges per 100,000 Residents by Region and Decade\n(Colleges existing as of 1944)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Decade', fontsize=12)
    plt.ylabel('Colleges per 100,000 Residents', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11, loc='upper right')
    plt.xticks(decades)

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "colleges_per_capita_by_region_decade.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Colleges per capita by region/decade plot saved to: {output_path}")

    # Print summary statistics
    print("\nColleges per 100,000 Residents by Region in 1940:")
    for region in regions:
        college_count = len(df_clean[df_clean['region'] == region])
        pop_data = regional_pop[(regional_pop['region'] == region) & (regional_pop['year'] == 1940)]
        if len(pop_data) > 0:
            population = pop_data['population'].values[0]
            per_capita = (college_count / population) * 100000
            print(f"  {region}: {per_capita:.2f} colleges per 100,000 residents ({college_count} colleges, {population:,} population)")

def create_public_colleges_per_capita_by_decade(df_clean, regional_pop):
    """Create figure showing public colleges per hundred thousand residents by region and decade."""

    # Filter for state-controlled colleges only
    df_public = df_clean[df_clean['Control'] == 'State'].copy()

    # Define decades to analyze (from 1900 to 1940, since population data starts at 1900)
    decades = list(range(1900, 1950, 10))

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Calculate public colleges per hundred thousand residents by decade for each region
    per_capita_by_decade = {region: [] for region in regions}

    for decade in decades:
        for region in regions:
            # Count public colleges founded on or before this decade
            college_count = len(df_public[(df_public['region'] == region) & (df_public['founding_year'] <= decade)])

            # Get population for this region at this decade
            pop_data = regional_pop[(regional_pop['region'] == region) & (regional_pop['year'] == decade)]

            if len(pop_data) > 0:
                population = pop_data['population'].values[0]
                # Calculate per hundred thousand residents
                per_capita = (college_count / population) * 100000
                per_capita_by_decade[region].append(per_capita)
            else:
                per_capita_by_decade[region].append(None)

    # Create the plot
    plt.figure(figsize=(14, 8))

    colors = plt.cm.Set1(np.linspace(0, 1, len(regions)))

    for i, region in enumerate(regions):
        # Filter out None values
        valid_decades = [d for d, v in zip(decades, per_capita_by_decade[region]) if v is not None]
        valid_values = [v for v in per_capita_by_decade[region] if v is not None]

        if len(valid_values) > 0:
            plt.plot(valid_decades, valid_values, linewidth=2.5,
                    label=region, color=colors[i], alpha=0.8, marker='o')

    plt.title('Public Colleges per 100,000 Residents by Region and Decade\n(State-controlled colleges existing as of 1944)',
              fontsize=16, fontweight='bold')
    plt.xlabel('Decade', fontsize=12)
    plt.ylabel('Public Colleges per 100,000 Residents', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11, loc='upper right')
    plt.xticks(decades)

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "public_colleges_per_capita_by_region_decade.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Public colleges per capita by region/decade plot saved to: {output_path}")

    # Print summary statistics
    print("\nPublic Colleges per 100,000 Residents by Region in 1940:")
    for region in regions:
        college_count = len(df_public[df_public['region'] == region])
        pop_data = regional_pop[(regional_pop['region'] == region) & (regional_pop['year'] == 1940)]
        if len(pop_data) > 0:
            population = pop_data['population'].values[0]
            per_capita = (college_count / population) * 100000
            print(f"  {region}: {per_capita:.2f} public colleges per 100,000 residents ({college_count} colleges, {population:,} population)")

def create_junior_colleges_per_capita_by_decade(regional_pop):
    """Create figure showing junior colleges per hundred thousand residents by region and decade."""

    # Load the full dataset (including junior colleges)
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv"
    df = pd.read_csv(data_path)

    # Clean founding years
    df['founding_year'] = pd.to_numeric(df['Founded_Year'], errors='coerce')
    df = df[(df['founding_year'] >= 1600) & (df['founding_year'].notna())].copy()

    # Filter for junior colleges only
    df_junior = df[df['College_Type'] == 'Junior Colleges'].copy()

    # Regional mapping
    regional_mapping = {
        'MAINE': 'Northeast', 'NEW HAMPSHIRE': 'Northeast', 'VERMONT': 'Northeast',
        'MASSACHUSETTS': 'Northeast', 'RHODE ISLAND': 'Northeast', 'CONNECTICUT': 'Northeast',
        'NEW YORK': 'Northeast', 'NEW JERSEY': 'Northeast', 'PENNSYLVANIA': 'Northeast',

        'DELAWARE': 'South', 'MARYLAND': 'South', 'VIRGINIA': 'South', 'WEST VIRGINIA': 'South',
        'KENTUCKY': 'South', 'TENNESSEE': 'South', 'NORTH CAROLINA': 'South', 'SOUTH CAROLINA': 'South',
        'GEORGIA': 'South', 'FLORIDA': 'South', 'ALABAMA': 'South', 'MISSISSIPPI': 'South',
        'ARKANSAS': 'South', 'LOUISIANA': 'South', 'TEXAS': 'South', 'OKLAHOMA': 'South',
        'DISTRICT OF COLUMBIA': 'South',

        'OHIO': 'Midwest', 'INDIANA': 'Midwest', 'ILLINOIS': 'Midwest', 'MICHIGAN': 'Midwest',
        'WISCONSIN': 'Midwest', 'MINNESOTA': 'Midwest', 'IOWA': 'Midwest', 'MISSOURI': 'Midwest',
        'NORTH DAKOTA': 'Midwest', 'SOUTH DAKOTA': 'Midwest', 'NEBRASKA': 'Midwest', 'KANSAS': 'Midwest',

        'MONTANA': 'West', 'IDAHO': 'West', 'WYOMING': 'West', 'COLORADO': 'West', 'NEW MEXICO': 'West',
        'ARIZONA': 'West', 'UTAH': 'West', 'NEVADA': 'West', 'WASHINGTON': 'West', 'OREGON': 'West',
        'CALIFORNIA': 'West', 'ALASKA': 'West', 'HAWAII': 'West'
    }

    # Map states to regions
    df_junior['region'] = df_junior['State'].str.upper().map(regional_mapping)
    df_junior = df_junior[df_junior['region'].notna()].copy()

    # Define decades to analyze (from 1900 to 1940, since population data starts at 1900)
    decades = list(range(1900, 1950, 10))

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Define consistent colors for regions
    region_colors = {
        'Northeast': '#1f77b4',
        'Midwest': '#ff7f0e',
        'South': '#2ca02c',
        'West': '#d62728'
    }

    # Calculate junior colleges per hundred thousand residents by decade for each region
    per_capita_by_decade = {region: [] for region in regions}

    for decade in decades:
        for region in regions:
            # Count junior colleges founded on or before this decade
            college_count = len(df_junior[(df_junior['region'] == region) & (df_junior['founding_year'] <= decade)])

            # Get population for this region at this decade
            pop_data = regional_pop[(regional_pop['region'] == region) & (regional_pop['year'] == decade)]

            if len(pop_data) > 0:
                population = pop_data['population'].values[0]
                # Calculate per hundred thousand residents
                per_capita = (college_count / population) * 100000
                per_capita_by_decade[region].append(per_capita)
            else:
                per_capita_by_decade[region].append(None)

    # Create the plot
    plt.figure(figsize=(14, 8))

    for region in regions:
        # Filter out None values
        valid_decades = [d for d, v in zip(decades, per_capita_by_decade[region]) if v is not None]
        valid_values = [v for v in per_capita_by_decade[region] if v is not None]

        if len(valid_values) > 0:
            plt.plot(valid_decades, valid_values, linewidth=2.5,
                    label=region, color=region_colors[region], alpha=0.8, marker='o', markersize=8)

    plt.title('Junior Colleges per 100,000 Residents by Region and Decade',
              fontsize=16, fontweight='bold')
    plt.xlabel('Decade', fontsize=12)
    plt.ylabel('Junior Colleges per 100,000 Residents', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11, loc='upper left')
    plt.xticks(decades)

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "junior_colleges_per_capita_by_region_decade.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Junior colleges per capita by region/decade plot saved to: {output_path}")

    # Print summary statistics
    print("\nJunior Colleges per 100,000 Residents by Region in 1940:")
    for region in regions:
        college_count = len(df_junior[(df_junior['region'] == region) & (df_junior['founding_year'] <= 1940)])
        pop_data = regional_pop[(regional_pop['region'] == region) & (regional_pop['year'] == 1940)]
        if len(pop_data) > 0:
            population = pop_data['population'].values[0]
            per_capita = (college_count / population) * 100000
            print(f"  {region}: {per_capita:.2f} junior colleges per 100,000 residents ({college_count} colleges, {population:,} population)")

def create_total_operating_colleges_by_decade(df_clean, secdr_df):
    """Create figure showing total number of operating colleges by decade from 1900-1940, broken down by type,
    with per-pupil expenditure overlaid on a second y-axis."""

    # Load the full dataset (including junior colleges)
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv"
    df = pd.read_csv(data_path)

    # Clean founding years
    df['founding_year'] = pd.to_numeric(df['Founded_Year'], errors='coerce')
    df_all = df[(df['founding_year'] >= 1600) & (df['founding_year'].notna())].copy()

    # Define decades to analyze (from 1900 to 1940)
    decades = list(range(1900, 1950, 10))

    # Categorize colleges by type
    # Teachers colleges: includes Teacher, Teachers, T., Teach
    df_all['is_teachers'] = df_all['College_Name'].str.contains(r'Teacher|Teachers|T\.|Teach', case=False, na=False, regex=True)

    # Junior colleges
    df_all['is_junior'] = df_all['College_Type'] == 'Junior Colleges'

    # Normal schools: includes Normal, Nor.
    df_all['is_normal'] = df_all['College_Name'].str.contains(r'Normal|Nor\.', case=False, na=False, regex=True)

    # Calculate counts by decade for each category
    teachers_by_decade = []
    junior_by_decade = []
    normal_by_decade = []
    other_by_decade = []
    total_by_decade = []

    for decade in decades:
        df_decade = df_all[df_all['founding_year'] <= decade]

        teachers_count = len(df_decade[df_decade['is_teachers']])
        junior_count = len(df_decade[df_decade['is_junior']])
        normal_count = len(df_decade[df_decade['is_normal']])

        # Other colleges (excluding teachers, junior, and normal)
        other_count = len(df_decade[~df_decade['is_teachers'] & ~df_decade['is_junior'] & ~df_decade['is_normal']])

        total_count = len(df_decade)

        teachers_by_decade.append(teachers_count)
        junior_by_decade.append(junior_count)
        normal_by_decade.append(normal_count)
        other_by_decade.append(other_count)
        total_by_decade.append(total_count)

    # Calculate per-pupil expenditure for overlapping years (1920-1940)
    df_filtered = secdr_df[secdr_df['ppexpend_adj'].notna() & secdr_df['students'].notna()].copy()

    expenditure_years = []
    expenditure_values = []

    for year in decades:
        if year >= 1920:  # SECDR data starts in 1920
            year_data = df_filtered[df_filtered['year'] == year]
            if len(year_data) > 0:
                total_weighted_expenditure = (year_data['ppexpend_adj'] * year_data['students']).sum()
                total_students = year_data['students'].sum()
                if total_students > 0:
                    weighted_avg = total_weighted_expenditure / total_students
                    expenditure_years.append(year)
                    expenditure_values.append(weighted_avg)

    # Create the plot with dual y-axes
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Plot college counts on primary y-axis
    # ax1.plot(decades, teachers_by_decade, linewidth=2.5, color='#e41a1c',
    #         alpha=0.8, marker='d', markersize=8, label='Teachers Colleges')
    ax1.plot(decades, junior_by_decade, linewidth=2.5, color='#377eb8',
            alpha=0.8, marker='d', markersize=8, label='Junior Colleges')
    ax1.plot(decades, other_by_decade, linewidth=2.5, color='#984ea3',
            alpha=0.8, marker='d', markersize=8, label='Conventional Colleges')

    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Number of Operating Colleges', fontsize=12, color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.set_xticks(decades)
    ax1.grid(True, alpha=0.3)

    # Create secondary y-axis for expenditure
    ax2 = ax1.twinx()
    ax2.plot(expenditure_years, expenditure_values, linewidth=3, color='#ff7f00',
            alpha=0.8, marker='o', markersize=10, label='K-12 Per-Student Expenditure', linestyle='--')

    ax2.set_ylabel('K-12 Expenditures per Student (2022 dollars)', fontsize=12, color='#ff7f00')
    ax2.tick_params(axis='y', labelcolor='#ff7f00')

    # Format y-axis as currency
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=11, loc='upper left')

    plt.title('Number of Operating Colleges and K-12 expenditures per student',
              fontsize=16, fontweight='bold')

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "operating_colleges_and_k12_expend.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Total operating colleges by decade plot saved to: {output_path}")

    # Print summary statistics
    print("\nOperating Colleges by Type and Decade:")
    for i, decade in enumerate(decades):
        print(f"  {decade}:")
        print(f"    Teachers Colleges: {teachers_by_decade[i]}")
        print(f"    Junior Colleges: {junior_by_decade[i]}")
        print(f"    Normal Schools: {normal_by_decade[i]}")
        print(f"    Other Colleges: {other_by_decade[i]}")
        print(f"    Total: {total_by_decade[i]}")

        # Add expenditure if available
        if decade in expenditure_years:
            idx = expenditure_years.index(decade)
            print(f"    Per-Student Expenditure: ${expenditure_values[idx]:,.2f}")

def create_regional_capacity_per_capita_histogram(regional_pop):
    """Create histogram of student capacity per capita by region in 1945."""

    # Load the full dataset (not just the cleaned one)
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv"
    df = pd.read_csv(data_path)

    # Drop junior colleges
    df = df[df['College_Type'] != 'Junior Colleges'].copy()

    # Convert Student_Capacity to numeric, handling non-numeric values
    df['Student_Capacity'] = pd.to_numeric(df['Student_Capacity'], errors='coerce')

    # Convert founding year and filter for colleges existing as of 1945
    df['founding_year'] = pd.to_numeric(df['Founded_Year'], errors='coerce')
    df = df[(df['founding_year'] <= 1945) & (df['founding_year'].notna())].copy()

    print(f"\nTotal colleges with capacity data (existing as of 1945): {df['Student_Capacity'].notna().sum()} out of {len(df)}")
    print(f"Total student capacity: {df['Student_Capacity'].sum():,.0f}")

    # Regional mapping
    regional_mapping = {
        'MAINE': 'Northeast', 'NEW HAMPSHIRE': 'Northeast', 'VERMONT': 'Northeast',
        'MASSACHUSETTS': 'Northeast', 'RHODE ISLAND': 'Northeast', 'CONNECTICUT': 'Northeast',
        'NEW YORK': 'Northeast', 'NEW JERSEY': 'Northeast', 'PENNSYLVANIA': 'Northeast',

        'DELAWARE': 'South', 'MARYLAND': 'South', 'VIRGINIA': 'South', 'WEST VIRGINIA': 'South',
        'KENTUCKY': 'South', 'TENNESSEE': 'South', 'NORTH CAROLINA': 'South', 'SOUTH CAROLINA': 'South',
        'GEORGIA': 'South', 'FLORIDA': 'South', 'ALABAMA': 'South', 'MISSISSIPPI': 'South',
        'ARKANSAS': 'South', 'LOUISIANA': 'South', 'TEXAS': 'South', 'OKLAHOMA': 'South',
        'DISTRICT OF COLUMBIA': 'South',

        'OHIO': 'Midwest', 'INDIANA': 'Midwest', 'ILLINOIS': 'Midwest', 'MICHIGAN': 'Midwest',
        'WISCONSIN': 'Midwest', 'MINNESOTA': 'Midwest', 'IOWA': 'Midwest', 'MISSOURI': 'Midwest',
        'NORTH DAKOTA': 'Midwest', 'SOUTH DAKOTA': 'Midwest', 'NEBRASKA': 'Midwest', 'KANSAS': 'Midwest',

        'MONTANA': 'West', 'WYOMING': 'West', 'COLORADO': 'West', 'NEW MEXICO': 'West',
        'IDAHO': 'West', 'UTAH': 'West', 'NEVADA': 'West', 'ARIZONA': 'West',
        'WASHINGTON': 'West', 'OREGON': 'West', 'CALIFORNIA': 'West', 'ALASKA': 'West', 'HAWAII': 'West'
    }

    # Map states to regions
    df['region'] = df['State'].map(regional_mapping)

    # Aggregate student capacity by region
    regional_capacity = df.groupby('region')['Student_Capacity'].sum().reset_index()
    regional_capacity.columns = ['region', 'Total_Capacity']

    # Get population data for 1945 at regional level
    pop_1945 = regional_pop[regional_pop['year'] == 1945].copy()

    # Merge capacity with population
    regional_capacity = regional_capacity.merge(pop_1945, on='region', how='left')

    # Calculate capacity per 100,000 residents
    regional_capacity['capacity_per_100k'] = (regional_capacity['Total_Capacity'] / regional_capacity['population']) * 100000

    # Remove regions with missing data
    regional_capacity_clean = regional_capacity.dropna(subset=['capacity_per_100k']).copy()

    # Sort by region
    region_order = ['Northeast', 'South', 'Midwest', 'West']
    regional_capacity_clean['region_order'] = regional_capacity_clean['region'].map({
        'Northeast': 1, 'South': 2, 'Midwest': 3, 'West': 4
    })
    regional_capacity_clean = regional_capacity_clean.sort_values('region_order')

    # Create color mapping for regions
    region_colors = {
        'Northeast': '#e41a1c',  # Red
        'South': '#377eb8',      # Blue
        'Midwest': '#4daf4a',    # Green
        'West': '#984ea3'        # Purple
    }

    # Create the histogram
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create bars
    x_positions = np.arange(len(regional_capacity_clean))
    colors = [region_colors[region] for region in regional_capacity_clean['region']]

    bars = ax.bar(x_positions, regional_capacity_clean['capacity_per_100k'],
                  color=colors, alpha=0.8, edgecolor='black', linewidth=1)

    # Add numbers on top of bars
    for i, (bar, value) in enumerate(zip(bars, regional_capacity_clean['capacity_per_100k'])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(value)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Set x-axis labels
    ax.set_xticks(x_positions)
    ax.set_xticklabels(regional_capacity_clean['region'], fontsize=12)

    # Labels and title
    ax.set_xlabel('Region', fontsize=12)
    ax.set_ylabel('Student Capacity per 100,000 Residents', fontsize=12)
    ax.set_title('Student Capacity per 100,000 Residents by Region (1945)\n(Colleges existing as of 1945, excluding Junior Colleges)',
                 fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Add some space at the top for the labels
    ax.set_ylim(0, max(regional_capacity_clean['capacity_per_100k']) * 1.2)

    plt.tight_layout(pad=2.0)
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "regional_capacity_per_capita_1945.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nRegional capacity per capita histogram saved to: {output_path}")

    # Print statistics for all regions
    print("\nStudent capacity per 100,000 residents by region (1945):")
    for _, row in regional_capacity_clean.iterrows():
        print(f"  {row['region']}: {row['capacity_per_100k']:.1f} capacity per 100k ({row['Total_Capacity']:,.0f} total capacity, {row['population']:,} population)")

def create_regional_control_latex_table(df_clean):
    """Create LaTeX table showing college names by region and control type for colleges founded between 1900-1940."""

    # Filter for colleges founded between 1900 and 1940
    df_filtered = df_clean[(df_clean['founding_year'] >= 1900) & (df_clean['founding_year'] <= 1940)].copy()

    print(f"Colleges founded 1900-1940: {len(df_filtered)} (out of {len(df_clean)} total)")

    # Create control type categories
    df_filtered['control_type'] = df_filtered['Control'].apply(lambda x: 'State' if x == 'State' else 'Non-State')

    # Ensure region mapping is available (should already be mapped in df_clean)
    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Create output directory
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Start LaTeX table
    latex_content = []
    latex_content.append("\\begin{table}[htbp]")
    latex_content.append("\\centering")
    latex_content.append("\\caption{Colleges Founded 1900-1940 by Region and Control Type (Excluding Junior Colleges)}")
    latex_content.append("\\begin{tabular}{lccc}")
    latex_content.append("\\toprule")
    latex_content.append("\\textbf{Region} & \\textbf{State Controlled} & \\textbf{Non-State Controlled} & \\textbf{Total} \\\\")
    latex_content.append("\\midrule")

    # Process each region and calculate counts
    total_state = 0
    total_non_state = 0
    total_overall = 0

    for region in regions:
        region_data = df_filtered[df_filtered['region'] == region]

        if len(region_data) == 0:
            continue

        # Get counts
        state_count = len(region_data[region_data['control_type'] == 'State'])
        non_state_count = len(region_data[region_data['control_type'] == 'Non-State'])
        region_total = len(region_data)

        # Add to totals
        total_state += state_count
        total_non_state += non_state_count
        total_overall += region_total

        # Add row to table
        latex_content.append(f"{region} & {state_count} & {non_state_count} & {region_total} \\\\")

    # Add totals row
    latex_content.append("\\midrule")
    latex_content.append(f"\\textbf{{Total}} & \\textbf{{{total_state}}} & \\textbf{{{total_non_state}}} & \\textbf{{{total_overall}}} \\\\")
    latex_content.append("\\bottomrule")

    # Close LaTeX table
    latex_content.append("\\end{tabular}")
    latex_content.append("\\end{table}")

    # Write to file
    output_path = Path(output_dir) / "regional_control_colleges_table.tex"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_content))

    print(f"LaTeX table saved to: {output_path}")

def create_city_timeline_scatter(df_clean):
    """Create timeline scatter plot showing colleges founded by city between 1900-1940.
    Only shows cities that went from 0 to 1 active college during this period."""

    # Filter for colleges founded between 1900 and 1940
    df_filtered = df_clean[(df_clean['founding_year'] >= 1900) & (df_clean['founding_year'] <= 1940)].copy()

    print(f"\nCreating city timeline scatter plot...")
    print(f"Colleges founded 1900-1940: {len(df_filtered)}")

    # Clean city data - handle missing cities
    df_filtered = df_filtered[df_filtered['City'].notna()].copy()

    # Exclude normal schools, teachers colleges, junior colleges, and related abbreviations
    df_filtered = df_filtered[~df_filtered['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False)].copy()

    # Filter for colleges with capacity over 100
    df_filtered['Student_Capacity'] = pd.to_numeric(df_filtered['Student_Capacity'], errors='coerce')
    df_filtered = df_filtered[df_filtered['Student_Capacity'] > 100].copy()
    print(f"Colleges with valid city data (excluding normal schools/teachers colleges, capacity > 100): {len(df_filtered)}")

    # Find cities that had 0 active colleges before 1900 and got their first college 1900-1940
    # First, identify all cities with colleges before 1900 (excluding normal schools/teachers colleges/jr/nor/teach)
    df_clean_no_normal = df_clean[~df_clean['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False)].copy()
    cities_before_1900 = set(df_clean_no_normal[(df_clean_no_normal['founding_year'] < 1900) &
                                                 (df_clean_no_normal['City'].notna())]['City'].unique())

    # Get cities with exactly 1 college founded 1900-1940
    city_counts_1900_1940 = df_filtered['City'].value_counts()
    cities_with_one_college = city_counts_1900_1940[city_counts_1900_1940 == 1].index.tolist()

    # Filter to cities that had no colleges before 1900 AND got exactly 1 college 1900-1940
    cities_to_show = [city for city in cities_with_one_college if city not in cities_before_1900]

    df_plot = df_filtered[df_filtered['City'].isin(cities_to_show)].copy()

    print(f"\nShowing {len(cities_to_show)} cities that went from 0 to 1 college ({len(df_plot)} colleges total)")

    # Sort cities by founding year for better visualization
    df_plot = df_plot.sort_values('founding_year')
    cities_sorted = df_plot['City'].tolist()

    # Create region color mapping
    region_colors = {
        'Northeast': '#e41a1c',
        'South': '#377eb8',
        'Midwest': '#4daf4a',
        'West': '#984ea3'
    }

    # Create the plot
    fig, ax = plt.subplots(figsize=(18, max(12, len(cities_sorted) * 0.25)))

    # Plot each college
    for idx, row in df_plot.iterrows():
        city = row['City']
        year = row['founding_year']
        region = row['region']
        college_name = row['College_Name'] if 'College_Name' in row else 'Unknown'

        # Add student capacity to the label
        student_capacity = row['Student_Capacity']
        if pd.notna(student_capacity):
            label = f"{college_name}, {int(student_capacity)}"
        else:
            label = f"{college_name}, N/A"

        y_pos = cities_sorted.index(city)

        # Plot the point
        ax.scatter(year, y_pos, color=region_colors[region],
                  s=150, alpha=0.7, edgecolors='black', linewidth=0.8, zorder=3)

        # Add college name and capacity as annotation directly next to the dot
        ax.annotate(label, xy=(year, y_pos), xytext=(8, 0),
                   textcoords='offset points', fontsize=8, va='center', ha='left',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85, edgecolor='gray', linewidth=0.5))

    # Add legend for regions
    for region, color in region_colors.items():
        ax.scatter([], [], color=color, s=150, alpha=0.7, edgecolors='black',
                  linewidth=0.8, label=region)

    # Set y-axis to show city names
    ax.set_yticks(range(len(cities_sorted)))
    ax.set_yticklabels(cities_sorted, fontsize=9)

    # Set x-axis
    ax.set_xlabel('Founding Year', fontsize=14)
    ax.set_ylabel('City', fontsize=14)
    ax.set_title('First College Founded in Each City, 1900-1940\n(Cities with no prior colleges, excluding Junior Colleges)',
                 fontsize=16, fontweight='bold')

    # Add grid
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(1898, 1942)

    # Add legend
    ax.legend(fontsize=11, loc='lower right', title='Region', framealpha=0.9)

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "city_timeline_scatter_1900_1940.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nCity timeline scatter plot saved to: {output_path}")

def create_county_timeline_scatter(df_clean):
    """Create timeline scatter plot showing colleges founded by county between 1900-1940.
    Only shows counties that went from 0 to 1 active college during this period."""

    # Filter for colleges founded between 1900 and 1940
    df_filtered = df_clean[(df_clean['founding_year'] >= 1900) & (df_clean['founding_year'] <= 1940)].copy()

    print(f"\nCreating county timeline scatter plot...")
    print(f"Colleges founded 1900-1940: {len(df_filtered)}")

    # Clean county data - handle missing counties
    df_filtered = df_filtered[df_filtered['ICPSRNAM'].notna()].copy()

    # Exclude normal schools, teachers colleges, junior colleges, and related abbreviations
    df_filtered = df_filtered[~df_filtered['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False)].copy()

    # Filter for colleges with capacity over 100
    df_filtered['Student_Capacity'] = pd.to_numeric(df_filtered['Student_Capacity'], errors='coerce')
    df_filtered = df_filtered[df_filtered['Student_Capacity'] > 100].copy()
    print(f"Colleges with valid county data (excluding normal schools/teachers colleges, capacity > 100): {len(df_filtered)}")

    # Find counties that had 0 active colleges before 1900 and got their first college 1900-1940
    # First, identify all counties with colleges before 1900 (excluding normal schools/teachers colleges/jr/nor/teach)
    df_clean_no_normal = df_clean[~df_clean['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False)].copy()

    # Filter for colleges with capacity > 100 in the historical data as well
    df_clean_no_normal['Student_Capacity'] = pd.to_numeric(df_clean_no_normal['Student_Capacity'], errors='coerce')
    df_clean_no_normal = df_clean_no_normal[df_clean_no_normal['Student_Capacity'] > 100].copy()

    counties_before_1900 = set(df_clean_no_normal[(df_clean_no_normal['founding_year'] < 1900) &
                                                   (df_clean_no_normal['ICPSRNAM'].notna())]['ICPSRNAM'].unique())

    # Get counties with exactly 1 college founded 1900-1940
    county_counts_1900_1940 = df_filtered['ICPSRNAM'].value_counts()
    counties_with_one_college = county_counts_1900_1940[county_counts_1900_1940 == 1].index.tolist()

    # Filter to counties that had no colleges before 1900 AND got exactly 1 college 1900-1940
    counties_to_show = [county for county in counties_with_one_college if county not in counties_before_1900]

    df_plot = df_filtered[df_filtered['ICPSRNAM'].isin(counties_to_show)].copy()

    print(f"\nShowing {len(counties_to_show)} counties that went from 0 to 1 college ({len(df_plot)} colleges total)")

    # Sort counties by founding year for better visualization
    df_plot = df_plot.sort_values('founding_year')

    # Create county labels with state names
    df_plot['county_label'] = df_plot['ICPSRNAM'] + ', ' + df_plot['STATENAM']
    counties_sorted = df_plot['county_label'].tolist()

    # Create region color mapping
    region_colors = {
        'Northeast': '#e41a1c',
        'South': '#377eb8',
        'Midwest': '#4daf4a',
        'West': '#984ea3'
    }

    # Create the plot
    fig, ax = plt.subplots(figsize=(18, max(12, len(counties_sorted) * 0.25)))

    # Plot each college
    for idx, row in df_plot.iterrows():
        county_label = row['county_label']
        year = row['founding_year']
        region = row['region']
        college_name = row['College_Name'] if 'College_Name' in row else 'Unknown'

        # Add student capacity to the label
        student_capacity = row['Student_Capacity']
        if pd.notna(student_capacity):
            label = f"{college_name}, {int(student_capacity)}"
        else:
            label = f"{college_name}, N/A"

        y_pos = counties_sorted.index(county_label)

        # Plot the point
        ax.scatter(year, y_pos, color=region_colors[region],
                  s=150, alpha=0.7, edgecolors='black', linewidth=0.8, zorder=3)

        # Add college name and capacity as annotation directly next to the dot
        ax.annotate(label, xy=(year, y_pos), xytext=(8, 0),
                   textcoords='offset points', fontsize=8, va='center', ha='left',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85, edgecolor='gray', linewidth=0.5))

    # Add legend for regions
    for region, color in region_colors.items():
        ax.scatter([], [], color=color, s=150, alpha=0.7, edgecolors='black',
                  linewidth=0.8, label=region)

    # Set y-axis to show county names
    ax.set_yticks(range(len(counties_sorted)))
    ax.set_yticklabels(counties_sorted, fontsize=9)

    # Set x-axis
    ax.set_xlabel('Founding Year', fontsize=14)
    ax.set_ylabel('County', fontsize=14)
    ax.set_title('First College Founded in Each County, 1900-1940\n(Counties with no prior colleges, excluding Junior Colleges, Normal Schools, and Teachers Colleges, capacity > 100)',
                 fontsize=16, fontweight='bold')

    # Add grid
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(1898, 1942)

    # Add legend
    ax.legend(fontsize=11, loc='lower right', title='Region', framealpha=0.9)

    plt.tight_layout()
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "county_timeline_scatter_1900_1940.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nCounty timeline scatter plot saved to: {output_path}")

def create_county_analysis_table(df_clean):
    """Create LaTeX table and visualization showing county treatment/control groups."""

    print(f"\nCreating county analysis table...")

    # Load 1940 county shapefile to get total number of counties
    shapefile_path = Path('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files/nhgis0004_shapefile_tl2000_us_county_1940/US_county_1940.shp')

    import geopandas as gpd
    counties_gdf = gpd.read_file(shapefile_path)
    total_counties_1940 = len(counties_gdf)
    print(f"Total counties in 1940: {total_counties_1940}")

    # Filter out normal schools, teachers colleges, junior colleges
    df_clean_no_normal = df_clean[~df_clean['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False, regex=True)].copy()

    # Filter for colleges with capacity > 100
    df_clean_no_normal['Student_Capacity'] = pd.to_numeric(df_clean_no_normal['Student_Capacity'], errors='coerce')
    df_clean_no_normal = df_clean_no_normal[df_clean_no_normal['Student_Capacity'] > 100].copy()

    # Get all unique counties that ever had a college
    all_counties_with_colleges = df_clean_no_normal[df_clean_no_normal['ICPSRNAM'].notna()]['ICPSRNAM'].unique()

    # Filter for colleges before 1900
    df_before_1900 = df_clean_no_normal[df_clean_no_normal['founding_year'] < 1900].copy()
    counties_before_1900 = set(df_before_1900[df_before_1900['ICPSRNAM'].notna()]['ICPSRNAM'].unique())

    # Filter for colleges 1900-1940
    df_1900_1940 = df_clean_no_normal[(df_clean_no_normal['founding_year'] >= 1900) &
                                       (df_clean_no_normal['founding_year'] <= 1940)].copy()

    # Count colleges per county in 1900-1940 period
    county_counts_1900_1940 = df_1900_1940[df_1900_1940['ICPSRNAM'].notna()]['ICPSRNAM'].value_counts()

    # Group 1: Counties that had college before 1900
    group1_counties = counties_before_1900

    # Group 2: Counties that gained exactly 1 college 1900-1940 (and had 0 before 1900) - TREATED
    counties_with_one = set(county_counts_1900_1940[county_counts_1900_1940 == 1].index.tolist())
    group2_counties = counties_with_one - counties_before_1900

    # Group 3: Counties that had 0 before 1900 and gained 2+ colleges 1900-1940
    counties_with_multiple = set(county_counts_1900_1940[county_counts_1900_1940 > 1].index.tolist())
    group3_counties = counties_with_multiple - counties_before_1900

    # Group 4: Counties that had college before 1900 and did NOT get another 1900-1940
    counties_that_gained_1900_1940 = set(county_counts_1900_1940.index.tolist())
    group4_counties = counties_before_1900 - counties_that_gained_1900_1940

    # Group 5: Counties that never had a college by 1940 - CONTROL
    n_counties_with_colleges = len(all_counties_with_colleges)
    n_group5 = total_counties_1940 - n_counties_with_colleges

    # Calculate totals
    n_group1 = len(group1_counties)
    n_group2 = len(group2_counties)
    n_group3 = len(group3_counties)
    n_group4 = len(group4_counties)
    n_total_with_colleges = len(all_counties_with_colleges)

    print(f"Group 1 (Had college before 1900): {n_group1}")
    print(f"Group 2 (0→1 college, 1900-1940) [TREATED]: {n_group2}")
    print(f"Group 3 (0→2+ colleges, 1900-1940): {n_group3}")
    print(f"Group 4 (Had college before 1900, no new college 1900-1940) [CONTROL]: {n_group4}")
    print(f"Group 5 (Never had college by 1940) [CONTROL]: {n_group5}")
    print(f"Total counties with colleges: {n_total_with_colleges}")
    print(f"Total counties: {total_counties_1940}")

    # Create LaTeX table
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    latex_content = []
    latex_content.append("\\begin{table}[htbp]")
    latex_content.append("\\centering")
    latex_content.append("\\caption{County Classification for College Analysis (1900-1940)}")
    latex_content.append("\\label{tab:county_classification}")
    latex_content.append("\\begin{tabular}{lcc}")
    latex_content.append("\\toprule")
    latex_content.append("\\textbf{County Group} & \\textbf{Count} & \\textbf{Role in Analysis} \\\\")
    latex_content.append("\\midrule")
    latex_content.append(f"Had college before 1900 & {n_group1} & --- \\\\")
    latex_content.append(f"\\quad Did not gain college 1900-1940 & {n_group4} & Potential Control \\\\")
    latex_content.append(f"\\quad Gained college(s) 1900-1940 & {n_group1 - n_group4} & --- \\\\")
    latex_content.append("\\midrule")
    latex_content.append(f"No college before 1900 & {n_group2 + n_group3 + n_group5} & --- \\\\")
    latex_content.append(f"\\quad Gained exactly 1 college 1900-1940 & {n_group2} & \\textbf{{Treated}} \\\\")
    latex_content.append(f"\\quad Gained 2+ colleges 1900-1940 & {n_group3} & --- \\\\")
    latex_content.append(f"\\quad Never gained college by 1940 & {n_group5} & Potential Control \\\\")
    latex_content.append("\\bottomrule")
    latex_content.append("\\end{tabular}")
    latex_content.append("\\\\[1em]")
    latex_content.append("\\begin{minipage}{0.85\\textwidth}")
    latex_content.append("\\small")
    latex_content.append("\\textit{Notes:} Analysis excludes junior colleges, normal schools, teachers colleges, and colleges with capacity $\\leq$ 100. ")
    latex_content.append("Treated group consists of counties that had no college before 1900 and gained exactly one college 1900-1940. ")
    latex_content.append("Potential control groups consist of (1) counties that had a college before 1900 but did not gain additional colleges 1900-1940, ")
    latex_content.append("and (2) counties that never had a college by 1940.")
    latex_content.append("\\end{minipage}")
    latex_content.append("\\end{table}")

    # Write to file
    output_path = Path(output_dir) / "county_classification_table.tex"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_content))

    print(f"LaTeX table saved to: {output_path}")

    return {
        'n_had_college_before_1900': n_group1,
        'n_treated_0_to_1': n_group2,
        'n_0_to_multiple': n_group3,
        'n_control_had_no_gain': n_group4,
        'n_control_never_had': n_group5,
        'n_total': total_counties_1940
    }

def create_capacity_share_bar_chart(df_clean, year=1940):
    """Create bar chart showing share of public (state) student capacity by census region for a specific year."""

    # Filter out normal schools, teachers colleges, and related abbreviations
    df_filtered = df_clean[~df_clean['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False)].copy()

    # Filter for colleges founded by specified year
    df_filtered = df_filtered[df_filtered['founding_year'] <= year].copy()

    # Filter out colleges with missing capacity data
    df_filtered = df_filtered[df_filtered['Student_Capacity'].notna()].copy()
    df_filtered['Student_Capacity'] = pd.to_numeric(df_filtered['Student_Capacity'], errors='coerce')
    df_filtered = df_filtered[df_filtered['Student_Capacity'] > 0].copy()

    print(f"\nColleges with capacity data (founded by {year}, excluding normal/teachers colleges): {len(df_filtered)}")
    print(f"Total student capacity: {df_filtered['Student_Capacity'].sum():,.0f}")

    # Create control type categories
    df_filtered['control_type'] = df_filtered['Control'].apply(lambda x: 'State' if x == 'State' else 'Non-State')

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Create consistent region colors
    region_colors = {
        'Northeast': '#377eb8',  # blue
        'South': '#4daf4a',      # green
        'Midwest': '#ff7f00',    # orange
        'West': '#e41a1c'        # red
    }

    # Calculate state share for each region
    state_shares = []
    colors = []

    for region in regions:
        regional_data = df_filtered[df_filtered['region'] == region].copy()

        if len(regional_data) == 0:
            state_shares.append(0)
        else:
            # Calculate total capacity by control type
            state_capacity = regional_data[regional_data['control_type'] == 'State']['Student_Capacity'].sum()
            total_capacity = regional_data['Student_Capacity'].sum()

            if total_capacity > 0:
                state_share = (state_capacity / total_capacity) * 100
            else:
                state_share = 0

            state_shares.append(state_share)

        colors.append(region_colors[region])

    # Create bar chart
    fig, ax = plt.subplots(figsize=(10, 8))

    x_positions = np.arange(len(regions))
    bars = ax.bar(x_positions, state_shares, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add value labels on top of bars
    for i, (bar, value) in enumerate(zip(bars, state_shares)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}%',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Set labels and title
    ax.set_xticks(x_positions)
    ax.set_xticklabels(regions, fontsize=12)
    ax.set_ylabel('State Share of Student Capacity (%)', fontsize=12)
    ax.set_title(f'Share of Total Capacity that is Public by Region ({year})\n(Excluding Junior Colleges, Normal Schools, and Teachers Colleges)',
                fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / f"capacity_share_by_region_bar_{year}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Bar chart saved to: {output_path}")

    # Print summary statistics
    print(f"\nState Capacity Share by Region in {year}:")
    for region in regions:
        regional_data = df_filtered[df_filtered['region'] == region]
        if len(regional_data) > 0:
            state_capacity = regional_data[regional_data['control_type'] == 'State']['Student_Capacity'].sum()
            total_capacity = regional_data['Student_Capacity'].sum()

            if total_capacity > 0:
                state_share = (state_capacity / total_capacity) * 100
                print(f"  {region}: {state_share:.1f}% State (Total capacity: {total_capacity:,.0f})")

def create_public_college_share_bar_chart(df_clean, year=1940):
    """Create bar chart showing share of public colleges (by count) by census region for a specific year."""

    # Filter out normal schools, teachers colleges, and related abbreviations
    df_filtered = df_clean[~df_clean['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False)].copy()

    # Filter for colleges founded by specified year
    df_filtered = df_filtered[df_filtered['founding_year'] <= year].copy()

    print(f"\nColleges (founded by {year}, excluding normal/teachers colleges): {len(df_filtered)}")

    # Define regional mapping based on state
    regional_mapping = {
        'MAINE': 'Northeast', 'NEW HAMPSHIRE': 'Northeast', 'VERMONT': 'Northeast',
        'MASSACHUSETTS': 'Northeast', 'RHODE ISLAND': 'Northeast', 'CONNECTICUT': 'Northeast',
        'NEW YORK': 'Northeast', 'NEW JERSEY': 'Northeast', 'PENNSYLVANIA': 'Northeast',

        'DELAWARE': 'South', 'MARYLAND': 'South', 'VIRGINIA': 'South', 'WEST VIRGINIA': 'South',
        'KENTUCKY': 'South', 'TENNESSEE': 'South', 'NORTH CAROLINA': 'South', 'SOUTH CAROLINA': 'South',
        'GEORGIA': 'South', 'FLORIDA': 'South', 'ALABAMA': 'South', 'MISSISSIPPI': 'South',
        'ARKANSAS': 'South', 'LOUISIANA': 'South', 'TEXAS': 'South', 'OKLAHOMA': 'South',
        'DISTRICT OF COLUMBIA': 'South',

        'OHIO': 'Midwest', 'INDIANA': 'Midwest', 'ILLINOIS': 'Midwest', 'MICHIGAN': 'Midwest',
        'WISCONSIN': 'Midwest', 'MINNESOTA': 'Midwest', 'IOWA': 'Midwest', 'MISSOURI': 'Midwest',
        'NORTH DAKOTA': 'Midwest', 'SOUTH DAKOTA': 'Midwest', 'NEBRASKA': 'Midwest', 'KANSAS': 'Midwest',

        'MONTANA': 'West', 'WYOMING': 'West', 'COLORADO': 'West', 'NEW MEXICO': 'West',
        'IDAHO': 'West', 'UTAH': 'West', 'NEVADA': 'West', 'ARIZONA': 'West',
        'WASHINGTON': 'West', 'OREGON': 'West', 'CALIFORNIA': 'West', 'ALASKA': 'West', 'HAWAII': 'West'
    }

    # Map regions
    df_filtered['region'] = df_filtered['State'].map(regional_mapping)

    # Create control type categories
    df_filtered['control_type'] = df_filtered['Control'].apply(lambda x: 'State' if x == 'State' else 'Non-State')

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Create consistent region colors
    region_colors = {
        'Northeast': '#1f77b4',  # blue
        'Midwest': '#ff7f0e',    # orange
        'South': '#2ca02c',      # green
        'West': '#d62728'        # red
    }

    # Calculate state share for each region
    state_shares = []
    colors = []

    for region in regions:
        regional_data = df_filtered[df_filtered['region'] == region].copy()

        if len(regional_data) == 0:
            state_shares.append(0)
        else:
            # Count colleges by control type
            state_count = len(regional_data[regional_data['control_type'] == 'State'])
            total_count = len(regional_data)

            if total_count > 0:
                state_share = (state_count / total_count) * 100
            else:
                state_share = 0

            state_shares.append(state_share)

        colors.append(region_colors[region])

    # Create bar chart
    fig, ax = plt.subplots(figsize=(10, 8))

    x_positions = np.arange(len(regions))
    bars = ax.bar(x_positions, state_shares, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add value labels on top of bars
    for i, (bar, value) in enumerate(zip(bars, state_shares)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}%',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Set labels and title
    ax.set_xticks(x_positions)
    ax.set_xticklabels(regions, fontsize=12)
    ax.set_ylabel('Public Share of Colleges (%)', fontsize=12)
    ax.set_title(f'Share of Total Colleges that are Public by Region ({year})\n(Excluding Junior Colleges, Normal Schools, and Teachers Colleges)',
                fontsize=14, fontweight='bold')

    # Set y-axis limit based on max value with some padding
    max_value = max(state_shares) if state_shares else 0
    ax.set_ylim(0, max_value * 1.2)  # 20% padding above max value
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / f"public_college_share_by_region_bar_{year}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Bar chart saved to: {output_path}")

    # Print summary statistics
    print(f"\nPublic College Share by Region in {year}:")
    for region in regions:
        regional_data = df_filtered[df_filtered['region'] == region]
        if len(regional_data) > 0:
            state_count = len(regional_data[regional_data['control_type'] == 'State'])
            total_count = len(regional_data)

            if total_count > 0:
                state_share = (state_count / total_count) * 100
                print(f"  {region}: {state_share:.1f}% Public ({state_count}/{total_count} colleges)")

def create_colleges_per_capita_bar_chart(df_clean, regional_pop, year=1930):
    """Create bar chart showing colleges per 100,000 residents by region for a specific year."""

    # Filter out normal schools, teachers colleges, and related abbreviations
    df_filtered = df_clean[~df_clean['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False)].copy()

    # Filter for colleges founded by specified year
    df_filtered = df_filtered[df_filtered['founding_year'] <= year].copy()

    print(f"\nColleges (founded by {year}, excluding normal/teachers colleges): {len(df_filtered)}")

    # Define regional mapping based on state
    regional_mapping = {
        'MAINE': 'Northeast', 'NEW HAMPSHIRE': 'Northeast', 'VERMONT': 'Northeast',
        'MASSACHUSETTS': 'Northeast', 'RHODE ISLAND': 'Northeast', 'CONNECTICUT': 'Northeast',
        'NEW YORK': 'Northeast', 'NEW JERSEY': 'Northeast', 'PENNSYLVANIA': 'Northeast',

        'DELAWARE': 'South', 'MARYLAND': 'South', 'VIRGINIA': 'South', 'WEST VIRGINIA': 'South',
        'KENTUCKY': 'South', 'TENNESSEE': 'South', 'NORTH CAROLINA': 'South', 'SOUTH CAROLINA': 'South',
        'GEORGIA': 'South', 'FLORIDA': 'South', 'ALABAMA': 'South', 'MISSISSIPPI': 'South',
        'ARKANSAS': 'South', 'LOUISIANA': 'South', 'TEXAS': 'South', 'OKLAHOMA': 'South',
        'DISTRICT OF COLUMBIA': 'South',

        'OHIO': 'Midwest', 'INDIANA': 'Midwest', 'ILLINOIS': 'Midwest', 'MICHIGAN': 'Midwest',
        'WISCONSIN': 'Midwest', 'MINNESOTA': 'Midwest', 'IOWA': 'Midwest', 'MISSOURI': 'Midwest',
        'NORTH DAKOTA': 'Midwest', 'SOUTH DAKOTA': 'Midwest', 'NEBRASKA': 'Midwest', 'KANSAS': 'Midwest',

        'MONTANA': 'West', 'WYOMING': 'West', 'COLORADO': 'West', 'NEW MEXICO': 'West',
        'IDAHO': 'West', 'UTAH': 'West', 'NEVADA': 'West', 'ARIZONA': 'West',
        'WASHINGTON': 'West', 'OREGON': 'West', 'CALIFORNIA': 'West', 'ALASKA': 'West', 'HAWAII': 'West'
    }

    # Map regions
    df_filtered['region'] = df_filtered['State'].map(regional_mapping)

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Create consistent region colors
    region_colors = {
        'Northeast': '#1f77b4',  # blue
        'Midwest': '#ff7f0e',    # orange
        'South': '#2ca02c',      # green
        'West': '#d62728'        # red
    }

    # Calculate colleges per capita for each region
    per_capita_values = []
    colors = []

    for region in regions:
        regional_data = df_filtered[df_filtered['region'] == region]
        college_count = len(regional_data)

        # Get population for this region and year
        pop_data = regional_pop[(regional_pop['region'] == region) & (regional_pop['year'] == year)]

        if len(pop_data) > 0:
            population = pop_data['population'].values[0]
            per_capita = (college_count / population) * 100000
        else:
            per_capita = 0

        per_capita_values.append(per_capita)
        colors.append(region_colors[region])

    # Create bar chart
    fig, ax = plt.subplots(figsize=(10, 8))

    x_positions = np.arange(len(regions))
    bars = ax.bar(x_positions, per_capita_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add value labels on top of bars
    for i, (bar, value) in enumerate(zip(bars, per_capita_values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.2f}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Set labels and title
    ax.set_xticks(x_positions)
    ax.set_xticklabels(regions, fontsize=12)
    ax.set_ylabel('Colleges per 100,000 Residents', fontsize=12)
    ax.set_title(f'Colleges per 100,000 Residents by Region ({year})\n(Excluding Junior Colleges, Normal Schools, and Teachers Colleges)',
                fontsize=14, fontweight='bold')

    # Set y-axis limit based on max value with some padding
    max_value = max(per_capita_values) if per_capita_values else 0
    ax.set_ylim(0, max_value * 1.2)  # 20% padding above max value
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / f"colleges_per_capita_by_region_bar_{year}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Bar chart saved to: {output_path}")

    # Print summary statistics
    print(f"\nColleges per 100,000 Residents by Region in {year}:")
    for region in regions:
        regional_data = df_filtered[df_filtered['region'] == region]
        college_count = len(regional_data)

        pop_data = regional_pop[(regional_pop['region'] == region) & (regional_pop['year'] == year)]
        if len(pop_data) > 0:
            population = pop_data['population'].values[0]
            per_capita = (college_count / population) * 100000
            print(f"  {region}: {per_capita:.2f} colleges per 100,000 ({college_count} colleges, {population:,} population)")

def create_capacity_share_by_control_and_region(df_clean):
    """Create figure showing share of public (state) student capacity by census region from 1890-1940."""

    # Filter out normal schools, teachers colleges, and related abbreviations
    df_filtered = df_clean[~df_clean['College_Name'].str.contains(r'Normal|Teachers|Teacher|Jr\.|Nor\.|Teach|T\.', case=False, na=False)].copy()

    # Filter for colleges founded by 1940
    df_filtered = df_filtered[df_filtered['founding_year'] <= 1940].copy()

    # Filter out colleges with missing capacity data
    df_filtered = df_filtered[df_filtered['Student_Capacity'].notna()].copy()
    df_filtered['Student_Capacity'] = pd.to_numeric(df_filtered['Student_Capacity'], errors='coerce')
    df_filtered = df_filtered[df_filtered['Student_Capacity'] > 0].copy()

    print(f"\nColleges with capacity data (founded by 1940, excluding normal/teachers colleges): {len(df_filtered)}")
    print(f"Total student capacity: {df_filtered['Student_Capacity'].sum():,.0f}")

    # Create control type categories
    df_filtered['control_type'] = df_filtered['Control'].apply(lambda x: 'State' if x == 'State' else 'Non-State')

    # Define decades to analyze
    decades = list(range(1890, 1950, 10))

    # Define regions
    regions = ['Northeast', 'South', 'Midwest', 'West']

    # Create consistent region colors
    region_colors = {
        'Northeast': '#e41a1c',
        'South': '#377eb8',
        'Midwest': '#4daf4a',
        'West': '#984ea3'
    }

    # Create single plot
    plt.figure(figsize=(14, 8))

    for region in regions:
        regional_data = df_filtered[df_filtered['region'] == region].copy()

        if len(regional_data) == 0:
            continue

        state_shares = []

        for decade in decades:
            # Get colleges operating at this decade (founded on or before this decade)
            operating = regional_data[regional_data['founding_year'] <= decade]

            if len(operating) == 0:
                state_shares.append(0)
                continue

            # Calculate total capacity by control type
            state_capacity = operating[operating['control_type'] == 'State']['Student_Capacity'].sum()
            non_state_capacity = operating[operating['control_type'] == 'Non-State']['Student_Capacity'].sum()
            total_capacity = state_capacity + non_state_capacity

            if total_capacity > 0:
                state_share = (state_capacity / total_capacity) * 100
            else:
                state_share = 0

            state_shares.append(state_share)

        # Plot the state share for this region
        plt.plot(decades, state_shares, linewidth=2.5, label=region,
                color=region_colors[region], alpha=0.8, marker='o', markersize=8)

    plt.title('Share of Public (State) Student Capacity by Region (1890-1940)\n(Excluding Junior Colleges, Normal Schools, and Teachers Colleges)',
             fontsize=16, fontweight='bold')
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('State Share of Student Capacity (%)', fontsize=12)
    plt.ylim(-5, 105)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11, loc='best')
    plt.xticks(decades)

    plt.tight_layout()

    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    output_path = Path(output_dir) / "capacity_share_by_control_region_1890_1940.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Capacity share by control/region plot saved to: {output_path}")

    # Print summary statistics
    print("\nState Capacity Share by Region in 1940:")
    for region in regions:
        regional_data = df_filtered[(df_filtered['region'] == region) &
                                    (df_filtered['founding_year'] <= 1940)]
        if len(regional_data) > 0:
            state_capacity = regional_data[regional_data['control_type'] == 'State']['Student_Capacity'].sum()
            non_state_capacity = regional_data[regional_data['control_type'] == 'Non-State']['Student_Capacity'].sum()
            total_capacity = state_capacity + non_state_capacity

            if total_capacity > 0:
                state_share = (state_capacity / total_capacity) * 100
                print(f"  {region}: {state_share:.1f}% State (Total capacity: {total_capacity:,.0f})")

def main():
    print("Creating founding years CDF analysis...")

    # Load SECDR data
    secdr_df = load_secdr_data()

    # Create per-pupil expenditure graph
    create_ppexpend_line_graph(secdr_df)

    # Create K-12 expenditure by region graph
    create_k12_expenditure_by_region(secdr_df)

    # Create overall CDF
    df_clean = create_founding_years_cdf()

    # Create regional CDF
    create_regional_founding_cdf(df_clean)

    # Create zoomed versions from 1800 onwards
    create_zoomed_founding_cdf(df_clean)
    create_zoomed_regional_founding_cdf(df_clean)

    # Create control type comparisons
    create_control_type_founding_cdf(df_clean)
    create_zoomed_control_type_founding_cdf(df_clean)

    # Create operating colleges by region and decade plot
    create_regional_operating_colleges_by_decade(df_clean)

    # Create operating public colleges by region and decade plot
    create_regional_operating_public_colleges_by_decade(df_clean)

    # Create total operating colleges by decade plot
    create_total_operating_colleges_by_decade(df_clean, secdr_df)

    # Load population data and create per capita figures
    regional_pop = load_and_aggregate_population_data()
    create_colleges_per_capita_by_decade(df_clean, regional_pop)
    create_public_colleges_per_capita_by_decade(df_clean, regional_pop)
    create_junior_colleges_per_capita_by_decade(regional_pop)

    # Create regional capacity per capita histogram
    create_regional_capacity_per_capita_histogram(regional_pop)

    # Create LaTeX table of colleges by region and control type
    create_regional_control_latex_table(df_clean)

    # Create city timeline scatter plot
    create_city_timeline_scatter(df_clean)

    # Create county timeline scatter plot
    create_county_timeline_scatter(df_clean)

    # Create county analysis table and visualization
    create_county_analysis_table(df_clean)

    # Create capacity share by control type and region
    create_capacity_share_by_control_and_region(df_clean)

    # Create bar chart for 1930
    create_capacity_share_bar_chart(df_clean, year=1930)

    print("\nFounding years analysis complete!")

if __name__ == "__main__":
    main()