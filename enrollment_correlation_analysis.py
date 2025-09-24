import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_and_prepare_data(file_path):
    """Load the college data and prepare it for analysis."""
    df = pd.read_csv(file_path)

    # Filter for total category only
    df_total = df[df['category'] == 'total'].copy()

    # Convert year to numeric
    df_total['year'] = pd.to_numeric(df_total['year'], errors='coerce')

    # Convert student columns to numeric
    df_total['students_men'] = pd.to_numeric(df_total['students_men'], errors='coerce')
    df_total['students_women'] = pd.to_numeric(df_total['students_women'], errors='coerce')

    # Calculate total enrollment
    df_total['total_enrollment'] = df_total['students_men'].fillna(0) + df_total['students_women'].fillna(0)

    # Remove rows with missing data
    df_total = df_total.dropna(subset=['year', 'college', 'total_enrollment'])
    df_total = df_total[df_total['total_enrollment'] > 0]

    return df_total

def calculate_year_over_year_correlations(df, apply_filter=True):
    """Calculate correlations between consecutive available years regardless of time gap."""
    correlations_by_year = {}

    # Get unique years and sort them
    years = sorted(df['year'].unique())

    for i in range(1, len(years)):  # Start from second year since we need previous year
        current_year = years[i]
        previous_year = years[i-1]

        current_year_data = df[df['year'] == current_year].set_index('college')['total_enrollment']
        previous_year_data = df[df['year'] == previous_year].set_index('college')['total_enrollment']

        # Find common colleges
        common_colleges = current_year_data.index.intersection(previous_year_data.index)

        if len(common_colleges) > 1:
            # Handle duplicates by grouping and taking mean
            current_grouped = current_year_data.groupby(current_year_data.index).mean()
            previous_grouped = previous_year_data.groupby(previous_year_data.index).mean()

            # Get common colleges after handling duplicates
            common_colleges_clean = current_grouped.index.intersection(previous_grouped.index)

            if len(common_colleges_clean) > 1:
                current_enrollments = current_grouped.loc[common_colleges_clean]
                previous_enrollments = previous_grouped.loc[common_colleges_clean]

                if apply_filter:
                    # Filter out cases with >=100% enrollment change
                    pct_change = (current_enrollments - previous_enrollments) / previous_enrollments
                    valid_mask = (pct_change.abs() < 1.0) & (previous_enrollments > 0) & (current_enrollments > 0)

                    current_filtered = current_enrollments[valid_mask]
                    previous_filtered = previous_enrollments[valid_mask]
                    excluded_count = len(common_colleges_clean) - len(current_filtered)
                else:
                    # Use all data without filtering
                    valid_mask = (previous_enrollments > 0) & (current_enrollments > 0)
                    current_filtered = current_enrollments[valid_mask]
                    previous_filtered = previous_enrollments[valid_mask]
                    excluded_count = len(common_colleges_clean) - len(current_filtered)

                if len(current_filtered) > 1:
                    # Calculate correlation
                    correlation = current_filtered.corr(previous_filtered)
                    if not np.isnan(correlation):
                        correlations_by_year[current_year] = {
                            'correlation': correlation,
                            'previous_year': previous_year,
                            'year_gap': current_year - previous_year,
                            'common_colleges': len(current_filtered),
                            'excluded_for_large_change': excluded_count if apply_filter else 0
                        }

    return correlations_by_year

def calculate_weighted_correlations(df, apply_filter=True):
    """Calculate enrollment-weighted correlations between consecutive available years."""
    correlations_by_year = {}

    # Get unique years and sort them
    years = sorted(df['year'].unique())

    for i in range(1, len(years)):  # Start from second year since we need previous year
        current_year = years[i]
        previous_year = years[i-1]

        current_year_data = df[df['year'] == current_year].set_index('college')['total_enrollment']
        previous_year_data = df[df['year'] == previous_year].set_index('college')['total_enrollment']

        # Find common colleges
        common_colleges = current_year_data.index.intersection(previous_year_data.index)

        if len(common_colleges) > 1:
            # Handle duplicates by grouping and taking mean
            current_grouped = current_year_data.groupby(current_year_data.index).mean()
            previous_grouped = previous_year_data.groupby(previous_year_data.index).mean()

            # Get common colleges after handling duplicates
            common_colleges_clean = current_grouped.index.intersection(previous_grouped.index)

            if len(common_colleges_clean) > 1:
                current_enrollments = current_grouped.loc[common_colleges_clean]
                previous_enrollments = previous_grouped.loc[common_colleges_clean]

                if apply_filter:
                    # Filter out cases with >=100% enrollment change
                    pct_change = (current_enrollments - previous_enrollments) / previous_enrollments
                    valid_mask = (pct_change.abs() < 1.0) & (previous_enrollments > 0) & (current_enrollments > 0)

                    current_filtered = current_enrollments[valid_mask]
                    previous_filtered = previous_enrollments[valid_mask]
                    excluded_count = len(common_colleges_clean) - len(current_filtered)
                else:
                    # Use all data without filtering
                    valid_mask = (previous_enrollments > 0) & (current_enrollments > 0)
                    current_filtered = current_enrollments[valid_mask]
                    previous_filtered = previous_enrollments[valid_mask]
                    excluded_count = len(common_colleges_clean) - len(current_filtered)

                if len(current_filtered) <= 1:
                    continue

                # Use average enrollment as weights
                weights = (current_filtered + previous_filtered) / 2

                # Convert to numpy arrays
                x_arr = current_filtered.values
                y_arr = previous_filtered.values
                w_arr = weights.values

                # Remove any zero or NaN weights
                mask = (w_arr > 0) & ~np.isnan(w_arr) & ~np.isnan(x_arr) & ~np.isnan(y_arr)
                x_arr = x_arr[mask]
                y_arr = y_arr[mask]
                w_arr = w_arr[mask]
            else:
                continue

            if len(x_arr) >= 2:
                # Weighted means
                w_sum = w_arr.sum()
                x_mean = (x_arr * w_arr).sum() / w_sum
                y_mean = (y_arr * w_arr).sum() / w_sum

                # Weighted covariance and variances
                cov = ((x_arr - x_mean) * (y_arr - y_mean) * w_arr).sum() / w_sum
                var_x = ((x_arr - x_mean) ** 2 * w_arr).sum() / w_sum
                var_y = ((y_arr - y_mean) ** 2 * w_arr).sum() / w_sum

                # Correlation
                if var_x > 0 and var_y > 0:
                    correlation = cov / np.sqrt(var_x * var_y)
                else:
                    correlation = np.nan
            else:
                correlation = np.nan

            if not np.isnan(correlation):
                correlations_by_year[current_year] = {
                    'correlation': correlation,
                    'previous_year': previous_year,
                    'year_gap': current_year - previous_year,
                    'common_colleges': len(x_arr),
                    'excluded_for_large_change': excluded_count if apply_filter else 0,
                    'total_weighted_enrollment': w_arr.sum()
                }

    return correlations_by_year

def get_top_colleges_by_year(df, top_n=100):
    """Get top N colleges by enrollment for each year."""
    top_colleges_data = []

    for year in df['year'].unique():
        year_data = df[df['year'] == year]
        top_colleges = year_data.nlargest(top_n, 'total_enrollment')
        top_colleges_data.append(top_colleges)

    return pd.concat(top_colleges_data, ignore_index=True)

def create_correlation_plot(correlations_dict, title, output_path):
    """Create and save correlation plot."""
    if not correlations_dict:
        print(f"No correlation data available for {title}")
        return

    years = list(correlations_dict.keys())
    correlations = [data['correlation'] for data in correlations_dict.values()]
    year_gaps = [data['year_gap'] for data in correlations_dict.values()]

    plt.figure(figsize=(14, 8))

    # Create scatter plot without color coding
    plt.scatter(years, correlations, s=100, alpha=0.7, edgecolors='black',
               linewidth=1, color='steelblue')
    plt.plot(years, correlations, linewidth=2, alpha=0.6, color='gray')

    plt.title(f'Consecutive Year Enrollment Correlations\n{title}', fontsize=16, fontweight='bold')
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Correlation Coefficient', fontsize=12)
    plt.grid(True, alpha=0.3)

    # Set y-axis limits to accommodate negative correlations
    min_corr = min(correlations)
    max_corr = max(correlations)
    y_margin = (max_corr - min_corr) * 0.1
    plt.ylim(min_corr - y_margin, max_corr + y_margin)

    # Ensure x-axis shows whole numbers
    plt.xticks(years)

    # Add correlation values, year gaps, and exclusion rates as text
    for year, data in correlations_dict.items():
        corr = data['correlation']
        gap = data['year_gap']
        prev_year = data['previous_year']
        excluded = data.get('excluded_for_large_change', 0)
        included = data['common_colleges']
        total = included + excluded
        exclusion_rate = (excluded / total * 100) if total > 0 else 0

        exclusion_text = f'{exclusion_rate:.1f}% excluded' if data.get('excluded_for_large_change', 0) > 0 else 'no exclusions'
        plt.annotate(f'{corr:.3f}\n({prev_year}→{year})\n{exclusion_text}',
                    (year, corr), textcoords="offset points", xytext=(0,15), ha='center',
                    fontsize=8, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Plot saved to: {output_path}")

def prepare_market_share_data(df):
    """Prepare market share data excluding 1916 and colleges not present in all years."""
    # Filter for total category only
    df_total = df[df['category'] == 'total'].copy()
    df_total['year'] = pd.to_numeric(df_total['year'], errors='coerce')
    df_total['students_men'] = pd.to_numeric(df_total['students_men'], errors='coerce')
    df_total['students_women'] = pd.to_numeric(df_total['students_women'], errors='coerce')
    df_total['total_enrollment'] = df_total['students_men'].fillna(0) + df_total['students_women'].fillna(0)
    df_total = df_total.dropna(subset=['year', 'college', 'total_enrollment'])
    df_total = df_total[df_total['total_enrollment'] > 0]

    # Handle duplicates by taking mean enrollment
    df_grouped = df_total.groupby(['year', 'college'])['total_enrollment'].mean().reset_index()

    # Exclude University of the Philippines
    df_grouped = df_grouped[df_grouped['college'] != 'University of the Philippines']

    # Exclude 1916
    years = sorted([year for year in df_grouped['year'].unique() if year != 1916])

    # Find colleges that appear in ALL years
    colleges_by_year = {}
    for year in years:
        colleges_by_year[year] = set(df_grouped[df_grouped['year'] == year]['college'].unique())

    # Get intersection of all years (colleges present in every year)
    colleges_in_all_years = set.intersection(*colleges_by_year.values())
    print(f"Colleges present in all {len(years)} years: {len(colleges_in_all_years)}")

    # Filter to only include colleges present in all years
    df_filtered = df_grouped[df_grouped['college'].isin(colleges_in_all_years)]

    market_share_data = []

    for year in years:
        year_data = df_filtered[df_filtered['year'] == year].copy()
        total_enrollment_year = year_data['total_enrollment'].sum()

        # Get top 10 colleges by enrollment (from those present in all years)
        top10 = year_data.nlargest(10, 'total_enrollment')
        top10_total = top10['total_enrollment'].sum()
        market_share = (top10_total / total_enrollment_year) * 100

        market_share_data.append({
            'year': year,
            'market_share': market_share,
            'top10_enrollment': top10_total,
            'total_enrollment': total_enrollment_year,
            'top_colleges': list(top10[['college', 'total_enrollment']].values)
        })

    return market_share_data

def create_market_share_percentage_plot(df, output_path):
    """Create and save market share percentage plot."""
    print("Creating top 10 colleges market share percentage plot...")

    market_share_data = prepare_market_share_data(df)

    plt.figure(figsize=(14, 8))

    years_list = [d['year'] for d in market_share_data]
    market_shares = [d['market_share'] for d in market_share_data]

    plt.plot(years_list, market_shares, marker='o', linewidth=3, markersize=10,
             color='darkblue', markerfacecolor='lightblue', markeredgecolor='darkblue', markeredgewidth=2)
    plt.title('Market Share of Top 10 Colleges by Total Enrollment\n(1916 excluded, only colleges present in all years)', fontsize=16, fontweight='bold')
    plt.ylabel('Market Share (%)', fontsize=12)
    plt.xlabel('Year', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.ylim(0, max(market_shares) * 1.1)

    # Ensure x-axis shows whole numbers
    plt.xticks(years_list)

    # Add percentage values as text
    for year, share in zip(years_list, market_shares):
        plt.annotate(f'{share:.1f}%', (year, share), textcoords="offset points",
                    xytext=(0,10), ha='center', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Market share percentage plot saved to: {output_path}")

def create_top10_composition_plot(df, output_path):
    """Create and save top 10 colleges composition plot."""
    print("Creating top 10 colleges composition plot...")

    market_share_data = prepare_market_share_data(df)

    # Create figure with more space for legend
    fig, (ax, ax_legend) = plt.subplots(1, 2, figsize=(20, 10), gridspec_kw={'width_ratios': [3, 1]})

    # Use distinct colors
    colors = plt.cm.tab20(np.linspace(0, 1, 20))

    # Collect all unique colleges and create shortened names
    all_colleges = set()
    for data in market_share_data:
        for college, _ in data['top_colleges']:
            all_colleges.add(college)

    def get_short_name(college):
        """Create consistent short names for bars with no ambiguous abbreviations."""
        if 'University of California' in college:
            return 'UC'
        elif 'New York University' in college:
            return 'NYU'
        elif 'University of Chicago' in college:
            return 'U.Chicago'
        elif 'University of Michigan' in college:
            return 'U.Michigan'
        elif 'University of Minnesota' in college:
            return 'U.Minnesota'
        elif 'Columbia University' in college:
            return 'Columbia'
        elif 'Cornell University' in college:
            return 'Cornell'
        elif 'University of Pennsylvania' in college:
            return 'U.Penn'
        elif 'University of Illinois' in college:
            return 'U.Illinois'
        elif 'College of the City of New York' in college:
            return 'CCNY'
        elif 'The City College' in college:
            return 'City College'
        elif 'Cooper Union' in college:
            return 'Cooper Union'
        elif 'Pennsylvania State College' in college:
            return 'Penn State'
        elif 'Purdue University' in college:
            return 'Purdue'
        elif 'Yale University' in college:
            return 'Yale'
        elif 'Harvard University' in college:
            return 'Harvard'
        elif 'Howard University' in college:
            return 'Howard'
        elif 'Northwestern University' in college:
            return 'Northwestern'
        elif 'University of Pittsburgh' in college:
            return 'U.Pittsburgh'
        elif 'University of Southern California' in college:
            return 'USC'
        elif 'Western Reserve University' in college:
            return 'W.Reserve'
        elif 'Ohio State University' in college:
            return 'Ohio State'
        elif 'University of Wisconsin' in college:
            return 'U.Wisconsin'
        elif 'Carnegie Institute of Technology' in college:
            return 'Carnegie Tech'
        elif 'Junior College' in college:
            return 'Junior College'
        elif 'Non-Collegiate Institution' in college:
            return 'Non-Collegiate'
        elif 'Colleges of the City of Detroit' in college:
            return 'Detroit City'
        else:
            # For any other college, use a more descriptive abbreviation
            words = college.split()
            if len(words) >= 2:
                # Take first letter of each word, but keep it readable
                if len(college) <= 12:
                    return college
                else:
                    # Create abbreviation from key words
                    key_words = [w for w in words if w not in ['of', 'the', 'and', 'for', 'in', 'at']]
                    if len(key_words) >= 2:
                        return f"{key_words[0][:4]}.{key_words[1][:4]}"
                    else:
                        return college[:10]
            else:
                return college[:10]

    def get_legend_name(college):
        """Create legend names (less abbreviated)."""
        if 'University of California' in college:
            return 'University of California'
        elif 'New York University' in college:
            return 'New York University'
        elif 'University of Chicago' in college:
            return 'University of Chicago'
        elif 'University of Michigan' in college:
            return 'University of Michigan'
        elif 'University of Minnesota' in college:
            return 'University of Minnesota'
        elif 'Columbia University' in college:
            return 'Columbia University'
        elif 'Cornell University' in college:
            return 'Cornell University'
        elif 'University of Pennsylvania' in college:
            return 'University of Pennsylvania'
        elif 'University of Illinois' in college:
            return 'University of Illinois'
        elif 'College of the City of New York' in college:
            return 'College of the City of NY'
        elif 'The City College' in college:
            return 'The City College'
        elif 'Cooper Union' in college:
            return 'Cooper Union'
        elif 'Pennsylvania State College' in college:
            return 'Pennsylvania State College'
        elif 'Purdue University' in college:
            return 'Purdue University'
        elif 'Yale University' in college:
            return 'Yale University'
        elif 'Howard University' in college:
            return 'Howard University'
        elif 'Northwestern University' in college:
            return 'Northwestern University'
        else:
            return college[:25] + '...' if len(college) > 25 else college

    college_short_names = {college: get_short_name(college) for college in sorted(all_colleges)}
    college_legend_names = {college: get_legend_name(college) for college in sorted(all_colleges)}
    college_colors = {college: colors[i % len(colors)] for i, college in enumerate(sorted(all_colleges))}

    # Plot the stacked bars
    for i, data in enumerate(market_share_data):
        year = data['year']
        total_year_enrollment = data['total_enrollment']
        bottom = 0

        for college, enrollment in data['top_colleges']:
            share = (enrollment / total_year_enrollment) * 100
            ax.bar(year, share, bottom=bottom, color=college_colors[college],
                   width=1.8, alpha=0.8, edgecolor='white', linewidth=0.5)

            # Always add text for all colleges in the top 10
            if share > 0.8:  # Very low threshold to include almost all
                ax.text(year, bottom + share/2, college_short_names[college],
                       ha='center', va='center', fontsize=7, rotation=0,
                       fontweight='bold', color='black')

            bottom += share

    ax.set_title('Top 10 Colleges by Enrollment Share Each Year\n(1916 and U. Philippines excluded, only colleges present in all years)',
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Enrollment Share (%)', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')

    # Set y-axis limit based on max market share
    max_share = max([d['market_share'] for d in market_share_data])
    ax.set_ylim(0, max_share * 1.05)

    # Ensure x-axis shows whole numbers
    years_list = [d['year'] for d in market_share_data]
    ax.set_xticks(years_list)

    # Create legend showing top colleges with their colors
    legend_elements = []
    # Get most frequent colleges across all years
    college_frequency = {}
    for data in market_share_data:
        for college, _ in data['top_colleges']:
            college_frequency[college] = college_frequency.get(college, 0) + 1

    # Sort by frequency and take top colleges
    top_frequent_colleges = sorted(college_frequency.items(), key=lambda x: x[1], reverse=True)[:15]

    for college, freq in top_frequent_colleges:
        legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=college_colors[college],
                                           alpha=0.8, label=f"{college_legend_names[college]} ({freq} years)"))

    ax_legend.legend(handles=legend_elements, loc='center', fontsize=9,
                    title='Most Frequent Top 10 Colleges', title_fontsize=11)
    ax_legend.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Top 10 composition plot saved to: {output_path}")

    # Print summary of market share data
    print("\n=== TOP 10 COLLEGES MARKET SHARE SUMMARY (1916 excluded, only colleges present in all years) ===")
    for data in market_share_data:
        year = data['year']
        share = data['market_share']
        print(f"\n{year}: Top 10 colleges hold {share:.1f}% of total enrollment")
        print("  Top 5 colleges:")
        for i, (college, enrollment) in enumerate(data['top_colleges'][:5]):
            college_share = (enrollment / data['total_enrollment']) * 100
            print(f"    {i+1}. {college}: {enrollment:,} students ({college_share:.1f}%)")

def main():
    # File paths
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/cleaned_appended_college_data.csv"
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"

    print("Loading and preparing data...")
    df = load_and_prepare_data(data_path)

    print(f"Data loaded: {len(df)} records across {df['year'].nunique()} years")
    print(f"Years available: {sorted(df['year'].unique())}")
    print(f"Number of unique colleges: {df['college'].nunique()}")

    # Analysis 1: All colleges (unweighted, filtered)
    print("\nCalculating correlations for all colleges (filtered)...")
    all_college_correlations = calculate_year_over_year_correlations(df, apply_filter=True)

    # Analysis 2: Top 100 colleges by enrollment each year (unweighted, filtered)
    print("Calculating correlations for top 100 colleges by enrollment each year (filtered)...")
    top_colleges_df = get_top_colleges_by_year(df, top_n=100)
    top_100_correlations = calculate_year_over_year_correlations(top_colleges_df, apply_filter=True)

    # Analysis 3: All colleges (weighted by enrollment, filtered)
    print("Calculating enrollment-weighted correlations for all colleges (filtered)...")
    all_college_weighted_correlations = calculate_weighted_correlations(df, apply_filter=True)

    # Analysis 4: Top 100 colleges (weighted by enrollment, filtered)
    print("Calculating enrollment-weighted correlations for top 100 colleges (filtered)...")
    top_100_weighted_correlations = calculate_weighted_correlations(top_colleges_df, apply_filter=True)

    # Analysis 5-8: Unfiltered versions
    print("\nCalculating correlations for all colleges (unfiltered)...")
    all_college_correlations_unfiltered = calculate_year_over_year_correlations(df, apply_filter=False)

    print("Calculating correlations for top 100 colleges (unfiltered)...")
    top_100_correlations_unfiltered = calculate_year_over_year_correlations(top_colleges_df, apply_filter=False)

    print("Calculating enrollment-weighted correlations for all colleges (unfiltered)...")
    all_college_weighted_correlations_unfiltered = calculate_weighted_correlations(df, apply_filter=False)

    print("Calculating enrollment-weighted correlations for top 100 colleges (unfiltered)...")
    top_100_weighted_correlations_unfiltered = calculate_weighted_correlations(top_colleges_df, apply_filter=False)

    # Create plots
    print("\nCreating correlation plots...")

    # Filtered plots
    # Plot 1: All colleges (unweighted, filtered)
    plot1_path = Path(output_dir) / "corr_plot_enrollment_all_colleges_filtered.png"
    create_correlation_plot(all_college_correlations, "All Colleges (Unweighted, Filtered)", plot1_path)

    # Plot 2: Top 100 colleges (unweighted, filtered)
    plot2_path = Path(output_dir) / "corr_plot_enrollment_top100_filtered.png"
    create_correlation_plot(top_100_correlations, "Top 100 Colleges (Unweighted, Filtered)", plot2_path)

    # Plot 3: All colleges (weighted, filtered)
    plot3_path = Path(output_dir) / "corr_plot_enrollment_all_colleges_weighted_filtered.png"
    create_correlation_plot(all_college_weighted_correlations, "All Colleges (Enrollment-Weighted, Filtered)", plot3_path)

    # Plot 4: Top 100 colleges (weighted, filtered)
    plot4_path = Path(output_dir) / "corr_plot_enrollment_top100_weighted_filtered.png"
    create_correlation_plot(top_100_weighted_correlations, "Top 100 Colleges (Enrollment-Weighted, Filtered)", plot4_path)

    # Unfiltered plots
    # Plot 5: All colleges (unweighted, unfiltered)
    plot5_path = Path(output_dir) / "corr_plot_enrollment_all_colleges_unfiltered.png"
    create_correlation_plot(all_college_correlations_unfiltered, "All Colleges (Unweighted, Unfiltered)", plot5_path)

    # Plot 6: Top 100 colleges (unweighted, unfiltered)
    plot6_path = Path(output_dir) / "corr_plot_enrollment_top100_unfiltered.png"
    create_correlation_plot(top_100_correlations_unfiltered, "Top 100 Colleges (Unweighted, Unfiltered)", plot6_path)

    # Plot 7: All colleges (weighted, unfiltered)
    plot7_path = Path(output_dir) / "corr_plot_enrollment_all_colleges_weighted_unfiltered.png"
    create_correlation_plot(all_college_weighted_correlations_unfiltered, "All Colleges (Enrollment-Weighted, Unfiltered)", plot7_path)

    # Plot 8: Top 100 colleges (weighted, unfiltered)
    plot8_path = Path(output_dir) / "corr_plot_enrollment_top100_weighted_unfiltered.png"
    create_correlation_plot(top_100_weighted_correlations_unfiltered, "Top 100 Colleges (Enrollment-Weighted, Unfiltered)", plot8_path)

    # Plot 9: Top 10 colleges market share percentage
    plot9_path = Path(output_dir) / "top10_market_share_percentage.png"
    create_market_share_percentage_plot(df, plot9_path)

    # Plot 10: Top 10 colleges composition by year
    plot10_path = Path(output_dir) / "top10_colleges_composition.png"
    create_top10_composition_plot(df, plot10_path)

    # Print summary statistics
    print("\n=== SUMMARY RESULTS ===")
    print("\n" + "="*60)
    print("FILTERED RESULTS (≥100% enrollment change excluded)")
    print("="*60)

    print(f"\nAll Colleges Correlations (Unweighted, Filtered):")
    for year, data in sorted(all_college_correlations.items()):
        excluded = data.get('excluded_for_large_change', 0)
        print(f"  {data['previous_year']} → {year} (gap: {data['year_gap']} years): {data['correlation']:.4f} ({data['common_colleges']} colleges, {excluded} excluded)")

    print(f"\nTop 100 Colleges Correlations (Unweighted, Filtered):")
    for year, data in sorted(top_100_correlations.items()):
        excluded = data.get('excluded_for_large_change', 0)
        print(f"  {data['previous_year']} → {year} (gap: {data['year_gap']} years): {data['correlation']:.4f} ({data['common_colleges']} colleges, {excluded} excluded)")

    print("\n" + "="*60)
    print("UNFILTERED RESULTS (all data included)")
    print("="*60)

    print(f"\nAll Colleges Correlations (Unweighted, Unfiltered):")
    for year, data in sorted(all_college_correlations_unfiltered.items()):
        print(f"  {data['previous_year']} → {year} (gap: {data['year_gap']} years): {data['correlation']:.4f} ({data['common_colleges']} colleges)")

    print(f"\nTop 100 Colleges Correlations (Unweighted, Unfiltered):")
    for year, data in sorted(top_100_correlations_unfiltered.items()):
        print(f"  {data['previous_year']} → {year} (gap: {data['year_gap']} years): {data['correlation']:.4f} ({data['common_colleges']} colleges)")

    # Calculate averages
    print("\n" + "="*60)
    print("AVERAGE CORRELATIONS COMPARISON")
    print("="*60)

    if all_college_correlations:
        avg_corr_all_filtered = np.mean([data['correlation'] for data in all_college_correlations.values()])
        print(f"All colleges (unweighted, filtered): {avg_corr_all_filtered:.4f}")

    if all_college_correlations_unfiltered:
        avg_corr_all_unfiltered = np.mean([data['correlation'] for data in all_college_correlations_unfiltered.values()])
        print(f"All colleges (unweighted, unfiltered): {avg_corr_all_unfiltered:.4f}")

    if top_100_correlations:
        avg_corr_top100_filtered = np.mean([data['correlation'] for data in top_100_correlations.values()])
        print(f"Top 100 colleges (unweighted, filtered): {avg_corr_top100_filtered:.4f}")

    if top_100_correlations_unfiltered:
        avg_corr_top100_unfiltered = np.mean([data['correlation'] for data in top_100_correlations_unfiltered.values()])
        print(f"Top 100 colleges (unweighted, unfiltered): {avg_corr_top100_unfiltered:.4f}")

    if all_college_weighted_correlations:
        avg_corr_all_weighted_filtered = np.mean([data['correlation'] for data in all_college_weighted_correlations.values()])
        print(f"All colleges (weighted, filtered): {avg_corr_all_weighted_filtered:.4f}")

    if all_college_weighted_correlations_unfiltered:
        avg_corr_all_weighted_unfiltered = np.mean([data['correlation'] for data in all_college_weighted_correlations_unfiltered.values()])
        print(f"All colleges (weighted, unfiltered): {avg_corr_all_weighted_unfiltered:.4f}")

    if top_100_weighted_correlations:
        avg_corr_top100_weighted_filtered = np.mean([data['correlation'] for data in top_100_weighted_correlations.values()])
        print(f"Top 100 colleges (weighted, filtered): {avg_corr_top100_weighted_filtered:.4f}")

    if top_100_weighted_correlations_unfiltered:
        avg_corr_top100_weighted_unfiltered = np.mean([data['correlation'] for data in top_100_weighted_correlations_unfiltered.values()])
        print(f"Top 100 colleges (weighted, unfiltered): {avg_corr_top100_weighted_unfiltered:.4f}")

if __name__ == "__main__":
    main()