"""
Filter cleaned census data to keep only individuals who can be linked to pre-18 observations.

This script:
1. Loads the cleaned census data
2. Identifies individuals age 25-70 in 1940
3. Finds which individuals have at least one observation when AGE < 18
4. Keeps only those individuals (all their observations across all census years)
5. Saves the filtered dataset

Input: cleaned census data
Output: linked-only census data
"""

import pandas as pd

# Input and output paths
input_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/born_georgia_linked_census_for_debugging_cleaned.csv"
output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/born_georgia_linked_census_for_debugging_cleaned_linked.csv"

print("="*70)
print("FILTER FOR LINKED INDIVIDUALS ONLY")
print("="*70)

# Load the cleaned data
print("\nLoading cleaned census data...")
print(f"Input file: {input_path}")
df = pd.read_csv(input_path)
print(f"Loaded {len(df):,} total observations")
print(f"Unique individuals: {df['HIK'].nunique():,}")

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

# Step 6: Save filtered dataset
print("\n" + "="*70)
print("SAVING FILTERED DATASET")
print("="*70)
print(f"Output file: {output_path}")
df_linked.to_csv(output_path, index=False)
print(f"Saved {len(df_linked):,} observations to linked-only file")

print("\n" + "="*70)
print("Filtering complete!")
print("="*70)
