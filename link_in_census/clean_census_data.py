"""
Clean census data for linking analysis.

This script performs data cleaning steps on the raw census data:
1. Drops records with missing age (AGE=999)
2. Saves cleaned data for subsequent analysis

Input: Raw census data
Output: Cleaned census data ready for linking analysis
"""

import pandas as pd
import os

# Input and output paths
input_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/born_georgia_linked_census_for_debugging.csv"
output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/born_georgia_linked_census_for_debugging_cleaned.csv"

print("="*70)
print("CENSUS DATA CLEANING")
print("="*70)

# Load the data
print("\nLoading census data...")
print(f"Input file: {input_path}")
df = pd.read_csv(input_path)
print(f"Loaded {len(df):,} total observations")

# Create ICPSR state code from FIPS state code
print("\nCreating ICPSR state code (stateicp) from STATEFIP...")
fips_icp = {
    1: 41, 2: 81, 4: 61, 5: 42, 6: 71, 8: 62, 9: 1, 10: 11,
    11: 55, 12: 43, 13: 44, 15: 82, 16: 63, 17: 21, 18: 22, 19: 31,
    20: 32, 21: 51, 22: 45, 23: 2, 24: 52, 25: 3, 26: 23, 27: 33,
    28: 46, 29: 34, 30: 64, 31: 35, 32: 65, 33: 4, 34: 12, 35: 66,
    36: 13, 37: 47, 38: 36, 39: 24, 40: 53, 41: 72, 42: 14, 44: 5,
    45: 48, 46: 37, 47: 54, 48: 49, 49: 67, 50: 6, 51: 40, 53: 73,
    54: 56, 55: 25, 56: 68
}

df['stateicp'] = df['STATEFIP'].map(fips_icp)

# Check if any states didn't match
unmapped = df[df['stateicp'].isna()]
if len(unmapped) > 0:
    print(f"   Warning: {len(unmapped):,} observations have STATEFIP values not in mapping")
    print(f"   Unique unmapped STATEFIP values: {sorted(unmapped['STATEFIP'].unique())}")
else:
    print(f"   Successfully mapped all {len(df):,} observations")

# Merge with county crosswalks to standardize counties across time
print("\n" + "="*70)
print("MERGING WITH COUNTY CROSSWALKS")
print("="*70)
print("Standardizing counties to 1900 boundaries across all years")

crosswalk_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files"

# Track observations before merges
n_before_crosswalk = len(df)

# Process each year separately
# We actually don't need the 1940 crosswalk since it will not be determining the treatment assignment
for year in [1900, 1910, 1920, 1930]:
    # Filter data for this year
    df_year = df[df['YEAR'] == year].copy()
    df_other = df[df['YEAR'] != year].copy()

    n_before_merge = len(df_year)

    if n_before_merge == 0:
        print(f"\n{year}: No observations to merge")
        continue

    # Load crosswalk file
    crosswalk_file = f"{crosswalk_dir}/county_crosswalk_{year}_to_1940.csv"
    crosswalk = pd.read_csv(crosswalk_file)

    # Rename columns for merging
    # Native data has: stateicp, COUNTYICP
    # Crosswalk has: icpsrst_{year}, icpsrcty_{year}, icpsrst_1940, icpsrcty_1940
    crosswalk = crosswalk.rename(columns={
        f'icpsrst_{year}': 'stateicp',
        f'icpsrcty_{year}': 'COUNTYICP',
        f'icpsrst_1940': 'stateicp_1940',
        f'icpsrcty_1940': 'COUNTYICP_1940'
    })

    # Keep only necessary columns from crosswalk
    crosswalk = crosswalk[['stateicp', 'COUNTYICP', 'stateicp_1940', 'COUNTYICP_1940']]

    # Merge with census data (inner merge to keep only matched observations)
    df_year_merged = df_year.merge(
        crosswalk,
        on=['stateicp', 'COUNTYICP'],
        how='inner',
        indicator=True
    )

    n_after_merge = len(df_year_merged)
    n_dropped = n_before_merge - n_after_merge

    print(f"\n{year}: Merged {n_before_merge:,} observations")
    print(f"   Matched: {n_after_merge:,} observations")
    print(f"   Dropped: {n_dropped:,} observations ({n_dropped/n_before_merge*100:.2f}%)")

    # Replace original county codes with 1940 standardized codes
    df_year_merged['stateicp'] = df_year_merged['stateicp_1940']
    df_year_merged['COUNTYICP'] = df_year_merged['COUNTYICP_1940']

    # Drop temporary columns
    df_year_merged = df_year_merged.drop(columns=['stateicp_1940', 'COUNTYICP_1940', '_merge'])

    # Combine back with other years
    df = pd.concat([df_other, df_year_merged], ignore_index=True)

# 1940 remains unchanged
df_1 = df[df['YEAR'] == 1940]
print(f"\n1940: No crosswalk needed (baseline year) - {len(df_1):,} observations")

n_after_crosswalk = len(df)
n_total_dropped = n_before_crosswalk - n_after_crosswalk

print(f"\nTotal crosswalk merge summary:")
print(f"   Before merges: {n_before_crosswalk:,} observations")
print(f"   After merges:  {n_after_crosswalk:,} observations")
print(f"   Total dropped: {n_total_dropped:,} observations ({n_total_dropped/n_before_crosswalk*100:.2f}%)")

# Data cleaning steps
print("\n" + "="*70)
print("CLEANING STEPS")
print("="*70)

n_before = len(df)

# Step 1: Drop people with age < 25 or > 70 in 1940
print("\n1. Dropping people with age < 25 or > 70 in 1940:")
if 'AGE' in df.columns and 'HIK' in df.columns and 'YEAR' in df.columns:
    n_before_age = len(df)

    # Find people in 1940 outside age range 25-70
    df_1940 = df[df['YEAR'] == 1940]
    n_outside_range = ((df_1940['AGE'] < 25) | (df_1940['AGE'] > 70)).sum()
    print(f"   Found {n_outside_range:,} observations in 1940 with AGE<25 or AGE>70")

    if n_outside_range > 0:
        # Get HIKs to drop (people with age<25 or age>70 in 1940)
        hiks_to_drop = df_1940[(df_1940['AGE'] < 25) | (df_1940['AGE'] > 70)]['HIK'].unique()
        print(f"   Dropping {len(hiks_to_drop):,} unique individuals (all their observations across all years)")

        # Drop all observations for these individuals
        df = df[~df['HIK'].isin(hiks_to_drop)].copy()
        n_after_age = len(df)
        print(f"   Dropped {n_before_age - n_after_age:,} total observations")
    else:
        print(f"   No records to drop")
else:
    if 'AGE' not in df.columns:
        print(f"   Warning: AGE column not found in data")
    if 'HIK' not in df.columns:
        print(f"   Warning: HIK column not found in data")
    if 'YEAR' not in df.columns:
        print(f"   Warning: YEAR column not found in data")

n_after = len(df)

# Step 2: Drop people in 1940 with missing education (educ=99)
print("\n2. Dropping people observed in 1940 with missing education (EDUC=99):")
if 'EDUC' in df.columns and 'YEAR' in df.columns:
    n_before_educ = len(df)
    n_missing_educ_1940 = ((df['YEAR'] == 1940) & (df['EDUC'] == 99)).sum()
    print(f"   Found {n_missing_educ_1940:,} observations in 1940 with EDUC=99")

    if n_missing_educ_1940 > 0:
        # Get HIKs to drop (people with educ=99 in 1940)
        hiks_to_drop = df[(df['YEAR'] == 1940) & (df['EDUC'] == 99)]['HIK'].unique()
        print(f"   Dropping {len(hiks_to_drop):,} unique individuals (all their observations across all years)")

        # Drop all observations for these individuals
        df = df[~df['HIK'].isin(hiks_to_drop)].copy()
        n_after_educ = len(df)
        print(f"   Dropped {n_before_educ - n_after_educ:,} total observations")
    else:
        print(f"   No records to drop")
else:
    if 'EDUC' not in df.columns:
        print(f"   Warning: EDUC column not found in data")
    if 'YEAR' not in df.columns:
        print(f"   Warning: YEAR column not found in data")

# Step 3: Create education indicator variables (college and ba)
print("\n3. Creating education indicator variables:")
if 'EDUC' in df.columns:
    # Create college indicator: 1 if EDUC is 7-11, 0 otherwise
    df['college'] = df['EDUC'].isin([7, 8, 9, 10, 11]).astype(int)

    # Create ba indicator: 1 if EDUC is 10 or 11, 0 otherwise
    df['ba'] = df['EDUC'].isin([10, 11]).astype(int)

    college_count = df['college'].sum()
    ba_count = df['ba'].sum()

    print(f"   Created college variable (EDUC 7-11): {college_count:,} records ({college_count/len(df)*100:.2f}%)")
    print(f"   Created ba variable (EDUC 10-11): {ba_count:,} records ({ba_count/len(df)*100:.2f}%)")
else:
    print(f"   Warning: EDUC column not found in data")

# Step 4: Recode labor force participation (LABFORCE: 2->1, 1->0, others->missing)
print("\n4. Recoding labor force participation variable (LABFORCE):")
print(f"   New coding: 2 -> 1 (in labor force), 1 -> 0 (not in labor force), others -> missing")
if 'LABFORCE' in df.columns:
    original_counts = df['LABFORCE'].value_counts().sort_index()
    print(f"   Before recoding:")
    for val, count in original_counts.items():
        print(f"      LABFORCE={val}: {count:,} records")

    # Recode using vectorized operation for efficiency
    # 2 -> 1, 1 -> 0, others -> NaN
    df['LABFORCE'] = df['LABFORCE'].replace({2: 1, 1: 0})
    df.loc[~df['LABFORCE'].isin([0, 1]), 'LABFORCE'] = pd.NA

    recoded_counts = df['LABFORCE'].value_counts(dropna=False).sort_index()
    print(f"   After recoding:")
    for val, count in recoded_counts.items():
        if pd.isna(val):
            print(f"      LABFORCE=Missing: {count:,} records")
        else:
            status = "In labor force" if val == 1 else "Not in labor force"
            print(f"      LABFORCE={int(val)} ({status}): {count:,} records")
else:
    print(f"   Warning: LABFORCE column not found in data")

# Step 5: Recode school attendance (SCHOOL: 2->1, 1->0, 8->0)
print("\n5. Recoding school attendance variable (SCHOOL):")
print(f"   New coding: 2 -> 1 (in school), 1 -> 0 (not in school), 8 -> 0 (not in school)")
if 'SCHOOL' in df.columns:
    original_counts = df['SCHOOL'].value_counts().sort_index()
    print(f"   Before recoding:")
    for val, count in original_counts.items():
        print(f"      SCHOOL={val}: {count:,} records")

    # Recode using vectorized operation for efficiency
    df['SCHOOL'] = df['SCHOOL'].replace({2: 1, 1: 0, 8:0})

    recoded_counts = df['SCHOOL'].value_counts().sort_index()
    print(f"   After recoding:")
    for val, count in recoded_counts.items():
        status = "In school" if val == 1 else "Not in school"
        print(f"      SCHOOL={val} ({status}): {count:,} records")
else:
    print(f"   Warning: SCHOOL column not found in data")

# Step 6: Create self_employed variable from CLASSWKR
print("\n6. Creating self_employed variable from CLASSWKR:")
print(f"   New coding: CLASSWKR=1 -> 1 (self employed), otherwise -> 0 (not self employed)")
if 'CLASSWKR' in df.columns:
    original_counts = df['CLASSWKR'].value_counts().sort_index()
    print(f"   Distribution of CLASSWKR variable:")
    for val, count in original_counts.items():
        print(f"      CLASSWKR={val}: {count:,} records")

    # Create self_employed variable using vectorized operation for efficiency
    df['self_employed'] = (df['CLASSWKR'] == 1).astype(int)

    self_emp_counts = df['self_employed'].value_counts().sort_index()
    print(f"   Created self_employed variable:")
    for val, count in self_emp_counts.items():
        status = "Self employed" if val == 1 else "Not self employed"
        print(f"      self_employed={val} ({status}): {count:,} records")
else:
    print(f"   Warning: CLASSWKR column not found in data")

# Step 7: Recode gender (SEX: 1=Male -> 0, 2=Female -> 1)
print("\n7. Recoding gender variable (SEX):")
print(f"   Original coding: 1=Male, 2=Female")
print(f"   New coding: 0=Male, 1=Female")
if 'SEX' in df.columns:
    original_counts = df['SEX'].value_counts().sort_index()
    print(f"   Before recoding:")
    for val, count in original_counts.items():
        print(f"      SEX={val}: {count:,} records")

    # Recode: 1->0 (Male), 2->1 (Female)
    df['SEX'] = df['SEX'].replace({1: 0, 2: 1})

    recoded_counts = df['SEX'].value_counts().sort_index()
    print(f"   After recoding:")
    for val, count in recoded_counts.items():
        gender = "Male" if val == 0 else "Female"
        print(f"      SEX={val} ({gender}): {count:,} records")
else:
    print(f"   Warning: SEX column not found in data")

# Step 8: Recode marital status (MARST: 1,2 -> 1 (married), others -> 0 (not married))
print("\n8. Recoding marital status variable (MARST):")
print(f"   New coding: 1 or 2 -> 1 (married), all others -> 0 (not married)")
if 'MARST' in df.columns:
    original_counts = df['MARST'].value_counts().sort_index()
    print(f"   Before recoding:")
    for val, count in original_counts.items():
        print(f"      MARST={val}: {count:,} records")

    # Recode: 1 or 2 -> 1 (married), others -> 0 (not married)
    # Using vectorized operation for efficiency on large datasets
    df['MARST'] = df['MARST'].isin([1, 2]).astype(int)

    recoded_counts = df['MARST'].value_counts().sort_index()
    print(f"   After recoding:")
    for val, count in recoded_counts.items():
        status = "Married" if val == 1 else "Not married"
        print(f"      MARST={val} ({status}): {count:,} records")
else:
    print(f"   Warning: MARST column not found in data")

# Step 9: Create foreign_born variable from NATIVITY (keep original NATIVITY)
print("\n9. Creating foreign_born variable from NATIVITY:")
print(f"   New coding: NATIVITY 1,2,3,4 -> 0 (native born), NATIVITY 5 -> 1 (foreign born)")
if 'NATIVITY' in df.columns:
    original_counts = df['NATIVITY'].value_counts().sort_index()
    print(f"   Distribution of NATIVITY variable:")
    for val, count in original_counts.items():
        print(f"      NATIVITY={val}: {count:,} records")

    # Create foreign_born variable using vectorized operation for efficiency
    # Keep original NATIVITY variable
    df['foreign_born'] = (df['NATIVITY'] == 5).astype(int)

    foreign_counts = df['foreign_born'].value_counts().sort_index()
    print(f"   Created foreign_born variable:")
    for val, count in foreign_counts.items():
        status = "Foreign born" if val == 1 else "Native born"
        print(f"      foreign_born={val} ({status}): {count:,} records")
else:
    print(f"   Warning: NATIVITY column not found in data")

# Step 10: Recode Hispanic origin (HISPAN: any nonzero -> 1, zero -> 0)
print("\n10. Recoding Hispanic origin variable (HISPAN):")
print(f"   New coding: 0 -> 0 (not Hispanic), any nonzero value -> 1 (Hispanic)")
if 'HISPAN' in df.columns:
    original_counts = df['HISPAN'].value_counts().sort_index()
    print(f"   Before recoding:")
    for val, count in list(original_counts.items())[:10]:  # Show first 10 values
        print(f"      HISPAN={val}: {count:,} records")
    if len(original_counts) > 10:
        print(f"      ... and {len(original_counts) - 10} more values")

    # Recode: any nonzero value -> 1, using vectorized operation for efficiency
    df['HISPAN'] = (df['HISPAN'] != 0).astype(int)

    recoded_counts = df['HISPAN'].value_counts().sort_index()
    print(f"   After recoding:")
    for val, count in recoded_counts.items():
        status = "Hispanic" if val == 1 else "Not Hispanic"
        print(f"      HISPAN={val} ({status}): {count:,} records")
else:
    print(f"   Warning: HISPAN column not found in data")

# Step 11: Create race indicator variables
print("\n11. Creating race indicator variables:")
print(f"   Original RACE codes: 1=White, 2=Black, 3=American Indian, 4=Chinese, 5=Japanese, Other=Other")
if 'RACE' in df.columns:
    original_counts = df['RACE'].value_counts().sort_index()
    print(f"   Distribution of RACE variable:")
    for val, count in original_counts.items():
        print(f"      RACE={val}: {count:,} records")

    # Create indicator variables using vectorized operations for efficiency
    df['race_white'] = (df['RACE'] == 1).astype(int)
    df['race_black'] = (df['RACE'] == 2).astype(int)
    df['race_amind'] = (df['RACE'] == 3).astype(int)
    df['race_chinese'] = (df['RACE'] == 4).astype(int)
    df['race_japanese'] = (df['RACE'] == 5).astype(int)
    df['race_other'] = (~df['RACE'].isin([1, 2, 3, 4, 5])).astype(int)

    print(f"   Created indicator variables:")
    print(f"      race_white: {df['race_white'].sum():,} records")
    print(f"      race_black: {df['race_black'].sum():,} records")
    print(f"      race_amind: {df['race_amind'].sum():,} records")
    print(f"      race_chinese: {df['race_chinese'].sum():,} records")
    print(f"      race_japanese: {df['race_japanese'].sum():,} records")
    print(f"      race_other: {df['race_other'].sum():,} records")
else:
    print(f"   Warning: RACE column not found in data")

# Summary
print("\n" + "="*70)
print("CLEANING SUMMARY")
print("="*70)
print(f"Records before cleaning: {n_before:,}")
print(f"Records after cleaning:  {n_after:,}")
print(f"Records dropped:         {n_before - n_after:,} ({((n_before - n_after) / n_before * 100):.2f}%)")

# Save cleaned data
print("\n" + "="*70)
print("SAVING CLEANED DATA")
print("="*70)
print(f"Output file: {output_path}")
df.to_csv(output_path, index=False)
print(f"Saved {len(df):,} observations to cleaned file")

print("\n" + "="*70)
print("Cleaning complete!")
print("="*70)
