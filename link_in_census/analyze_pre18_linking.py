"""
Generate LaTeX comparison table of linked vs unlinked individuals.

This script creates a table comparing 1940 characteristics between:
- Individuals age 25-70 in 1940 who can be linked to pre-18 observations
- Individuals age 25-70 in 1940 who cannot be linked to pre-18 observations

Usage:
    python analyze_pre18_linking.py <input_path> [output_path]

Arguments:
    input_path: Path to cleaned census data (CSV or Parquet)
    output_path: (Optional) Path to save LaTeX table
                 Defaults to: /Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables/linked_vs_unlinked_comparison.tex
"""

import pandas as pd
import sys
import os

# Parse command-line arguments
if len(sys.argv) < 2:
    print("Error: Missing required arguments")
    print("\nUsage:")
    print("  python analyze_pre18_linking.py <input_path> [output_path]")
    print("\nArguments:")
    print("  input_path:  Path to cleaned census data (CSV or Parquet)")
    print("  output_path: (Optional) Path to save LaTeX table")
    sys.exit(1)

data_path = sys.argv[1]

# Default output path (can be overridden)
default_output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables/linked_vs_unlinked_comparison.tex"
output_path = sys.argv[2] if len(sys.argv) > 2 else default_output_path

# Load the cleaned data
print("Loading cleaned census data...")
print(f"Input file: {data_path}")

# Detect input file format
input_ext = os.path.splitext(data_path)[1].lower()
if input_ext == '.parquet':
    print("Reading Parquet format...")
    df = pd.read_parquet(data_path)
elif input_ext == '.csv':
    print("Reading CSV format...")
    df = pd.read_csv(data_path)
else:
    print(f"Warning: Unrecognized file extension '{input_ext}', assuming CSV...")
    df = pd.read_csv(data_path)

print(f"Loaded {len(df):,} total observations")

# Identify individuals age 25-70 in 1940
df_1940 = df[df['YEAR'] == 1940][['HIK', 'AGE', 'BIRTHYR']].drop_duplicates()
df_1940_25to70 = df_1940[(df_1940['AGE'] >= 25) & (df_1940['AGE'] <= 70)].copy()

# Get all observations where people are under 18
df_under18 = df[df['AGE'] < 18].copy()

# Find individuals with pre-18 observations
hik_1940_25to70 = set(df_1940_25to70['HIK'].unique())
hik_under18 = set(df_under18['HIK'].unique())
linked_hiks = hik_1940_25to70.intersection(hik_under18)

# Count pre-18 observations per person
pre18_counts = df_under18.groupby('HIK').size().reset_index(name='n_pre18_obs')
df_1940_analysis = df_1940_25to70[['HIK', 'AGE', 'BIRTHYR']].drop_duplicates()
df_1940_analysis = df_1940_analysis.merge(pre18_counts, on='HIK', how='left')
df_1940_analysis['n_pre18_obs'] = df_1940_analysis['n_pre18_obs'].fillna(0).astype(int)
df_1940_analysis['has_pre18_link'] = df_1940_analysis['n_pre18_obs'] > 0

# Merge full 1940 data with linking status
df_1940_full = df[df['YEAR'] == 1940].copy()
df_1940_full = df_1940_full[(df_1940_full['AGE'] >= 25) & (df_1940_full['AGE'] <= 70)]  # Only age 25-70

# Add linking status
linking_status = df_1940_analysis[['HIK', 'has_pre18_link', 'n_pre18_obs']].copy()
df_1940_full = df_1940_full.merge(linking_status, on='HIK', how='left')
df_1940_full['has_pre18_link'] = df_1940_full['has_pre18_link'].fillna(False)

# Select only key observables for comparison
selected_cols = ['SEX', 'AGE', 'college', 'MARST', 'race_white']
numeric_cols = [col for col in selected_cols if col in df_1940_full.columns]

# Calculate means for linked and unlinked groups
linked_group = df_1940_full[df_1940_full['has_pre18_link'] == True]
unlinked_group = df_1940_full[df_1940_full['has_pre18_link'] == False]

comparison_data = []
# Variables to multiply by 100 for percentage interpretation
pct_vars = ['SEX', 'college', 'MARST', 'race_white']

for col in numeric_cols:
    if col in df_1940_full.columns:
        linked_mean = linked_group[col].mean()
        unlinked_mean = unlinked_group[col].mean()
        diff = linked_mean - unlinked_mean

        # Calculate standard errors
        linked_se = linked_group[col].sem()
        unlinked_se = unlinked_group[col].sem()

        # Multiply by 100 for percentage interpretation for specific variables
        if col in pct_vars:
            linked_mean *= 100
            unlinked_mean *= 100
            diff *= 100
            linked_se *= 100
            unlinked_se *= 100

        comparison_data.append({
            'Variable': col,
            'Linked Mean': linked_mean,
            'Linked SE': linked_se,
            'Unlinked Mean': unlinked_mean,
            'Unlinked SE': unlinked_se,
            'Difference': diff
        })

comparison_df = pd.DataFrame(comparison_data)

# Create LaTeX table with better variable names
var_name_mapping = {
    'SEX': 'Female (\\%)',
    'AGE': 'Age',
    'college': 'College (\\%)',
    'MARST': 'Married (\\%)',
    'race_white': 'White (\\%)'
}

latex_output = "\\begin{table}[htbp]\n"
latex_output += "\\centering\n"
latex_output += "\\caption{Comparison of 1940 Characteristics: Linked vs Unlinked Individuals}\n"
latex_output += "\\label{tab:linked_vs_unlinked}\n"
latex_output += "\\begin{tabular}{lccc}\n"
latex_output += "\\hline\\hline\n"
latex_output += " & \\textcolor{green}{Linked} & \\textcolor{red}{Unlinked} & Difference \\\\\n"
latex_output += " & \\textcolor{green}{Mean} & \\textcolor{red}{Mean} & \\\\\n"
latex_output += "\\hline\n"

for _, row in comparison_df.iterrows():
    var_code = row['Variable']
    var_name = var_name_mapping.get(var_code, var_code.replace('_', '\\_'))
    linked_str = f"{row['Linked Mean']:.1f}"
    unlinked_str = f"{row['Unlinked Mean']:.1f}"
    diff_str = f"{row['Difference']:.1f}"
    latex_output += f"{var_name} & {linked_str} & {unlinked_str} & {diff_str} \\\\\n"

latex_output += "\\hline\n"
# Calculate percentages of total sample
total_sample = len(linked_group) + len(unlinked_group)
linked_pct = (len(linked_group) / total_sample) * 100
unlinked_pct = (len(unlinked_group) / total_sample) * 100
latex_output += f"N & {len(linked_group):,} & {len(unlinked_group):,} & \\\\\n"
latex_output += f"\\% of Total & {linked_pct:.1f}\\% & {unlinked_pct:.1f}\\% & \\\\\n"
latex_output += "\\hline\\hline\n"
latex_output += "\\end{tabular}\n"
latex_output += "\\begin{tablenotes}\n"
latex_output += "\\small\n"
latex_output += "\\item Note: This table compares mean characteristics in 1940 for individuals age between 25 and 70 who were successfully linked to pre-age 18 observations versus those who were not linked.\n"
latex_output += "\\end{tablenotes}\n"
latex_output += "\\end{table}\n"

# Save LaTeX table
print(f"\nSaving LaTeX table to: {output_path}")
with open(output_path, 'w') as f:
    f.write(latex_output)

print(f"LaTeX table saved to: {output_path}")
print("LaTeX table generation complete!")
