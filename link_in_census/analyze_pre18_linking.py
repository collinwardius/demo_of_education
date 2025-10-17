"""
Analyze linking from 1940 census (age 25+) to observations before age 18.

This script determines:
1. How many people age 25+ in 1940 can be linked to at least one observation before age 18
2. The distribution of pre-18 observations per person
3. Examples of multiple pre-18 observations
4. Which census years provide the pre-18 observations
"""

import pandas as pd
import numpy as np

# Load the cleaned data
data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/born_georgia_linked_census_for_debugging_cleaned.csv"
print("Loading cleaned census data...")
df = pd.read_csv(data_path)
print(f"Loaded {len(df):,} total observations")

# Get all individuals observed in 1940 who are age 25 or older
df_1940 = df[df['YEAR'] == 1940][['HIK', 'AGE', 'BIRTHYR']].drop_duplicates()
df_1940_25plus = df_1940[df_1940['AGE'] >= 25].copy()
print(f"\nUnique individuals in 1940 (all ages): {len(df_1940):,}")
print(f"Unique individuals in 1940 (age 25+): {len(df_1940_25plus):,}")

# Get all observations where people are under 18
df_under18 = df[df['AGE'] < 18].copy()
print(f"\nTotal observations with AGE < 18: {len(df_under18):,}")
print(f"Unique individuals observed under 18: {df_under18['HIK'].nunique():,}")

# For each person age 25+ in 1940, find all their observations when they were under 18
hik_1940_25plus = set(df_1940_25plus['HIK'].unique())
hik_under18 = set(df_under18['HIK'].unique())

# Find intersection: people age 25+ in 1940 who have at least one under-18 observation
linked_to_pre18 = hik_1940_25plus.intersection(hik_under18)

n_linked = len(linked_to_pre18)
n_total_1940_25plus = len(hik_1940_25plus)
pct_linked = (n_linked / n_total_1940_25plus) * 100 if n_total_1940_25plus > 0 else 0

print("\n" + "="*70)
print("LINKING TO PRE-18 OBSERVATIONS (AGE 25+ IN 1940)")
print("="*70)
print(f"People age 25+ in 1940: {n_total_1940_25plus:,}")
print(f"  With at least one pre-18 obs: {n_linked:,} ({pct_linked:.2f}%)")
print(f"  With no pre-18 obs: {n_total_1940_25plus - n_linked:,} ({100-pct_linked:.2f}%)")

# Count number of pre-18 observations per person
print("\n" + "="*70)
print("DISTRIBUTION OF PRE-18 OBSERVATIONS PER PERSON (AGE 25+ IN 1940)")
print("="*70)

# For each HIK in 1940 (age 25+), count their pre-18 observations
pre18_counts = df_under18.groupby('HIK').size().reset_index(name='n_pre18_obs')

# Merge with 1940 sample (age 25+)
df_1940_analysis = df_1940_25plus[['HIK', 'AGE', 'BIRTHYR']].drop_duplicates()
df_1940_analysis = df_1940_analysis.merge(pre18_counts, on='HIK', how='left')
df_1940_analysis['n_pre18_obs'] = df_1940_analysis['n_pre18_obs'].fillna(0).astype(int)

# Show distribution
print("\nNumber of pre-18 observations per person:")
print(f"{'# Pre-18 Obs':<15} {'# People':<15} {'% of Age 25+ Sample':<25}")
print("-"*70)

obs_distribution = df_1940_analysis['n_pre18_obs'].value_counts().sort_index()
for n_obs, count in obs_distribution.items():
    pct = (count / len(df_1940_analysis)) * 100
    print(f"{n_obs:<15} {count:>12,}   {pct:>20.2f}%")

# Summary statistics
print("\nSummary statistics for pre-18 observations:")
print(f"  Mean: {df_1940_analysis['n_pre18_obs'].mean():.2f}")
print(f"  Median: {df_1940_analysis['n_pre18_obs'].median():.0f}")
print(f"  Max: {df_1940_analysis['n_pre18_obs'].max():.0f}")
print(f"  People with 1+ pre-18 obs: {(df_1940_analysis['n_pre18_obs'] > 0).sum():,} "
      f"({(df_1940_analysis['n_pre18_obs'] > 0).mean()*100:.2f}%)")
print(f"  People with 2+ pre-18 obs: {(df_1940_analysis['n_pre18_obs'] >= 2).sum():,} "
      f"({(df_1940_analysis['n_pre18_obs'] >= 2).mean()*100:.2f}%)")
print(f"  People with 3+ pre-18 obs: {(df_1940_analysis['n_pre18_obs'] >= 3).sum():,} "
      f"({(df_1940_analysis['n_pre18_obs'] >= 3).mean()*100:.2f}%)")

# Age distribution in 1940 for people with/without pre-18 links
print("\n" + "="*70)
print("AGE DISTRIBUTION IN 1940 BY LINKING STATUS")
print("="*70)

df_1940_analysis['has_pre18_link'] = df_1940_analysis['n_pre18_obs'] > 0

print("\nAge statistics in 1940 (age 25+ sample):")
print(f"  All people age 25+:")
print(f"    Mean age: {df_1940_analysis['AGE'].mean():.1f}")
print(f"    Median age: {df_1940_analysis['AGE'].median():.0f}")
print(f"    Min age: {df_1940_analysis['AGE'].min():.0f}")
print(f"    Max age: {df_1940_analysis['AGE'].max():.0f}")

linked = df_1940_analysis[df_1940_analysis['has_pre18_link']]
unlinked = df_1940_analysis[~df_1940_analysis['has_pre18_link']]

print(f"\n  People WITH pre-18 links:")
print(f"    Mean age: {linked['AGE'].mean():.1f}")
print(f"    Median age: {linked['AGE'].median():.0f}")

print(f"\n  People WITHOUT pre-18 links:")
print(f"    Mean age: {unlinked['AGE'].mean():.1f}")
print(f"    Median age: {unlinked['AGE'].median():.0f}")

# Show examples of people with multiple pre-18 observations
print("\n" + "="*70)
print("EXAMPLES: People (Age 25+ in 1940) with Multiple Pre-18 Observations")
print("="*70)

# Get people with 2+ pre-18 observations
multi_pre18 = df_1940_analysis[df_1940_analysis['n_pre18_obs'] >= 2]['HIK'].head(5)

for hik in multi_pre18:
    person_data = df[df['HIK'] == hik][['YEAR', 'AGE', 'BIRTHYR', 'STATEFIP', 'COUNTYICP']].sort_values('YEAR')
    print(f"\nPerson HIK: {hik}")
    print(f"  Birth year: {person_data['BIRTHYR'].iloc[0]}")
    obs_1940 = person_data[person_data['YEAR'] == 1940]
    if len(obs_1940) > 0:
        print(f"  Age in 1940: {obs_1940['AGE'].iloc[0]}")
    print(f"  Total pre-18 observations: {(person_data['AGE'] < 18).sum()}")
    print(f"  All observations:")
    for idx, row in person_data.iterrows():
        under18_flag = " <- UNDER 18" if row['AGE'] < 18 else ""
        year_1940_flag = " (1940 obs)" if row['YEAR'] == 1940 else ""
        print(f"    {row['YEAR']}: Age {row['AGE']}, State {row['STATEFIP']}, County {row['COUNTYICP']}{under18_flag}{year_1940_flag}")

# Analyze by census year: which censuses provide pre-18 observations for age 25+ sample?
print("\n" + "="*70)
print("PRE-18 OBSERVATIONS BY CENSUS YEAR (for Age 25+ in 1940 sample)")
print("="*70)

# Filter under-18 observations to only those who are age 25+ in 1940
df_under18_linked = df_under18[df_under18['HIK'].isin(hik_1940_25plus)]

pre18_by_year = df_under18_linked.groupby('YEAR').agg({
    'HIK': 'nunique',
    'YEAR': 'size'
}).rename(columns={'HIK': 'unique_people', 'YEAR': 'total_obs'})

print("\nPre-18 observations (for age 25+ in 1940) available in each census:")
print(f"{'Census Year':<15} {'Unique People':<20} {'Total Observations':<20}")
print("-"*70)
for year, row in pre18_by_year.iterrows():
    print(f"{year:<15} {row['unique_people']:>15,}   {row['total_obs']:>20,}")

# Age distribution in pre-18 observations (for age 25+ in 1940 sample)
print("\n" + "="*70)
print("AGE DISTRIBUTION IN PRE-18 OBSERVATIONS (for Age 25+ in 1940 sample)")
print("="*70)

age_dist = df_under18_linked['AGE'].value_counts().sort_index()
print("\nCount of observations by age (under 18, for those age 25+ in 1940):")
print(f"{'Age':<10} {'# Observations':<20}")
print("-"*40)
for age, count in age_dist.items():
    print(f"{age:<10} {count:>15,}")

# Create comparison table of means between linked and unlinked individuals
print("\n" + "="*70)
print("COMPARISON OF MEANS: LINKED VS UNLINKED (1940 Observables)")
print("="*70)

# Merge full 1940 data with linking status
df_1940_full = df[df['YEAR'] == 1940].copy()
df_1940_full = df_1940_full[df_1940_full['AGE'] >= 25]  # Only age 25+

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

# Print to console
print("\nComparison of Means (1940 Characteristics):")
print(f"Sample sizes: Linked = {len(linked_group):,}, Unlinked = {len(unlinked_group):,}")
print("\n" + "-"*100)
print(f"{'Variable':<20} {'Linked Mean':<15} {'Unlinked Mean':<15} {'Difference':<15}")
print("-"*100)
for _, row in comparison_df.iterrows():
    print(f"{row['Variable']:<20} {row['Linked Mean']:>12.3f}   {row['Unlinked Mean']:>12.3f}   {row['Difference']:>12.3f}")

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
output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables/linked_vs_unlinked_comparison.tex"
with open(output_path, 'w') as f:
    f.write(latex_output)

print(f"\n\nLaTeX table saved to: {output_path}")

print("\n" + "="*70)
print("Analysis complete!")
print("="*70)
