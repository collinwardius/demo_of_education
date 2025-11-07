# Census Linking Analysis: Pre-18 Observations

## Overview

This repository contains a data processing pipeline for linking individuals observed in the 1940 U.S. census back to their earlier census observations when they were under age 18. The primary goal is to identify where people were living before they turned 18, which is crucial for understanding the demographic and geographic factors that influenced their educational and economic outcomes.

**Important**: This code is designed to be run on a supercomputer with large census datasets. All code has been optimized for efficient memory management and processing of large files.

## Table of Contents

- [Project Purpose](#project-purpose)
- [Pipeline Overview](#pipeline-overview)
- [Directory Structure](#directory-structure)
- [Data Requirements](#data-requirements)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Pipeline Components](#pipeline-components)
- [Output Files](#output-files)
- [Key Findings](#key-findings)
- [Performance Considerations](#performance-considerations)
- [Troubleshooting](#troubleshooting)

## Project Purpose

The primary objectives of this analysis are to:

1. **Link individuals across censuses**: Identify people age 25+ in 1940 who can be successfully linked to at least one census observation before age 18
2. **Assess linking quality**: Understand the distribution of pre-18 observations per person
3. **Evaluate selection bias**: Compare characteristics between individuals who were successfully linked versus those who were not
4. **Standardize geographic units**: Use county crosswalks to standardize counties to 1900 boundaries across all years
5. **Merge treatment data**: Incorporate county-level treatment status (college openings) for analysis

## Pipeline Overview

The complete pipeline consists of three main stages:

```
Raw Census Data
    ↓
[1] clean_census_data.py
    ↓
Cleaned Census Data (temp)
    ↓
[2] filter_merge_cleaned_data.py
    ↓
Filtered & Merged Census Data (final)
    ↓
[3] analyze_pre18_linking.py
    ↓
LaTeX Comparison Table
```

### Stage 1: Data Cleaning
- Filters to individuals aged 25-70 in 1940
- Removes records with missing education (EDUC=99)
- Standardizes counties across census years using crosswalks
- Creates indicator variables for education, race, labor force, etc.
- Keeps only pre-18 observations (AGE < 18) for non-1940 years

### Stage 2: Filtering & Merging
- Identifies individuals who can be linked to pre-18 observations
- Filters dataset to keep only linked individuals
- Merges county-level treatment status data

### Stage 3: Analysis
- Compares characteristics of linked vs. unlinked individuals
- Generates LaTeX tables for publication

## Directory Structure

```
link_in_census/
├── README.md                              # This file
├── CLAUDE.md                              # Project instructions for Claude Code
├── CLEANED_DATA_SUMMARY.md                # Data dictionary and cleaning summary
├── clean_census_data.py                   # Stage 1: Data cleaning script
├── filter_merge_cleaned_data.py           # Stage 2: Filtering and merging script
├── analyze_pre18_linking.py               # Stage 3: Analysis script
├── run_census_pipeline.sh                 # Complete pipeline (runs all 3 stages)
├── run_census_pipeline_partial.sh         # Partial pipeline (skips stage 1)
└── .claude/                               # Claude Code settings
    └── settings.local.json
```

## Data Requirements

### Input Data

**Raw Census Data**:
- Path: `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/`
- Format: CSV file with linked census records across years (1900, 1910, 1920, 1930, 1940)
- Key identifier: `HIK` (Historical Individual Key) - links same person across censuses

**Required Columns**:
- `HIK`: Individual identifier across censuses
- `YEAR`: Census year
- `AGE`: Age at census
- `BIRTHYR`: Birth year
- `EDUC`: Education level (0-11, 99=missing)
- `STATEFIP`: State FIPS code
- `COUNTYICP`: County ICPSR code
- Demographic variables: `SEX`, `RACE`, `MARST`, `HISPAN`, `NATIVITY`
- Labor market variables: `LABFORCE`, `CLASSWKR`, `SCHOOL`

### County Crosswalk Files

**Directory**: `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/county_shape_files/`

**Required files**:
- `county_crosswalk_1900_to_1940.csv`
- `county_crosswalk_1910_to_1940.csv`
- `county_crosswalk_1920_to_1940.csv`
- `county_crosswalk_1930_to_1940.csv`

**Crosswalk structure**:
- `icpsrst_[year]`: ICPSR state code for original year
- `icpsrcty_[year]`: ICPSR county code for original year
- `icpsrst_1940`: Standardized state code (1940 boundaries)
- `icpsrcty_1940`: Standardized county code (1940 boundaries)

### County Treatment Data

**Path**: `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/county_treatment_status.csv`

**Required columns**:
- `ICPSRST`: ICPSR state code
- `ICPSRCTY`: ICPSR county code
- Treatment indicator variable(s)

## Installation & Setup

### Prerequisites

- Python 3.7 or higher
- pandas library

### Installation

```bash
# Install required Python packages
pip install pandas

# Make shell scripts executable
chmod +x run_census_pipeline.sh
chmod +x run_census_pipeline_partial.sh
```

## Usage

### Option 1: Complete Pipeline (Recommended)

Run the complete pipeline from raw data to final analysis:

```bash
./run_census_pipeline.sh \
    <input_raw_data> \
    <output_linked_data> \
    [crosswalk_dir] \
    [treatment_path] \
    [analysis_output]
```

**Example**:
```bash
./run_census_pipeline.sh \
    "/path/to/raw_census.csv" \
    "/path/to/output/linked_census.csv" \
    "/path/to/county_shape_files" \
    "/path/to/county_treatment_status.csv" \
    "/path/to/output/tables/linked_comparison.tex"
```

### Option 2: Partial Pipeline

If you already have cleaned data and want to skip the cleaning stage:

```bash
./run_census_pipeline_partial.sh \
    <input_cleaned_data> \
    <output_linked_data> \
    [treatment_path] \
    [analysis_output]
```

### Option 3: Individual Scripts

Run scripts individually for more control:

**Step 1: Clean data**
```bash
python3 clean_census_data.py \
    <input_path> \
    <output_path> \
    [crosswalk_dir]
```

**Step 2: Filter and merge**
```bash
python3 filter_merge_cleaned_data.py \
    <input_path> \
    <output_path> \
    [treatment_path]
```

**Step 3: Analyze linking**
```bash
python3 analyze_pre18_linking.py \
    <input_path> \
    [output_path]
```

## Pipeline Components

### 1. clean_census_data.py

**Purpose**: Cleans raw census data and standardizes counties across years

**Operations**:
- **Two-pass processing**: First pass identifies valid individuals, second pass loads only relevant observations
- **Age filtering**: Keeps individuals aged 25-70 in 1940; for other years, keeps only AGE < 18
- **Education filtering**: Removes individuals with EDUC=99 in 1940
- **County standardization**: Merges with crosswalks to standardize all counties to 1940 boundaries
- **Variable recoding**: Creates indicator variables and recodes categorical variables
  - SEX: 1→0 (Male), 2→1 (Female)
  - MARST: 1,2→1 (Married), others→0 (Not married)
  - LABFORCE: 2→1 (In labor force), 1→0 (Not in labor force)
  - SCHOOL: 2→1 (In school), 1→0 (Not in school)
  - HISPAN: nonzero→1 (Hispanic), 0→0 (Not Hispanic)
- **New variables created**:
  - `college`: 1 if EDUC in [7-11], 0 otherwise
  - `ba`: 1 if EDUC in [10-11], 0 otherwise
  - `self_employed`: 1 if CLASSWKR=1, 0 otherwise
  - `foreign_born`: 1 if NATIVITY=5, 0 otherwise
  - `race_white`, `race_black`, `race_amind`, `race_chinese`, `race_japanese`, `race_other`
  - `stateicp`: ICPSR state code (created from STATEFIP)

**Memory optimization**:
- Chunk processing to handle large files
- Drops unnecessary columns early
- Two-pass approach minimizes memory usage

**Output**: Cleaned census data with standardized counties and indicator variables

### 2. filter_merge_cleaned_data.py

**Purpose**: Filters to linked individuals and merges treatment data

**Operations**:
- Identifies individuals age 25-70 in 1940
- Finds individuals with at least one pre-18 observation
- Keeps only linked individuals (all their observations across all years)
- Performs left merge with county treatment data
- Validates merge quality and reports statistics

**Key metrics reported**:
- Linking rate (% of 1940 sample with pre-18 observations)
- Distribution of observations by census year
- Distribution of pre-18 vs. post-18 observations
- Merge statistics (matched vs. unmatched counties)

**Output**: Filtered dataset containing only linked individuals with merged treatment data

### 3. analyze_pre18_linking.py

**Purpose**: Generates comparison table of linked vs. unlinked individuals

**Operations**:
- Compares 1940 characteristics between linked and unlinked groups
- Calculates means and standard errors
- Generates formatted LaTeX table

**Variables compared**:
- SEX (Female %)
- AGE
- college (College %)
- MARST (Married %)
- race_white (White %)

**Output**: LaTeX table ready for publication

## Output Files

### Figures Directory
All generated figures are saved to:
```
/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures/
```

### Tables Directory
All LaTeX tables and statistical tables are saved to:
```
/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables/
```

### Default Outputs

1. **Cleaned data** (temporary): `*_temp_cleaned.csv`
   - Intermediate file, deleted after pipeline completion

2. **Final linked data**: User-specified output path
   - Contains only linked individuals with merged treatment data
   - Ready for regression analysis

3. **Comparison table**: `linked_vs_unlinked_comparison.tex`
   - LaTeX table comparing linked vs. unlinked individuals
   - Includes means, sample sizes, and percentages

## Key Findings

Based on analysis of the Georgia debugging sample:

### Linking Statistics
- **Overall linking rate**: ~37-38% of individuals age 25+ in 1940 can be linked to at least one pre-18 observation
- **Multiple observations**: ~20% of age 25+ sample has 2+ pre-18 observations
- **Best census coverage**: 1910 and 1920 provide the most pre-18 observations

### Selection Patterns
- **Age bias**: Younger individuals in 1940 are more likely to be linked
  - Linked group mean age: ~37 years
  - Unlinked group mean age: ~50 years
- **Reason**: Older cohorts would have been children in earlier census years (1900-1910) when record-keeping was less complete

### Data Quality
- **Sample composition after cleaning**:
  - 55.5% male, 44.5% female
  - 74.3% White, 25.7% Black
  - 64.5% married
  - 2.5% with some college
  - 1.0% with BA degree

### County Standardization
- Counties successfully standardized to 1940 boundaries
- Typical crosswalk match rates: 95%+ for most years
- Unmatched observations dropped during cleaning stage

## Performance Considerations

### For Supercomputer Implementation

**Memory Management**:
- Chunk processing with configurable chunk size (default: 1,000,000 rows)
- Early column dropping to reduce memory footprint
- Two-pass processing to minimize memory usage
- Vectorized operations throughout for efficiency

**Optimization Tips**:
1. Adjust `chunk_size` in clean_census_data.py based on available memory
2. Consider parallelization for independent processing of census years
3. Use SSD storage for faster I/O operations
4. Monitor memory usage with large datasets (10M+ records)

**Expected Processing Times** (approximate):
- Cleaning stage: 5-10 minutes per 5M records
- Filtering stage: 2-5 minutes per 5M records
- Analysis stage: 1-2 minutes per 5M records

### Disk Space Requirements
- Raw data: Variable (typically 500MB-5GB for full sample)
- Cleaned data (temporary): ~60% of raw data size
- Final linked data: ~40% of cleaned data size
- Total temporary space needed: 2x raw data size

## Troubleshooting

### Common Issues

**1. Memory errors during cleaning**
- Solution: Reduce `chunk_size` in clean_census_data.py (line 62)
- Alternative: Process data in smaller batches

**2. Crosswalk merge failures**
- Check that crosswalk files exist in specified directory
- Verify column names match expected format
- Review unmatched STATEFIP values in cleaning output

**3. Treatment data merge issues**
- Verify treatment file has `ICPSRST` and `ICPSRCTY` columns
- Check that county codes are in ICPSR format (not FIPS)
- Review merge statistics output for details

**4. Missing output directories**
- Create output directories before running pipeline:
  ```bash
  mkdir -p "/path/to/output/figures"
  mkdir -p "/path/to/output/tables"
  ```

**5. Permission denied errors**
- Make shell scripts executable: `chmod +x run_census_pipeline.sh`
- Check write permissions for output directories

### Validation Checks

**After cleaning**:
- Verify no 1940 observations outside age range 25-70
- Verify no EDUC=99 in 1940
- Check that all counties have been standardized
- Review dropped observation counts

**After filtering**:
- Confirm linking rate is reasonable (~30-40%)
- Check that pre-18 observations exist for all included individuals
- Verify treatment merge statistics

**After analysis**:
- Review LaTeX table for reasonable values
- Check that sample sizes match expectations
- Verify standard errors are calculated

## Additional Documentation

- **CLAUDE.md**: Instructions for Claude Code (project context)
- **CLEANED_DATA_SUMMARY.md**: Detailed data dictionary and variable descriptions
- See individual script docstrings for function-level documentation

## Future Extensions

Potential enhancements to this pipeline:

1. **Linking quality assessment**: Calculate false positive/negative rates
2. **Geographic mobility analysis**: Track movement between pre-18 and 1940 locations
3. **Data quality metrics**: Analyze relationship between number of observations and data quality
4. **Stratified analysis**: Examine linking rates by birth cohort, region, race, etc.
5. **Selection bias corrections**: Develop weighting schemes to address non-random linking
6. **Parallel processing**: Implement multi-core processing for large datasets
7. **Interactive visualizations**: Create dashboards showing linking patterns

## Citation

If you use this code in your research, please cite:

```
[Your citation information here]
```

## Contact

For questions or issues, contact:
- [Your contact information]

## License

[Your license information here]

---

**Last Updated**: November 2025
**Version**: 1.0
