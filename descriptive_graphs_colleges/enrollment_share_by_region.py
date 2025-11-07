import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_enrollment_share_by_region():
    """Create bar chart showing enrollment share in junior vs conventional colleges by region."""

    # Load data
    data_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_counties_1940.csv"
    df = pd.read_csv(data_path)

    print(f"\nLoaded {len(df)} colleges")

    # Regional mapping
    state_to_region = {
        # Northeast
        'MAINE': 'Northeast', 'NEW HAMPSHIRE': 'Northeast', 'VERMONT': 'Northeast',
        'MASSACHUSETTS': 'Northeast', 'RHODE ISLAND': 'Northeast', 'CONNECTICUT': 'Northeast',
        'NEW YORK': 'Northeast', 'NEW JERSEY': 'Northeast', 'PENNSYLVANIA': 'Northeast',

        # South
        'DELAWARE': 'South', 'MARYLAND': 'South', 'VIRGINIA': 'South', 'WEST VIRGINIA': 'South',
        'KENTUCKY': 'South', 'TENNESSEE': 'South', 'NORTH CAROLINA': 'South', 'SOUTH CAROLINA': 'South',
        'GEORGIA': 'South', 'FLORIDA': 'South', 'ALABAMA': 'South', 'MISSISSIPPI': 'South',
        'ARKANSAS': 'South', 'LOUISIANA': 'South', 'TEXAS': 'South', 'OKLAHOMA': 'South',
        'DISTRICT OF COLUMBIA': 'South',

        # Midwest
        'OHIO': 'Midwest', 'INDIANA': 'Midwest', 'ILLINOIS': 'Midwest', 'MICHIGAN': 'Midwest',
        'WISCONSIN': 'Midwest', 'MINNESOTA': 'Midwest', 'IOWA': 'Midwest', 'MISSOURI': 'Midwest',
        'NORTH DAKOTA': 'Midwest', 'SOUTH DAKOTA': 'Midwest', 'NEBRASKA': 'Midwest', 'KANSAS': 'Midwest',

        # West
        'MONTANA': 'West', 'WYOMING': 'West', 'COLORADO': 'West', 'NEW MEXICO': 'West',
        'IDAHO': 'West', 'UTAH': 'West', 'NEVADA': 'West', 'ARIZONA': 'West',
        'WASHINGTON': 'West', 'OREGON': 'West', 'CALIFORNIA': 'West', 'ALASKA': 'West', 'HAWAII': 'West'
    }

    # Map states to regions
    df['Region'] = df['State'].map(state_to_region)

    # Create college type category (Junior vs Conventional)
    df['College_Category'] = df['College_Type'].apply(
        lambda x: 'Junior Colleges' if x == 'Junior Colleges' else 'Conventional Colleges'
    )

    # Calculate total enrollment (convert to numeric, handling missing values)
    df['Male_Enrollment'] = pd.to_numeric(df['Male_Enrollment'], errors='coerce').fillna(0)
    df['Female_Enrollment'] = pd.to_numeric(df['Female_Enrollment'], errors='coerce').fillna(0)
    df['Total_Enrollment'] = df['Male_Enrollment'] + df['Female_Enrollment']

    # Filter out records with missing region or zero enrollment
    df_filtered = df[(df['Region'].notna()) & (df['Total_Enrollment'] > 0)].copy()

    print(f"\nRecords with valid region and enrollment: {len(df_filtered)}")
    print(f"\nTotal enrollment in dataset: {df_filtered['Total_Enrollment'].sum():,.0f}")

    # Calculate enrollment by region and college category
    enrollment_by_region = df_filtered.groupby(['Region', 'College_Category'])['Total_Enrollment'].sum().reset_index()

    # Calculate total enrollment by region
    total_by_region = df_filtered.groupby('Region')['Total_Enrollment'].sum().reset_index()
    total_by_region.columns = ['Region', 'Total_Regional_Enrollment']

    # Merge to calculate shares
    enrollment_shares = enrollment_by_region.merge(total_by_region, on='Region')
    enrollment_shares['Share'] = (enrollment_shares['Total_Enrollment'] / enrollment_shares['Total_Regional_Enrollment']) * 100

    print("\nEnrollment shares by region and college type:")
    print(enrollment_shares)

    # Pivot data for plotting
    pivot_data = enrollment_shares.pivot(index='Region', columns='College_Category', values='Share').fillna(0)

    # Ensure both columns exist
    if 'Junior Colleges' not in pivot_data.columns:
        pivot_data['Junior Colleges'] = 0
    if 'Conventional Colleges' not in pivot_data.columns:
        pivot_data['Conventional Colleges'] = 0

    # Order regions
    region_order = ['Northeast', 'South', 'Midwest', 'West']
    pivot_data = pivot_data.reindex(region_order)

    # Create the grouped bar chart
    fig, ax = plt.subplots(figsize=(12, 8))

    x = np.arange(len(region_order))
    width = 0.35

    bars1 = ax.bar(x - width/2, pivot_data['Junior Colleges'], width,
                   label='Junior Colleges', color='#ff7f0e', alpha=0.8)
    bars2 = ax.bar(x + width/2, pivot_data['Conventional Colleges'], width,
                   label='Conventional Colleges', color='#1f77b4', alpha=0.8)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=10)

    # Customize plot
    ax.set_xlabel('Region', fontsize=12, fontweight='bold')
    ax.set_ylabel('Share of Total Enrollment (%)', fontsize=12, fontweight='bold')
    ax.set_title('Enrollment Share in Junior vs Conventional Colleges by Region\n(Colleges existing as of 1944)',
                fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(region_order, fontsize=11)
    ax.legend(fontsize=11, loc='upper right', framealpha=0.9)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    # Save the figure
    output_dir = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "enrollment_share_by_region.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\nEnrollment share graph saved to: {output_path}")

    # Print summary statistics
    print("\nSummary by Region:")
    for region in region_order:
        if region in pivot_data.index:
            junior_share = pivot_data.loc[region, 'Junior Colleges']
            conventional_share = pivot_data.loc[region, 'Conventional Colleges']
            print(f"\n{region}:")
            print(f"  Junior Colleges: {junior_share:.1f}%")
            print(f"  Conventional Colleges: {conventional_share:.1f}%")

if __name__ == "__main__":
    create_enrollment_share_by_region()
