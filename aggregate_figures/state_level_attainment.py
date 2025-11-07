"""
State-Level Census Data Analyzer

This program processes census data to calculate education attainment and income statistics
at the state level. It uses chunking to handle large datasets efficiently.

For each state-cohort combination, calculates:
- High school attainment rate (EDUC 6-11)
- College attainment rate (EDUC 7-11)
- College completion rate conditional on HS completion
- Mean income wage for employed individuals (EMPSTAT==1)
"""

import pandas as pd
from typing import Iterator, Optional, Callable
import os
import argparse


class CensusDataLoader:
    """
    A class to efficiently load and process large census datasets using chunking.
    """

    def __init__(self, file_path: str, chunksize: int = 1_000_000, year_filter: int = 1940):
        """
        Initialize the CensusDataLoader.

        Parameters:
        -----------
        file_path : str
            Path to the CSV file containing census data
        chunksize : int, default=1,000,000
            Number of rows to read per chunk
        year_filter : int, default=1940
            Year to filter the data to (only rows with YEAR == year_filter will be loaded)
        """
        self.file_path = file_path
        self.chunksize = chunksize
        self.year_filter = year_filter
        self._validate_file()

    def _validate_file(self):
        """Validate that the file exists."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

    def get_chunks(self) -> Iterator[pd.DataFrame]:
        """
        Generator that yields chunks of the census data filtered by year.

        Yields:
        -------
        pd.DataFrame
            A chunk of the census data with approximately chunksize rows, filtered to year_filter
        """
        try:
            # Read columns needed for state-level analysis including income and employment
            cols_to_read = ['YEAR', 'EDUC', 'BIRTHYR', 'BPL', 'INCWAGE', 'EMPSTAT']
            for chunk in pd.read_csv(self.file_path, chunksize=self.chunksize, usecols=cols_to_read):
                chunk_filtered = chunk[chunk['YEAR'] == self.year_filter]
                if len(chunk_filtered) > 0:
                    yield chunk_filtered
        except Exception as e:
            print(f"Error reading file: {e}")
            raise

    def process_chunks(self,
                      process_func: Callable[[pd.DataFrame], any],
                      combine_func: Optional[Callable[[list], any]] = None) -> any:
        """
        Process data in chunks and optionally combine results.

        Parameters:
        -----------
        process_func : callable
            Function to apply to each chunk. Should accept a DataFrame and return a result.
        combine_func : callable, optional
            Function to combine results from all chunks. If None, returns list of results.

        Returns:
        --------
        any
            Combined results from processing all chunks
        """
        results = []
        chunk_num = 0

        for chunk in self.get_chunks():
            chunk_num += 1
            print(f"Processing chunk {chunk_num} ({len(chunk):,} rows)...")
            result = process_func(chunk)
            results.append(result)

        if combine_func is not None:
            return combine_func(results)
        return results


def map_bpl_to_state(bpl_code):
    """
    Map BPL codes to state names.

    Parameters:
    -----------
    bpl_code : int
        BPL code from IPUMS (can be state code like 13 for Georgia, or full code like 1300)

    Returns:
    --------
    str
        State name (e.g., 'Georgia', 'California') or 'Other' for non-US states
    """
    # Handle both formats: if > 100, extract state code; otherwise use as-is
    state_code = bpl_code // 100 if bpl_code >= 100 else bpl_code

    state_map = {
        1: 'Alabama', 2: 'Alaska', 4: 'Arizona', 5: 'Arkansas', 6: 'California',
        8: 'Colorado', 9: 'Connecticut', 10: 'Delaware', 11: 'District of Columbia',
        12: 'Florida', 13: 'Georgia', 15: 'Hawaii', 16: 'Idaho', 17: 'Illinois',
        18: 'Indiana', 19: 'Iowa', 20: 'Kansas', 21: 'Kentucky', 22: 'Louisiana',
        23: 'Maine', 24: 'Maryland', 25: 'Massachusetts', 26: 'Michigan',
        27: 'Minnesota', 28: 'Mississippi', 29: 'Missouri', 30: 'Montana',
        31: 'Nebraska', 32: 'Nevada', 33: 'New Hampshire', 34: 'New Jersey',
        35: 'New Mexico', 36: 'New York', 37: 'North Carolina', 38: 'North Dakota',
        39: 'Ohio', 40: 'Oklahoma', 41: 'Oregon', 42: 'Pennsylvania',
        44: 'Rhode Island', 45: 'South Carolina', 46: 'South Dakota',
        47: 'Tennessee', 48: 'Texas', 49: 'Utah', 50: 'Vermont',
        51: 'Virginia', 53: 'Washington', 54: 'West Virginia', 55: 'Wisconsin',
        56: 'Wyoming'
    }

    return state_map.get(state_code, 'Other')


def process_chunk_state_attainment(chunk: pd.DataFrame) -> pd.DataFrame:
    """
    Process a chunk to calculate education attainment and income by cohort and state.

    Parameters:
    -----------
    chunk : pd.DataFrame
        A chunk of census data

    Returns:
    --------
    pd.DataFrame
        Aggregated data with columns: hs_cohort, state, college_count, hs_count,
        total_count, income_sum, employed_count
    """
    # Make a copy to avoid SettingWithCopyWarning
    chunk = chunk.copy()

    # Map BPL to state
    chunk['state'] = chunk['BPL'].apply(map_bpl_to_state)

    # Create college attainment variable (EDUC between 7 and 11)
    chunk['college'] = ((chunk['EDUC'] >= 7) & (chunk['EDUC'] <= 11)).astype(int)

    # Create HS attainment variable (EDUC between 6 and 11)
    chunk['hs_attainment'] = ((chunk['EDUC'] >= 6) & (chunk['EDUC'] <= 11)).astype(int)

    # Create high school cohort (birth year + 18)
    chunk['hs_cohort'] = chunk['BIRTHYR'] + 18

    # Filter income data: only employed (EMPSTAT==1) and exclude missing codes
    chunk['valid_income'] = (
        (chunk['EMPSTAT'] == 1) &
        (~chunk['INCWAGE'].isin([999998, 999999]))
    )
    chunk['income_for_calc'] = chunk['INCWAGE'].where(chunk['valid_income'], 0)

    # Filter income for college-educated only
    chunk['valid_income_college'] = chunk['valid_income'] & (chunk['college'] == 1)
    chunk['income_for_calc_college'] = chunk['INCWAGE'].where(chunk['valid_income_college'], 0)

    # Filter income for HS only (EDUC = 6)
    chunk['hs_only'] = (chunk['EDUC'] == 6).astype(int)
    chunk['valid_income_hs'] = chunk['valid_income'] & (chunk['hs_only'] == 1)
    chunk['income_for_calc_hs'] = chunk['INCWAGE'].where(chunk['valid_income_hs'], 0)

    # Aggregate by cohort and state
    cohort_stats = chunk.groupby(['hs_cohort', 'state']).agg(
        college_count=('college', 'sum'),
        hs_or_more_count=('hs_attainment', 'sum'),
        total_count=('college', 'size'),
        income_sum=('income_for_calc', 'sum'),
        employed_count=('valid_income', 'sum'),
        college_income_sum=('income_for_calc_college', 'sum'),
        college_employed_count=('valid_income_college', 'sum'),
        hs_income_sum=('income_for_calc_hs', 'sum'),
        hs_employed_count=('valid_income_hs', 'sum')
    ).reset_index()

    return cohort_stats


def combine_state_results(results: list) -> pd.DataFrame:
    """
    Combine results from all chunks.

    Parameters:
    -----------
    results : list
        List of DataFrames from each chunk

    Returns:
    --------
    pd.DataFrame
        Combined and aggregated data by state with rates and mean income
    """
    # Concatenate all results
    combined = pd.concat(results, ignore_index=True)

    # Re-aggregate across all chunks
    final = combined.groupby(['hs_cohort', 'state']).agg(
        college_count=('college_count', 'sum'),
        hs_or_more_count=('hs_or_more_count', 'sum'),
        total_count=('total_count', 'sum'),
        income_sum=('income_sum', 'sum'),
        employed_count=('employed_count', 'sum'),
        college_income_sum=('college_income_sum', 'sum'),
        college_employed_count=('college_employed_count', 'sum'),
        hs_income_sum=('hs_income_sum', 'sum'),
        hs_employed_count=('hs_employed_count', 'sum')
    ).reset_index()

    # Filter to cohorts between 1890 and 1935
    final = final[(final['hs_cohort'] >= 1890) & (final['hs_cohort'] <= 1935)]

    # Create 5-year bins
    final['cohort_5year'] = (final['hs_cohort'] // 5) * 5

    # Aggregate by 5-year bins and state
    final_binned = final.groupby(['cohort_5year', 'state']).agg(
        college_count=('college_count', 'sum'),
        hs_or_more_count=('hs_or_more_count', 'sum'),
        total_count=('total_count', 'sum'),
        income_sum=('income_sum', 'sum'),
        employed_count=('employed_count', 'sum'),
        college_income_sum=('college_income_sum', 'sum'),
        college_employed_count=('college_employed_count', 'sum'),
        hs_income_sum=('hs_income_sum', 'sum'),
        hs_employed_count=('hs_employed_count', 'sum')
    ).reset_index()

    # Calculate attainment rates
    final_binned['college_rate'] = (final_binned['college_count'] / final_binned['total_count']) * 100
    final_binned['hs_or_more_rate'] = (final_binned['hs_or_more_count'] / final_binned['total_count']) * 100

    # Calculate college completion rate conditional on HS completion
    final_binned['college_given_hs_rate'] = final_binned.apply(
        lambda row: (row['college_count'] / row['hs_or_more_count']) * 100 if row['hs_or_more_count'] > 0 else None,
        axis=1
    )

    # Calculate mean income (only for those with valid employment/income data)
    final_binned['mean_incwage'] = final_binned.apply(
        lambda row: row['income_sum'] / row['employed_count'] if row['employed_count'] > 0 else None,
        axis=1
    )

    # Calculate mean income for college-educated only
    final_binned['mean_incwage_college'] = final_binned.apply(
        lambda row: row['college_income_sum'] / row['college_employed_count'] if row['college_employed_count'] > 0 else None,
        axis=1
    )

    # Calculate mean income for HS or less educated only (EDUC 1-6)
    final_binned['mean_incwage_hs'] = final_binned.apply(
        lambda row: row['hs_income_sum'] / row['hs_employed_count'] if row['hs_employed_count'] > 0 else None,
        axis=1
    )

    return final_binned


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Analyze census data for education attainment and income by state.')
    parser.add_argument('input', type=str, nargs='?',
                        default="/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/born_georgia_linked_census_for_debugging.csv",
                        help='Path to input census CSV file')
    parser.add_argument('--output', type=str,
                        default="/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output",
                        help='Directory to save output CSV')
    parser.add_argument('--year', type=int, default=1940,
                        help='Census year to filter (default: 1940)')
    parser.add_argument('--chunksize', type=int, default=1_000_000,
                        help='Number of rows per chunk (default: 1,000,000)')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    # Initialize loader
    loader = CensusDataLoader(args.input, chunksize=args.chunksize, year_filter=args.year)

    print(f"Processing census data for {args.year}...")

    # Process chunks for state-level attainment analysis
    state_data = loader.process_chunks(process_chunk_state_attainment, combine_state_results)

    # Sort by state and cohort
    state_data = state_data.sort_values(['state', 'cohort_5year'])

    print(f"\nProcessed {len(state_data):,} state-cohort combinations")
    print(f"States: {state_data['state'].nunique()}")
    print(f"Cohort range: {state_data['cohort_5year'].min()} - {state_data['cohort_5year'].max()}")
    print(f"Overall college attainment rate: {state_data['college_count'].sum() / state_data['total_count'].sum() * 100:.2f}%")
    print(f"Overall HS or more attainment rate: {state_data['hs_or_more_count'].sum() / state_data['total_count'].sum() * 100:.2f}%")

    # Calculate overall mean income
    total_income = state_data['income_sum'].sum()
    total_employed = state_data['employed_count'].sum()
    if total_employed > 0:
        print(f"Overall mean income (employed): ${total_income / total_employed:,.2f}")

    # Calculate overall mean income for college graduates
    total_college_income = state_data['college_income_sum'].sum()
    total_college_employed = state_data['college_employed_count'].sum()
    if total_college_employed > 0:
        print(f"Overall mean income (college-educated, employed): ${total_college_income / total_college_employed:,.2f}")

    # Calculate overall mean income for HS only (EDUC=6)
    total_hs_income = state_data['hs_income_sum'].sum()
    total_hs_employed = state_data['hs_employed_count'].sum()
    if total_hs_employed > 0:
        print(f"Overall mean income (HS only, employed): ${total_hs_income / total_hs_employed:,.2f}")

    # Save to CSV
    output_csv = os.path.join(args.output, "state_cohort_attainment_income.csv")

    # Select and order columns for output
    output_columns = ['state', 'cohort_5year', 'hs_or_more_rate', 'college_rate', 'college_given_hs_rate',
                      'mean_incwage', 'mean_incwage_college', 'mean_incwage_hs', 'total_count', 'employed_count',
                      'college_employed_count', 'hs_employed_count', 'college_count', 'hs_or_more_count']
    state_data[output_columns].to_csv(output_csv, index=False)

    print(f"\nCSV saved to: {output_csv}")
    print(f"Columns: {', '.join(output_columns)}")
