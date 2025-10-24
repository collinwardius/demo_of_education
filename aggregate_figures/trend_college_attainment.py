"""
Census Data Loader with Chunking

This program loads census data in chunks to handle large datasets efficiently.
It reads 1,000,000 observations at a time to manage memory usage.
"""

import pandas as pd
import matplotlib.pyplot as plt
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
            # Only read the columns we need for efficiency
            cols_to_read = ['YEAR', 'EDUC', 'BIRTHYR']
            for chunk in pd.read_csv(self.file_path, chunksize=self.chunksize, usecols=cols_to_read):
                chunk_filtered = chunk[chunk['YEAR'] == self.year_filter]
                if len(chunk_filtered) > 0:
                    yield chunk_filtered
        except Exception as e:
            print(f"Error reading file: {e}")
            raise

    def load_all(self) -> pd.DataFrame:
        """
        Load the entire dataset into memory, filtered by year.
        WARNING: Use only if you're confident the data fits in memory.

        Returns:
        --------
        pd.DataFrame
            The complete census dataset filtered to year_filter
        """
        print(f"Loading dataset from {self.file_path} for year {self.year_filter}...")
        df = pd.read_csv(self.file_path)
        df = df[df['YEAR'] == self.year_filter]
        print(f"Loaded {len(df):,} rows with {len(df.columns)} columns")
        return df

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

    def get_dataset_info(self) -> dict:
        """
        Get information about the filtered dataset without loading all data.

        Returns:
        --------
        dict
            Dictionary containing dataset metadata for filtered data
        """
        # Read chunks and count rows matching year filter
        total_rows = 0
        first_chunk = None

        for chunk in pd.read_csv(self.file_path, chunksize=self.chunksize):
            chunk_filtered = chunk[chunk['YEAR'] == self.year_filter]
            total_rows += len(chunk_filtered)
            if first_chunk is None and len(chunk_filtered) > 0:
                first_chunk = chunk_filtered

        info = {
            'file_path': self.file_path,
            'year_filter': self.year_filter,
            'total_rows': total_rows,
            'columns': list(first_chunk.columns) if first_chunk is not None else [],
            'num_columns': len(first_chunk.columns) if first_chunk is not None else 0,
            'dtypes': first_chunk.dtypes.to_dict() if first_chunk is not None else {},
            'estimated_chunks': (total_rows // self.chunksize) + 1 if total_rows > 0 else 0
        }

        return info


def process_chunk_college_attainment(chunk: pd.DataFrame) -> pd.DataFrame:
    """
    Process a chunk to calculate college and HS attainment by cohort.

    Parameters:
    -----------
    chunk : pd.DataFrame
        A chunk of census data

    Returns:
    --------
    pd.DataFrame
        Aggregated data with columns: hs_cohort, college_count, hs_count, total_count
    """
    # Make a copy to avoid SettingWithCopyWarning
    chunk = chunk.copy()

    # Create college attainment variable (EDUC between 7 and 11)
    chunk['college'] = ((chunk['EDUC'] >= 7) & (chunk['EDUC'] <= 11)).astype(int)

    # Create HS attainment variable (EDUC between 6 and 11)
    chunk['hs_attainment'] = ((chunk['EDUC'] >= 6) & (chunk['EDUC'] <= 11)).astype(int)

    # Create high school cohort (birth year + 18)
    chunk['hs_cohort'] = chunk['BIRTHYR'] + 18

    # Aggregate by cohort
    cohort_stats = chunk.groupby('hs_cohort').agg(
        college_count=('college', 'sum'),
        hs_count=('hs_attainment', 'sum'),
        total_count=('college', 'size')
    ).reset_index()

    return cohort_stats


def combine_college_results(results: list) -> pd.DataFrame:
    """
    Combine results from all chunks.

    Parameters:
    -----------
    results : list
        List of DataFrames from each chunk

    Returns:
    --------
    pd.DataFrame
        Combined and aggregated data
    """
    # Concatenate all results
    combined = pd.concat(results, ignore_index=True)

    # Re-aggregate across all chunks
    final = combined.groupby('hs_cohort').agg(
        college_count=('college_count', 'sum'),
        hs_count=('hs_count', 'sum'),
        total_count=('total_count', 'sum')
    ).reset_index()

    # Filter to cohorts between 1890 and 1935
    final = final[(final['hs_cohort'] >= 1890) & (final['hs_cohort'] <= 1935)]

    # Create 5-year bins
    final['cohort_5year'] = (final['hs_cohort'] // 5) * 5

    # Aggregate by 5-year bins
    final_binned = final.groupby('cohort_5year').agg(
        college_count=('college_count', 'sum'),
        hs_count=('hs_count', 'sum'),
        total_count=('total_count', 'sum')
    ).reset_index()

    # Calculate attainment rates
    final_binned['college_rate'] = (final_binned['college_count'] / final_binned['total_count']) * 100
    final_binned['hs_rate'] = (final_binned['hs_count'] / final_binned['total_count']) * 100

    return final_binned


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Analyze census data for college and HS attainment by cohort.')
    parser.add_argument('input', type=str, nargs='?',
                        default="/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/census/born_georgia_linked_census_for_debugging.csv",
                        help='Path to input census CSV file')
    parser.add_argument('--output', type=str,
                        default="/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures",
                        help='Directory to save output figures')
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

    # Process chunks for college attainment analysis
    cohort_data = loader.process_chunks(process_chunk_college_attainment, combine_college_results)

    # Sort by cohort
    cohort_data = cohort_data.sort_values('cohort_5year')

    print(f"\nProcessed {len(cohort_data):,} 5-year cohort bins")
    print(f"Cohort range: {cohort_data['cohort_5year'].min()} - {cohort_data['cohort_5year'].max()}")
    print(f"Overall college attainment rate: {cohort_data['college_count'].sum() / cohort_data['total_count'].sum() * 100:.2f}%")
    print(f"Overall HS attainment rate: {cohort_data['hs_count'].sum() / cohort_data['total_count'].sum() * 100:.2f}%")

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(cohort_data['cohort_5year'], cohort_data['college_rate'],
            linewidth=2, marker='o', markersize=5, label='College')

    ax.set_xlabel('High School Cohort (5-Year Bins)', fontsize=12)
    ax.set_ylabel('Attainment Rate (%)', fontsize=12)
    ax.set_title(f'College Attainment by High School Cohort, 1890-1935 ({args.year} Census)', fontsize=14)
    ax.legend(fontsize=14)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    output_path = os.path.join(args.output, "college_attainment_by_cohort.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved to: {output_path}")

    plt.close()

