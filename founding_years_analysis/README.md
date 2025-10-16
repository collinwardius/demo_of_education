# Founding Years Analysis

This directory contains scripts for analyzing the founding years and geographic distribution of colleges in the United States based on historical college bluebook data.

## Files

### `clean_bluebook.py`
Cleans the raw college bluebook data by:
- Dropping observations with missing city information
- Expanding abbreviated city names to their full forms (e.g., "Mt. Vernon" → "Mount Vernon", "St. Louis" → "Saint Louis", "Colorado Spg." → "Colorado Springs")
- Outputs cleaned data to `combined_college_blue_book_data_cleaned.csv`

**Usage:**
```bash
python clean_bluebook.py
```

**Input:** `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/combined_college_blue_book_data.csv`

**Output:** `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/combined_college_blue_book_data_cleaned.csv`

### `geocode_colleges.py`
Geocodes college locations by converting city and state information to latitude/longitude coordinates using the Nominatim geocoder.

**Features:**
- Incremental geocoding: By default, only geocodes new locations not found in existing results
- Overwrite mode: Option to re-geocode all locations from scratch
- Handles abbreviations and city name variations
- Saves both full dataset with coordinates and unique location lookup table

**Usage:**
```bash
# Default mode: only geocode new locations
python geocode_colleges.py

# Overwrite mode: re-geocode all locations
python geocode_colleges.py --overwrite
```

**Input:** `combined_college_blue_book_data_cleaned.csv`

**Output:**
- `colleges_with_coordinates.csv` - Full dataset with geocoded coordinates
- `unique_locations_geocoded.csv` - Unique city-state pairs with coordinates

### `founding_years_analysis.py`
Generates comprehensive visualizations and statistical analyses of college founding years, regional distributions, and enrollment capacity. Uses county-level geographic data from 1940 census boundaries.

**Main Functions:**

**Founding Year Distributions:**
- `create_founding_years_cdf()` - Cumulative distribution of college founding years
- `create_zoomed_founding_cdf()` - Zoomed CDF focusing on 1800+ period
- `create_regional_founding_cdf()` - Regional comparison of founding year CDFs
- `create_zoomed_regional_founding_cdf()` - Zoomed regional CDF (1800-1944)
- `create_control_type_founding_cdf()` - CDF by control type (State vs Non-State)
- `create_zoomed_control_type_founding_cdf()` - Zoomed control type CDF (1800-1944)

**Regional Analysis:**
- `create_regional_operating_colleges_by_decade()` - Number of operating colleges by region and decade
- `create_regional_operating_public_colleges_by_decade()` - Public colleges by region and decade
- `create_colleges_per_capita_by_decade()` - Colleges per capita by region over time
- `create_public_colleges_per_capita_by_decade()` - Public colleges per capita by region
- `create_regional_capacity_per_capita_histogram()` - Student capacity per capita by region (1945)
- `create_capacity_share_by_control_and_region()` - Share of public student capacity by region (1890-1940)
- `create_capacity_share_bar_chart()` - Bar chart of state capacity share by region for specific year

**Geographic Analysis:**
- `create_city_timeline_scatter()` - Timeline scatter plot of first college foundings by city (1900-1940)
- `create_county_timeline_scatter()` - Timeline scatter plot of first college foundings by county (1900-1940)
- `create_county_analysis_table()` - LaTeX table and visualization showing county treatment/control groups for causal analysis

**Tables:**
- `create_regional_control_latex_table()` - LaTeX table of colleges founded 1900-1940 by region and control type
- `create_county_analysis_table()` - LaTeX table classifying counties for difference-in-differences analysis

**Regional Definitions:**
- **Northeast:** ME, NH, VT, MA, RI, CT, NY, NJ, PA
- **South:** DE, MD, VA, WV, KY, TN, NC, SC, GA, FL, AL, MS, AR, LA, TX, OK, DC
- **Midwest:** OH, IN, IL, MI, WI, MN, IA, MO, ND, SD, NE, KS
- **West:** MT, WY, CO, NM, ID, UT, NV, AZ, WA, OR, CA, AK, HI

**Filtering Criteria:**
Analysis excludes:
- Junior colleges
- Normal schools and teachers colleges
- Colleges with student capacity ≤ 100

**Usage:**
```bash
python founding_years_analysis.py
```

**Input:**
- `colleges_with_counties_1940.csv` - College data with 1940 county assignments
- Historical state population data by year
- 1940 county shapefiles (for total county counts)

**Outputs:**
- **Figures:** `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures/`
  - Founding year CDFs (overall, regional, by control type)
  - Operating colleges by region/decade
  - Colleges per capita by region
  - Student capacity analyses
  - City and county timeline scatter plots
  - County classification chart
- **Tables:** `/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/tables/`
  - Regional control type classifications
  - County treatment/control group assignments

### `intersect_colleges_counties_1940.py`
Performs spatial intersection of college locations with 1940 census county boundaries to assign each college to its historical county.

**Usage:**
```bash
python intersect_colleges_counties_1940.py
```

**Input:**
- `colleges_with_coordinates.csv` - Geocoded college data
- 1940 county shapefiles from NHGIS

**Output:** `colleges_with_counties_1940.csv` - College data with county assignments

## Data Pipeline

1. **Clean data:** `clean_bluebook.py` → `combined_college_blue_book_data_cleaned.csv`
2. **Geocode locations:** `geocode_colleges.py` → `colleges_with_coordinates.csv`
3. **Assign counties:** `intersect_colleges_counties_1940.py` → `colleges_with_counties_1940.csv`
4. **Generate analysis:** `founding_years_analysis.py` → figures and tables

## Requirements

- pandas
- numpy
- matplotlib
- geopy (for geocoding)
- pathlib

## Notes

- All scripts exclude junior colleges from analysis
- Founding years are filtered to be between 1600 and the data collection year (1944)
- Color schemes are consistent across visualizations for regional comparisons
- The geocoder uses a rate limiter (1 second delay) to respect API usage limits
