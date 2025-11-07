"""
State-Level College Attainment by Region

This script creates college attainment trends by region using pre-aggregated
state-level cohort data. It replicates the trend_college_attainment.py figure
but uses state_cohort_attainment_income.csv as the data source.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse
import statsmodels.formula.api as smf
import numpy as np


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


def aggregate_to_regions(df):
    """
    Aggregate state-level data to regional level.

    Parameters:
    -----------
    df : pd.DataFrame
        State-level data with columns: state, cohort_5year, college_count,
        total_count, hs_or_more_count, etc.

    Returns:
    --------
    pd.DataFrame
        Regional aggregates with recalculated college_rate and college_given_hs_rate
    """
    # Map states to regions
    df['region'] = df['state'].apply(map_state_to_region)

    # Filter out 'Other' region if any
    df = df[df['region'] != 'Other']

    # Aggregate by region and cohort
    regional_data = df.groupby(['region', 'cohort_5year']).agg(
        college_count=('college_count', 'sum'),
        total_count=('total_count', 'sum'),
        hs_or_more_count=('hs_or_more_count', 'sum')
    ).reset_index()

    # Recalculate college rate from aggregated counts
    regional_data['college_rate'] = (regional_data['college_count'] /
                                     regional_data['total_count']) * 100

    # Calculate college completion rate conditional on HS (weighted by hs_or_more_count)
    regional_data['college_given_hs_rate'] = (regional_data['college_count'] /
                                               regional_data['hs_or_more_count']) * 100

    return regional_data


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Create college attainment by region figure from state-level data.'
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

    # Filter to specified cohort range
    df = df[(df['cohort_5year'] >= args.cohort_min) &
            (df['cohort_5year'] <= args.cohort_max)]

    print(f"\nFiltered to cohorts {args.cohort_min}-{args.cohort_max}")
    print(f"Remaining observations: {len(df):,}")

    # Aggregate to regions
    print("\nAggregating to regions...")
    regional_data = aggregate_to_regions(df)

    # Sort by region and cohort
    regional_data = regional_data.sort_values(['region', 'cohort_5year'])

    print(f"\nProcessed {len(regional_data):,} regional 5-year cohort bins")
    print(f"Overall college attainment rate: {regional_data['college_count'].sum() / regional_data['total_count'].sum() * 100:.2f}%")

    # Print by region
    print("\nBy Region:")
    for region in ['Northeast', 'Midwest', 'South', 'West']:
        region_data = regional_data[regional_data['region'] == region]
        if len(region_data) > 0:
            total_college = region_data['college_count'].sum()
            total_pop = region_data['total_count'].sum()
            rate = (total_college / total_pop * 100) if total_pop > 0 else 0
            print(f"  {region}: {rate:.2f}% college attainment ({total_pop:,} individuals)")

    # Define consistent colors for regions (matching original script)
    region_colors = {
        'Northeast': '#1f77b4',  # blue
        'Midwest': '#ff7f0e',    # orange
        'South': '#2ca02c',      # green
        'West': '#d62728'        # red
    }

    # ========================================================================
    # Plot 1: Raw College Attainment Rates by Region
    # ========================================================================
    print("\n" + "="*60)
    print("Creating raw college attainment rate plot")
    print("="*60)

    fig, ax = plt.subplots(figsize=(12, 6))

    for region in ['Northeast', 'Midwest', 'South', 'West']:
        region_data = regional_data[regional_data['region'] == region]
        if len(region_data) > 0:
            ax.plot(region_data['cohort_5year'], region_data['college_rate'],
                   linewidth=2, marker='o', markersize=5, label=region,
                   color=region_colors[region])

    ax.set_xlabel('High School Cohort (5-Year Bins)', fontsize=12)
    ax.set_ylabel('College Attainment Rate (%)', fontsize=12)
    ax.set_title(f'College Attainment by High School Cohort and Region, {args.cohort_min}-{args.cohort_max}',
                fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save raw attainment figure
    raw_output_path = os.path.join(args.output, "state_college_attainment_by_cohort_region_raw.png")
    plt.savefig(raw_output_path, dpi=300, bbox_inches='tight')
    print(f"Raw attainment figure saved to: {raw_output_path}")

    plt.close()

    # ========================================================================
    # Plot 2: Regression Coefficients - Cohort x Region Interactions
    # ========================================================================
    print("\n" + "="*60)
    print("Running regression with cohort-region interactions")
    print("="*60)

    # Prepare data for regression
    reg_data = regional_data.copy()

    # Set Northeast and 1900 as reference categories
    reg_data['region_cat'] = pd.Categorical(reg_data['region'],
                                            categories=['Northeast', 'Midwest', 'South', 'West'])
    reg_data['cohort_cat'] = pd.Categorical(reg_data['cohort_5year'])

    # Run regression with full interactions
    # C() ensures categorical treatment with specified reference
    formula = 'college_rate ~ C(region_cat, Treatment(reference="Northeast")) * C(cohort_cat, Treatment(reference=1900))'
    model = smf.ols(formula, data=reg_data).fit()

    print("\nRegression Summary:")
    print(f"R-squared: {model.rsquared:.4f}")
    print(f"Number of observations: {model.nobs}")

    # Extract coefficients for interaction terms
    coef_data = []

    for param_name, coef in model.params.items():
        if ':' in param_name:  # Interaction terms
            # Parse the parameter name
            parts = param_name.split(':')

            # Extract region
            region_part = parts[0] if 'region_cat' in parts[0] else parts[1]
            if 'Midwest' in region_part:
                region = 'Midwest'
            elif 'South' in region_part:
                region = 'South'
            elif 'West' in region_part:
                region = 'West'
            else:
                continue

            # Extract cohort
            cohort_part = parts[1] if 'cohort_cat' in parts[1] else parts[0]
            try:
                cohort = int(cohort_part.split('[T.')[1].split(']')[0])
            except:
                continue

            # Get standard error and confidence interval
            se = model.bse[param_name]
            ci_lower = model.conf_int().loc[param_name, 0]
            ci_upper = model.conf_int().loc[param_name, 1]

            coef_data.append({
                'region': region,
                'cohort': cohort,
                'coefficient': coef,
                'se': se,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper
            })

    coef_df = pd.DataFrame(coef_data)

    print(f"\nExtracted {len(coef_df)} interaction coefficients")

    # Create coefficient plot
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot coefficients for each region
    for region in ['Midwest', 'South', 'West']:
        region_coefs = coef_df[coef_df['region'] == region].sort_values('cohort')

        if len(region_coefs) > 0:
            ax.plot(region_coefs['cohort'], region_coefs['coefficient'],
                   linewidth=2, marker='o', markersize=6, label=region,
                   color=region_colors[region])

            # Add confidence intervals as shaded area
            ax.fill_between(region_coefs['cohort'],
                          region_coefs['ci_lower'],
                          region_coefs['ci_upper'],
                          alpha=0.2, color=region_colors[region])

    # Add reference line at 0
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5,
              label='Northeast (reference)')

    ax.set_xlabel('High School Cohort (5-Year Bins)', fontsize=12)
    ax.set_ylabel('Coefficient (percentage points relative to Northeast, 1900)', fontsize=12)
    ax.set_title('Regional Differences in College Attainment Across Cohorts\n(Regression Coefficients: Region × Cohort Interactions)',
                fontsize=14)
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save coefficient plot
    coef_output_path = os.path.join(args.output, "state_college_attainment_regression_coefficients.png")
    plt.savefig(coef_output_path, dpi=300, bbox_inches='tight')
    print(f"\nRegression coefficient plot saved to: {coef_output_path}")

    plt.close()

    # Print sample coefficients
    print("\nSample coefficients (first 5 for each region):")
    for region in ['Midwest', 'South', 'West']:
        print(f"\n{region}:")
        region_coefs = coef_df[coef_df['region'] == region].sort_values('cohort').head(5)
        for _, row in region_coefs.iterrows():
            print(f"  Cohort {row['cohort']}: {row['coefficient']:+.3f} ({row['ci_lower']:+.3f}, {row['ci_upper']:+.3f})")

    # ========================================================================
    # Plot 3: College Completion Rate Conditional on HS by Region
    # ========================================================================
    print("\n" + "="*60)
    print("Creating college completion conditional on HS plot")
    print("="*60)

    fig, ax = plt.subplots(figsize=(12, 6))

    for region in ['Northeast', 'Midwest', 'South', 'West']:
        region_data = regional_data[regional_data['region'] == region]
        if len(region_data) > 0:
            ax.plot(region_data['cohort_5year'], region_data['college_given_hs_rate'],
                   linewidth=2, marker='o', markersize=5, label=region,
                   color=region_colors[region])

    ax.set_xlabel('High School Cohort (5-Year Bins)', fontsize=12)
    ax.set_ylabel('College Completion Rate | HS Completion (%)', fontsize=12)
    ax.set_title(f'College Completion (Conditional on HS) by Cohort and Region, {args.cohort_min}-{args.cohort_max}',
                fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save conditional college completion figure
    conditional_output_path = os.path.join(args.output, "state_college_given_hs_by_region.png")
    plt.savefig(conditional_output_path, dpi=300, bbox_inches='tight')
    print(f"College given HS figure saved to: {conditional_output_path}")

    plt.close()

    # Print summary statistics for college given HS
    print("\nCollege Completion | HS Completion by Region:")
    for region in ['Northeast', 'Midwest', 'South', 'West']:
        region_data = regional_data[regional_data['region'] == region]
        if len(region_data) > 0:
            total_college = region_data['college_count'].sum()
            total_hs = region_data['hs_or_more_count'].sum()
            rate = (total_college / total_hs * 100) if total_hs > 0 else 0
            print(f"  {region}: {rate:.2f}% ({total_college:,} college / {total_hs:,} HS+)")

    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)
