# Cleaned Census Data Summary

## Data Source
- **Input**: `born_georgia_linked_census_for_debugging.csv`
- **Output**: `born_georgia_linked_census_for_debugging_cleaned.csv`
- **Original observations**: 4,951,853
- **Cleaned observations**: 3,336,607
- **Records dropped**: 1,615,246 (32.6%)

## Cleaning Steps Applied

1. **Dropped individuals with age < 25 or > 70 in 1940** (679,681 individuals, 1,563,548 total observations)
2. **Dropped individuals with EDUC=99 in 1940** (16,531 individuals, 51,698 total observations)

## Variables in Cleaned Dataset

### Demographic Variables

**SEX** - Gender (recoded)
- 0 = Male (1,851,619 records, 55.5%)
- 1 = Female (1,484,988 records, 44.5%)

**AGE** - Age at census (25-70 in 1940)

**MARST** - Marital status (recoded)
- 0 = Not married (1,183,940 records, 35.5%)
- 1 = Married (2,152,667 records, 64.5%)

**RACE** - Race (original variable retained)
- 1 = White (2,478,513 records, 74.3%)
- 2 = Black (857,601 records, 25.7%)
- 3 = American Indian (429 records)
- 4 = Chinese (37 records)
- 5 = Japanese (3 records)
- 6+ = Other (24 records)

### Race Indicator Variables (NEW)

**race_white** - White indicator (1 if RACE=1, 0 otherwise)
**race_black** - Black indicator (1 if RACE=2, 0 otherwise)
**race_amind** - American Indian indicator (1 if RACE=3, 0 otherwise)
**race_chinese** - Chinese indicator (1 if RACE=4, 0 otherwise)
**race_japanese** - Japanese indicator (1 if RACE=5, 0 otherwise)
**race_other** - Other race indicator (1 if RACE not in 1-5, 0 otherwise)

### Nativity & Ethnicity

**NATIVITY** - Nativity (original variable retained)
- 0 = Missing/N/A (981,571 records)
- 1 = Native born (2,323,919 records)
- 2 = Native born, mixed parents (13,582 records)
- 3 = Native born, foreign father (3,552 records)
- 4 = Native born, foreign mother (13,983 records)
- 5 = Foreign born (0 records in this sample)

**foreign_born** (NEW) - Foreign born indicator
- 0 = Native born (3,336,607 records, 100%)
- 1 = Foreign born (0 records)

**HISPAN** - Hispanic origin (recoded)
- 0 = Not Hispanic (3,334,350 records, 99.9%)
- 1 = Hispanic (2,257 records, 0.1%)

### Education Variables

**EDUC** - Education (original variable, cleaned)
- Values 0-11 representing educational attainment
- Value 99 (missing) removed for 1940 observations

**college** (NEW) - College attendance indicator
- 0 = No college (3,253,585 records, 97.5%)
- 1 = Some college (EDUC 7-11) (83,022 records, 2.5%)

**ba** (NEW) - Bachelor's degree indicator
- 0 = No BA (3,304,033 records, 99.0%)
- 1 = BA or higher (EDUC 10-11) (32,574 records, 1.0%)

**SCHOOL** - School attendance (recoded)
- 0 = Not in school (2,954,569 records, 88.6%)
- 1 = In school (382,038 records, 11.4%)

### Labor Market Variables

**LABFORCE** - Labor force participation (recoded)
- 0 = Not in labor force (1,543,786 records, 46.3%)
- 1 = In labor force (1,576,905 records, 47.3%)
- Missing = N/A (215,916 records, 6.5%)

**CLASSWKR** - Class of worker (original variable retained)
- 0 = N/A (1,476,189 records)
- 1 = Self-employed (547,111 records)
- 2 = Wage/salary worker (1,096,482 records)
- 9 = Unknown (909 records)

**self_employed** (NEW) - Self-employment indicator
- 0 = Not self-employed (2,789,496 records, 83.6%)
- 1 = Self-employed (547,111 records, 16.4%)

### Linking & Identification Variables

**HIK** - Historical individual identifier (links same person across censuses)
**YEAR** - Census year (1900, 1910, 1920, 1930, 1940)
**BIRTHYR** - Birth year

### Geographic Variables

**STATEFIP** - State FIPS code
**COUNTYICP** - County ICPSR code

## Key Summary Statistics

- **Sample composition**: 55.5% male, 44.5% female
- **Race**: 74.3% White, 25.7% Black
- **Married**: 64.5%
- **College attendance**: 2.5%
- **BA degree**: 1.0%
- **In labor force**: 47.3% (excluding missing)
- **Self-employed**: 16.4%
- **Currently in school**: 11.4%

## Notes

- All individuals with age < 25 or > 70 in 1940 were removed (entire record history across all census years)
- All individuals with missing education (EDUC=99) in 1940 were removed (entire record history across all census years)
- Binary variables use 1/0 coding for ease of regression analysis
- All recoding uses vectorized operations for computational efficiency on large datasets
- Final sample restricted to individuals age 25-70 in 1940
