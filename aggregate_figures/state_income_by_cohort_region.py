"""
State-Level Mean Income by Region

This script creates mean income wage trends by region using pre-aggregated
state-level cohort data. It uses weighted averages by employed_count when
aggregating to the regional level.
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
    Aggregate state-level data to regional level using weighted averages.

    Parameters:
    -----------
    df : pd.DataFrame
        State-level data with columns: state, cohort_5year, mean_incwage,
        employed_count, college_count, total_count, etc.

    Returns:
    --------
    pd.DataFrame
        Regional aggregates with weighted mean_incwage and college_rate
    """
    # Map states to regions
    df['region'] = df['state'].apply(map_state_to_region)

    # Filter out 'Other' region if any
    df = df[df['region'] != 'Other']

    # Calculate weighted income (income * employed_count)
    df['weighted_income'] = df['mean_incwage'] * df['employed_count']

    # Aggregate by region and cohort
    regional_data = df.groupby(['region', 'cohort_5year']).agg(
        weighted_income_sum=('weighted_income', 'sum'),
        employed_count=('employed_count', 'sum'),
        college_count=('college_count', 'sum'),
        total_count=('total_count', 'sum')
    ).reset_index()

    # Calculate weighted mean income
    regional_data['mean_incwage'] = (regional_data['weighted_income_sum'] /
                                     regional_data['employed_count'])

    # Calculate college rate
    regional_data['college_rate'] = (regional_data['college_count'] /
                                     regional_data['total_count']) * 100

    # Drop the intermediate weighted_income_sum column
    regional_data = regional_data.drop(columns=['weighted_income_sum'])

    return regional_data


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Create mean income by region figure from state-level data.'
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

    # Calculate overall weighted mean income
    total_weighted_income = (df['mean_incwage'] * df['employed_count']).sum()
    total_employed = df['employed_count'].sum()
    overall_mean_income = total_weighted_income / total_employed
    print(f"Overall mean income wage: ${overall_mean_income:,.2f}")

    # Print by region
    print("\nBy Region:")
    for region in ['Northeast', 'Midwest', 'South', 'West']:
        region_data = regional_data[regional_data['region'] == region]
        if len(region_data) > 0:
            total_weighted = (region_data['mean_incwage'] * region_data['employed_count']).sum()
            total_employed_region = region_data['employed_count'].sum()
            mean_income = total_weighted / total_employed_region if total_employed_region > 0 else 0
            print(f"  {region}: ${mean_income:,.2f} mean income ({total_employed_region:,} employed)")

    # Save regional income and college attainment data to CSV
    output_data = regional_data[['region', 'cohort_5year', 'mean_incwage', 'college_rate']].copy()
    output_data = output_data.rename(columns={'cohort_5year': 'cohort', 'mean_incwage': 'incwage', 'college_rate': 'college_attainment'})

    census_output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census"
    os.makedirs(census_output_dir, exist_ok=True)

    csv_output_path = os.path.join(census_output_dir, "regional_income_by_cohort.csv")
    output_data.to_csv(csv_output_path, index=False)
    print(f"\nRegional income and college attainment data saved to: {csv_output_path}")

    # Define consistent colors for regions (matching original script)
    region_colors = {
        'Northeast': '#1f77b4',  # blue
        'Midwest': '#ff7f0e',    # orange
        'South': '#2ca02c',      # green
        'West': '#d62728'        # red
    }

    # Create plot: Mean income by region
    fig, ax = plt.subplots(figsize=(12, 6))

    for region in ['Northeast', 'Midwest', 'South', 'West']:
        region_data = regional_data[regional_data['region'] == region]
        if len(region_data) > 0:
            ax.plot(region_data['cohort_5year'], region_data['mean_incwage'],
                   linewidth=2, marker='o', markersize=5, label=region,
                   color=region_colors[region])

    ax.set_xlabel('High School Cohort (5-Year Bins)', fontsize=12)
    ax.set_ylabel('Mean Income Wage ($)', fontsize=12)
    ax.set_title(f'Mean Income Wage by High School Cohort and Region, {args.cohort_min}-{args.cohort_max}',
                fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    plt.tight_layout()

    # Save figure
    output_path = os.path.join(args.output, "state_income_by_cohort_region.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved to: {output_path}")

    plt.close()

    # ========================================================================
    # Plot 2: Regression Coefficients - Cohort x Region Interactions
    # ========================================================================
    print("\n" + "="*60)
    print("Running regression with cohort-region interactions (log income)")
    print("="*60)

    # Prepare data for regression
    reg_data = regional_data.copy()

    # Transform income to log scale
    reg_data['log_incwage'] = np.log(reg_data['mean_incwage'])

    # Set Northeast and 1900 as reference categories
    reg_data['region_cat'] = pd.Categorical(reg_data['region'],
                                            categories=['Northeast', 'Midwest', 'South', 'West'])
    reg_data['cohort_cat'] = pd.Categorical(reg_data['cohort_5year'])

    # Run regression with full interactions using log income
    # C() ensures categorical treatment with specified reference
    formula = 'log_incwage ~ C(region_cat, Treatment(reference="Northeast")) * C(cohort_cat, Treatment(reference=1900))'
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
    ax.set_ylabel('Coefficient (log points relative to Northeast, 1900)', fontsize=12)
    ax.set_title('Regional Differences in Log Mean Income Across Cohorts\n(Regression Coefficients: Region × Cohort Interactions)',
                fontsize=14)
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save coefficient plot
    coef_output_path = os.path.join(args.output, "state_income_regression_coefficients_log.png")
    plt.savefig(coef_output_path, dpi=300, bbox_inches='tight')
    print(f"\nRegression coefficient plot saved to: {coef_output_path}")

    plt.close()

    # Print sample coefficients
    print("\nSample coefficients (first 5 for each region):")
    for region in ['Midwest', 'South', 'West']:
        print(f"\n{region}:")
        region_coefs = coef_df[coef_df['region'] == region].sort_values('cohort').head(5)
        for _, row in region_coefs.iterrows():
            pct_change = (np.exp(row['coefficient']) - 1) * 100
            print(f"  Cohort {row['cohort']}: {row['coefficient']:+.4f} log points ({pct_change:+.2f}% change)")

    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)

