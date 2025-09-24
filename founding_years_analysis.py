import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_founding_years_cdf():
    """Create CDF of college founding years using 1928 data."""

    # Load data
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/cleaned_appended_college_data.csv"
    df = pd.read_csv(data_path)

    # Filter for 1928 data only
    df_1928 = df[df['year'] == 1928].copy()

    # Clean founding years - exclude missing or zero values
    df_1928['founding_year'] = pd.to_numeric(df_1928['year_first_opening'], errors='coerce')
    df_clean = df_1928[(df_1928['founding_year'] > 0) & (df_1928['founding_year'].notna())].copy()

    print(f"Total colleges in 1928: {len(df_1928)}")
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

    plt.title('Cumulative Distribution of College Founding Years\n(Colleges existing in 1928)',
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
    """Create regional CDF of college founding years."""

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
    df_clean['region'] = df_clean['state'].map(regional_mapping)

    # Check for unmapped states
    unmapped = df_clean[df_clean['region'].isna()]['state'].unique()
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

    regions = df_clean['region'].unique()
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

    plt.title('Cumulative Distribution of College Founding Years by Region\n(Colleges existing in 1928)',
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
    for region in sorted(regions):
        if pd.notna(region):
            regional_median = df_clean[df_clean['region'] == region]['founding_year'].median()
            print(f"  {region}: {int(regional_median)}")

def create_zoomed_founding_cdf(df_clean):
    """Create zoomed CDF of college founding years from 1800 onwards."""

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

    plt.title('Cumulative Distribution of College Founding Years (1800-1928)\n(Colleges existing in 1928)',
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
    """Create zoomed regional CDF of college founding years from 1800 onwards."""

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

    df_1800_plus['region'] = df_1800_plus['state'].map(regional_mapping)

    # Also map regions for the full dataset to get pre-1800 counts by region
    df_clean['region'] = df_clean['state'].map(regional_mapping)

    # Get regional statistics for 1800+ data
    regional_stats = df_1800_plus.groupby('region').agg({
        'founding_year': ['count', 'min', 'max', 'mean']
    }).round(1)
    regional_stats.columns = ['Count', 'Min_Year', 'Max_Year', 'Mean_Year']
    print("\nRegional Statistics (1800+):")
    print(regional_stats)

    # Create zoomed regional CDF plot
    plt.figure(figsize=(14, 8))

    regions = df_1800_plus['region'].unique()
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

    plt.title('Cumulative Distribution of College Founding Years by Region (1800-1928)\n(Colleges existing in 1928)',
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

def main():
    print("Creating founding years CDF analysis...")

    # Create overall CDF
    df_clean = create_founding_years_cdf()

    # Create regional CDF
    create_regional_founding_cdf(df_clean)

    # Create zoomed versions from 1800 onwards
    create_zoomed_founding_cdf(df_clean)
    create_zoomed_regional_founding_cdf(df_clean)

    print("\nFounding years analysis complete!")

if __name__ == "__main__":
    main()