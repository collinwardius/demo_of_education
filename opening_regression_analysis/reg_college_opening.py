"""
Performs regression analysis of college openings
Translated from Stata to Python
Collin Wardius
October 22, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# Try to import pyfixest (best option for replicating reghdfe)
try:
    import pyfixest as pf
    USE_PYFIXEST = True
except ImportError:
    print("Warning: pyfixest not installed. Install with: pip install pyfixest")
    print("Falling back to statsmodels (results may differ from Stata)")
    USE_PYFIXEST = False
    from statsmodels.api import OLS
    from statsmodels.tools import add_constant

# Set data path
data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/data_from_cluster/"
output_figures_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"

# Create output directory if it doesn't exist
os.makedirs(output_figures_path, exist_ok=True)

print("=" * 80)
print("Loading data and preparing for regression analysis...")
print("=" * 80)

# Load data
df = pd.read_stata(os.path.join(data_path, "cleaned_opening_regression_data.dta"))

# Restrict to treatment cohorts around the college founding
df = df[df['treatment_cohort'].between(-8, 8)].copy()

# Create post_founding indicator
df['post_founding'] = (df['treatment_cohort'] >= 0).astype(int)

# Get list of unique colleges
colleges = df['college_name'].unique()
print(f"\nFound {len(colleges)} unique colleges")

# Initialize results storage
results_model1 = []
results_model2 = []

print("\n" + "=" * 80)
print("Running regressions for each college...")
print("=" * 80)

# Loop over each college
for i, college in enumerate(colleges, 1):
    print(f"\n[{i}/{len(colleges)}] Processing: {college}")

    # Filter data for this college
    df_college = df[df['college_name'] == college].copy()

    # Check if we have enough data
    if len(df_college) < 50 or df_college['post_founding'].sum() < 10:
        print(f"  -> Skipping (insufficient data: n={len(df_college)})")
        continue

    try:
        if USE_PYFIXEST:
            # Model 1: Basic specification with fixed effects
            # reghdfe college post_founding, absorb(g_state_county_pre_18 nativity race hispan mbpl fbpl) vce(cl hik)
            model1 = pf.feols(
                "college ~ post_founding | g_state_county_pre_18 + nativity + race + hispan + mbpl + fbpl",
                data=df_college,
                vcov={'CRV1': 'hik'}
            )

            coef1 = model1.coef().loc['post_founding']
            se1 = model1.se().loc['post_founding']
            ci1_low = coef1 - 1.96 * se1
            ci1_high = coef1 + 1.96 * se1

            results_model1.append({
                'college': college,
                'coefficient': coef1,
                'std_error': se1,
                'ci_low': ci1_low,
                'ci_high': ci1_high,
                'n_obs': len(df_college)
            })

            print(f"  -> Model 1: β={coef1:.4f} (SE={se1:.4f})")

            # Model 2: With county-specific trends
            # reghdfe college post_founding, absorb(g_state_county_pre_18 g_state_county_pre_18#c.treatment_cohort nativity race hispan mbpl fbpl) vce(cl hik)
            try:
                # Use i() syntax for interactions in pyfixest
                model2 = pf.feols(
                    "college ~ post_founding | g_state_county_pre_18 + nativity + race + hispan + mbpl + fbpl + i(g_state_county_pre_18, treatment_cohort, ref=0)",
                    data=df_college,
                    vcov={'CRV1': 'hik'}
                )

                coef2 = model2.coef().loc['post_founding']
                se2 = model2.se().loc['post_founding']
                ci2_low = coef2 - 1.96 * se2
                ci2_high = coef2 + 1.96 * se2

                results_model2.append({
                    'college': college,
                    'coefficient': coef2,
                    'std_error': se2,
                    'ci_low': ci2_low,
                    'ci_high': ci2_high,
                    'n_obs': len(df_college)
                })

                print(f"  -> Model 2: β={coef2:.4f} (SE={se2:.4f})")
            except Exception as e2:
                print(f"  -> Model 2: Failed ({str(e2)[:50]})")

        else:
            # Fallback using statsmodels with manual fixed effects
            # This is a simplified version and may not exactly match Stata
            print("  -> Using simplified statsmodels approach (may differ from Stata)")

            # Create dummy variables for fixed effects
            fe_vars = ['g_state_county_pre_18', 'nativity', 'race', 'hispan', 'mbpl', 'fbpl']
            df_college_dummies = pd.get_dummies(df_college[fe_vars], drop_first=True)

            # Model 1
            X1 = pd.concat([df_college[['post_founding']], df_college_dummies], axis=1)
            y = df_college['college']

            model1 = OLS(y, add_constant(X1)).fit(cov_type='cluster', cov_kwds={'groups': df_college['hik']})

            coef1 = model1.params['post_founding']
            se1 = model1.bse['post_founding']
            ci1_low = model1.conf_int().loc['post_founding', 0]
            ci1_high = model1.conf_int().loc['post_founding', 1]

            results_model1.append({
                'college': college,
                'coefficient': coef1,
                'std_error': se1,
                'ci_low': ci1_low,
                'ci_high': ci1_high,
                'n_obs': len(df_college)
            })

            print(f"  -> Model 1: β={coef1:.4f} (SE={se1:.4f})")

    except Exception as e:
        print(f"  -> Error: {str(e)}")
        continue

# Convert results to DataFrames
df_results_model1 = pd.DataFrame(results_model1)
df_results_model2 = pd.DataFrame(results_model2)

print("\n" + "=" * 80)
print(f"Successfully estimated {len(results_model1)} regressions for Model 1")
print(f"Successfully estimated {len(results_model2)} regressions for Model 2")
print("=" * 80)

# Create figures
def create_coefficient_plot(results_df, model_name, filename):
    """Create a coefficient plot with confidence intervals"""

    # Sort by coefficient value
    results_df = results_df.sort_values('coefficient').reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, max(8, len(results_df) * 0.3)))

    # Plot coefficients and confidence intervals
    y_positions = range(len(results_df))
    ax.scatter(results_df['coefficient'], y_positions, s=80, color='steelblue', zorder=3)

    # Add confidence intervals
    for i, row in results_df.iterrows():
        ax.plot([row['ci_low'], row['ci_high']], [i, i],
                color='steelblue', linewidth=2, alpha=0.6, zorder=2)

    # Add vertical line at 0
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1, alpha=0.7, zorder=1)

    # Formatting
    ax.set_yticks(y_positions)
    ax.set_yticklabels(results_df['college'], fontsize=8)
    ax.set_xlabel('Coefficient on post_founding', fontsize=11)
    ax.set_title(f'{model_name}\nEffect of College Opening on College Attendance', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3, linestyle=':', linewidth=0.5)

    plt.tight_layout()

    # Save figure
    output_path = os.path.join(output_figures_path, filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved to: {output_path}")
    plt.close()

# Create Model 1 figure
if len(df_results_model1) > 0:
    create_coefficient_plot(df_results_model1, 'Model 1: Basic Specification', 'college_opening_model1.png')

# Create Model 2 figure
if len(df_results_model2) > 0:
    create_coefficient_plot(df_results_model2, 'Model 2: With County-Specific Trends', 'college_opening_model2.png')

print("\n" + "=" * 80)
print("Analysis complete!")
print("=" * 80)
