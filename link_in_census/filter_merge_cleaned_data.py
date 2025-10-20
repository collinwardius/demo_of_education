"""
Filter cleaned census data to keep only individuals who can be linked to pre-18 observations.

This script:
1. Loads the cleaned census data
2. Identifies individuals age 25-70 in 1940
3. Finds which individuals have at least one observation when AGE < 18
4. Keeps only those individuals (all their observations across all census years)
5. Saves the filtered dataset

Usage:
    python filter_merge_cleaned_data.py <input_path> <output_path> [treatment_path]

Arguments:
    input_path: Path to cleaned census data CSV
    output_path: Path to save filtered and merged census data CSV
    treatment_path: (Optional) Path to county treatment status CSV
                   Defaults to: /Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/county_treatment_status.csv

Input: cleaned census data
Output: linked-only census data
"""

import pandas as pd
import sys

# Parse command-line arguments
if len(sys.argv) < 3:
    print("Error: Missing required arguments")
    print("\nUsage:")
    print("  python filter_merge_cleaned_data.py <input_path> <output_path> [treatment_path]")
    print("\nArguments:")
    print("  input_path:     Path to cleaned census data CSV")
    print("  output_path:    Path to save filtered and merged census data CSV")
    print("  treatment_path: (Optional) Path to county treatment status CSV")
    sys.exit(1)

input_path = sys.argv[1]
output_path = sys.argv[2]

# Default treatment path (can be overridden)
default_treatment_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/county_treatment_status.csv"
treatment_path = sys.argv[3] if len(sys.argv) > 3 else default_treatment_path


print("="*70)
print("FILTER FOR LINKED INDIVIDUALS ONLY")
print("="*70)

# Load the cleaned data
print("\nLoading cleaned census data...")
print(f"Input file: {input_path}")
df = pd.read_csv(input_path)
print(f"Loaded {len(df):,} total observations")
print(f"Unique individuals: {df['HIK'].nunique():,}")
print(df.columns)

# Step 1: Get all individuals observed in 1940 who are age 25-70
print("\n" + "="*70)
print("IDENTIFYING INDIVIDUALS IN 1940 (AGE 25-70)")
print("="*70)
df_1940 = df[df['YEAR'] == 1940][['HIK', 'AGE', 'BIRTHYR']].drop_duplicates()
df_1940_25to70 = df_1940[(df_1940['AGE'] >= 25) & (df_1940['AGE'] <= 70)].copy()
print(f"Unique individuals in 1940 (age 25-70): {len(df_1940_25to70):,}")

# Step 2: Get all observations where people are under 18
print("\n" + "="*70)
print("IDENTIFYING PRE-18 OBSERVATIONS")
print("="*70)
df_under18 = df[df['AGE'] < 18].copy()
print(f"Total observations with AGE < 18: {len(df_under18):,}")
print(f"Unique individuals observed under 18: {df_under18['HIK'].nunique():,}")

# Step 3: Find individuals age 25-70 in 1940 who have at least one under-18 observation
print("\n" + "="*70)
print("FINDING LINKED INDIVIDUALS")
print("="*70)
hik_1940_25to70 = set(df_1940_25to70['HIK'].unique())
hik_under18 = set(df_under18['HIK'].unique())

# Find intersection: people age 25-70 in 1940 who have at least one under-18 observation
linked_hiks = hik_1940_25to70.intersection(hik_under18)

n_linked = len(linked_hiks)
n_total_1940 = len(hik_1940_25to70)
pct_linked = (n_linked / n_total_1940) * 100 if n_total_1940 > 0 else 0

print(f"Individuals age 25-70 in 1940: {n_total_1940:,}")
print(f"  With at least one pre-18 obs: {n_linked:,} ({pct_linked:.2f}%)")
print(f"  Without pre-18 obs: {n_total_1940 - n_linked:,} ({100-pct_linked:.2f}%)")

# Step 4: Filter dataset to keep only linked individuals (all their observations)
print("\n" + "="*70)
print("FILTERING DATASET")
print("="*70)
print(f"Keeping only individuals who can be linked to pre-18 observations...")

n_before = len(df)
df_linked = df[df['HIK'].isin(linked_hiks)].copy()
n_after = len(df_linked)

print(f"Observations before filtering: {n_before:,}")
print(f"Observations after filtering:  {n_after:,}")
print(f"Observations dropped:          {n_before - n_after:,} ({(n_before - n_after)/n_before*100:.2f}%)")
print(f"Unique individuals in filtered dataset: {df_linked['HIK'].nunique():,}")

# Step 5: Summary statistics
print("\n" + "="*70)
print("FILTERED DATASET SUMMARY")
print("="*70)

# Count observations by census year
print("\nObservations by census year:")
year_counts = df_linked['YEAR'].value_counts().sort_index()
for year, count in year_counts.items():
    pct = (count / len(df_linked)) * 100
    print(f"  {year}: {count:,} ({pct:.1f}%)")

# Count pre-18 vs post-18 observations
pre18_count = (df_linked['AGE'] < 18).sum()
post18_count = (df_linked['AGE'] >= 18).sum()
print(f"\nObservations by age group:")
print(f"  Age < 18: {pre18_count:,} ({pre18_count/len(df_linked)*100:.1f}%)")
print(f"  Age >= 18: {post18_count:,} ({post18_count/len(df_linked)*100:.1f}%)")

# Step 6: Merge county treatment status
print("\n" + "="*70)
print("MERGING COUNTY TREATMENT STATUS")
print("="*70)

# Load county treatment status data, counties are treated if they gain exactly one college.
print(f"Loading treatment data from: {treatment_path}")
df_treatment = pd.read_csv(treatment_path)
print(f"Loaded {len(df_treatment):,} county records")
print(f"Treatment data columns: {list(df_treatment.columns)}")

# Check for merge keys in census data
print("\nChecking merge keys in census data...")
if 'stateicp' not in df_linked.columns:
    print("WARNING: stateicp not found in census data")
else:
    print(f"  Found stateicp in census data")
if 'COUNTYICP' not in df_linked.columns:
    print("WARNING: COUNTYICP not found in census data")
else:
    print(f"  Found COUNTYICP in census data")

# Count observations before merge
n_before_merge = len(df_linked)

# Perform many-to-1 merge (many census observations to 1 county)
# Census data uses stateicp/countyicp, treatment data uses ICPSRST/ICPSRCTY
# indicator=True allows us to see merge statistics
df_merged = df_linked.merge(
    df_treatment,
    left_on=['stateicp', 'COUNTYICP'],
    right_on=['ICPSRST', 'ICPSRCTY'],
    how='left',
    indicator=True,
    validate='many_to_one'
)

# Report merge statistics
print("\nMerge statistics:")
merge_stats = df_merged['_merge'].value_counts()
print(merge_stats)

if 'left_only' in merge_stats.index:
    n_unmatched = merge_stats['left_only']
    pct_unmatched = (n_unmatched / n_before_merge) * 100
    print(f"\nCensus observations without county match: {n_unmatched:,} ({pct_unmatched:.2f}%)")
    print("These observations will be kept in the dataset (no census data dropped)")

if 'both' in merge_stats.index:
    n_matched = merge_stats['both']
    pct_matched = (n_matched / n_before_merge) * 100
    print(f"Census observations with county match: {n_matched:,} ({pct_matched:.2f}%)")

# Drop the merge indicator column
df_merged = df_merged.drop(columns=['_merge'])

# Verify no census observations were dropped
n_after_merge = len(df_merged)
assert n_after_merge == n_before_merge, f"Census observations were dropped! Before: {n_before_merge}, After: {n_after_merge}"
print(f"\nVerified: No census observations dropped (still {n_after_merge:,} observations)")

# Update the dataframe to use merged version
df_linked = df_merged

# Step 7: Save filtered and merged dataset
print("\n" + "="*70)
print("SAVING FILTERED AND MERGED DATASET")
print("="*70)
print(f"Output file: {output_path}")
df_linked.to_csv(output_path, index=False)
print(f"Saved {len(df_linked):,} observations to linked-only file")

print("\n" + "="*70)
print("Filtering and merging complete!")
print("="*70)
