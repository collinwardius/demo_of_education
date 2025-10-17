# Census Linking Analysis: Pre-18 Observations

## Overview

This folder contains code to link individuals observed in the 1940 census back to observations from earlier censuses when they were under age 18. The goal is to determine where people were living before they turned 18, which is crucial for understanding the demographic factors that influenced their educational and economic outcomes.

## Purpose

The primary objective is to:
1. Identify how many people age 25+ in 1940 can be successfully linked to at least one census observation before age 18
2. Understand the distribution of pre-18 observations per person
3. Compare characteristics between individuals who were successfully linked versus those who were not
4. Assess the quality and coverage of the linking process

## Files

### `analyze_pre18_linking.py`

Main analysis script that performs the following:

**Primary Analysis:**
- Filters to individuals age 25+ in 1940 (ensures they had sufficient time to be observed in earlier censuses)
- Identifies which individuals have at least one observation when they were under age 18
- Calculates linking rates and distributions

**Key Outputs:**
1. **Linking Statistics**
   - Total number and percentage of people age 25+ in 1940 who can be linked to pre-18 observations
   - Distribution of the number of pre-18 observations per person
   - Summary statistics (mean, median, max observations per person)

2. **Age Distribution Analysis**
   - Compares mean age in 1940 between linked and unlinked individuals
   - Shows which ages are better represented in the linked sample

3. **Census Year Coverage**
   - Shows which census years (1900, 1910, 1920, 1930) provide pre-18 observations
   - Identifies unique individuals and total observations from each census

4. **Comparison Table (LaTeX output)**
   - Compares means of all 1940 observables between linked and unlinked individuals
   - Includes standard errors for all estimates
   - Saved to: `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables/linked_vs_unlinked_comparison.tex`

**Example Results:**
The script provides detailed examples of individuals with multiple pre-18 observations, showing their full census history including:
- Birth year
- Age in each census
- State and county of residence
- Which observations are pre-18

## Data Requirements

**Input Data:**
- Path: `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/born_georgia_linked_census_for_debugging.csv`
- Required columns: `HIK` (individual identifier), `YEAR`, `AGE`, `BIRTHYR`, plus various demographic and economic variables

**Key Variables:**
- `HIK`: Histid unique identifier linking the same person across censuses
- `YEAR`: Census year (1900, 1910, 1920, 1930, 1940)
- `AGE`: Age at time of census
- `BIRTHYR`: Birth year

## Output

### Tables
LaTeX table saved to:
```
/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables/linked_vs_unlinked_comparison.tex
```

This table includes:
- Mean values for linked and unlinked groups
- Standard errors
- Difference between groups
- Sample sizes

## Running the Analysis

To run the analysis:
```bash
cd /Users/cjwardius/Documents/GitHub/demo_of_education/link_in_census
python analyze_pre18_linking.py
```

## Key Findings

The analysis reveals:
- **Linking Rate**: Approximately 37-38% of individuals age 25+ in 1940 can be linked to at least one pre-18 observation
- **Age Selection**: Younger individuals in 1940 are more likely to be linked (mean age ~37 for linked vs ~50 for unlinked)
- **Multiple Observations**: About 20% of the age 25+ sample has 2+ pre-18 observations
- **Census Coverage**: 1910 and 1920 provide the most pre-18 observations for the age 25+ sample

## Supercomputer Implementation

**Important Note**: Code in this folder is designed to be run on a supercomputer with the full census sample. When adapting for large-scale runs:
- Ensure efficient memory management for large datasets
- Consider parallelization strategies for the linking process
- Optimize I/O operations for reading/writing large files
- Test thoroughly on the debugging sample before running on full data

## Future Extensions

Potential extensions of this analysis:
1. Linking quality assessment (false positive/negative rates)
2. Geographic mobility patterns between pre-18 and 1940 observations
3. Relationship between number of pre-18 observations and data quality
4. Stratified analysis by birth cohort or region
5. Analysis of selection bias in the linking process
