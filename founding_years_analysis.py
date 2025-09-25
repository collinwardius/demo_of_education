import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_founding_years_cdf():
    """Create CDF of college founding years for colleges existing as of 1944."""

    # Load data
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/combined_college_blue_book_data.csv"
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

def main():
    print("Creating founding years CDF analysis...")

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

    # Create LaTeX table of colleges by region and control type
    create_regional_control_latex_table(df_clean)

    print("\nFounding years analysis complete!")

if __name__ == "__main__":
    main()