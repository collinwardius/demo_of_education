import pandas as pd
import matplotlib.pyplot as plt

# Load the college data CSV
data_path = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/combined_college_blue_book_data_cleaned.csv'
df = pd.read_csv(data_path)

# Output directory for figures
output_dir = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures'

print("=" * 80)
print("DATASET OVERVIEW")
print("=" * 80)
print(f"\nDataset shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"\nColumn names: {list(df.columns)}")

# Check for year column name
year_cols = [col for col in df.columns if 'year' in col.lower() or 'found' in col.lower()]
print(f"\nYear-related columns: {year_cols}")

# Display sample of data
print("\nFirst few rows:")
print(df.head())

# Filter for colleges founded between 1900 and 1940
# Need to identify the correct year column
if 'year_founding' in df.columns:
    year_col = 'year_founding'
elif 'founding_year' in df.columns:
    year_col = 'founding_year'
elif 'year' in df.columns:
    year_col = 'year'
else:
    year_col = year_cols[0] if year_cols else None

if year_col:
    print(f"\nUsing '{year_col}' as the founding year column")
    # Convert year column to numeric, handling any non-numeric values
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    missing_years = df[year_col].isna().sum()
    print(f"Colleges with missing founding year: {missing_years}")
    df_filtered = df[(df[year_col] >= 1900) & (df[year_col] <= 1940)].copy()
    print(f"Colleges founded 1900-1940: {len(df_filtered)}")
else:
    print("\nWarning: Could not identify year column")
    df_filtered = df.copy()

print("\n" + "=" * 80)
print("DEMOGRAPHIC-SPECIFIC COLLEGES (1900-1940)")
print("=" * 80)

# Count each category
womens_colleges = len(df_filtered[df_filtered['Gender'] == 'W'])
mens_colleges = len(df_filtered[df_filtered['Gender'] == 'M'])
historically_black = len(df_filtered[df_filtered['College_Type'] == 'Colleges Especially for Negroes'])

print(f"Women's colleges: {womens_colleges}")
print(f"Men's colleges: {mens_colleges}")
print(f"Historically Black colleges: {historically_black}")

# Create bar graph
fig, ax = plt.subplots(figsize=(10, 7))

categories = ["Women's Colleges", "Men's Colleges", "Historically Black Colleges"]
counts = [womens_colleges, mens_colleges, historically_black]

# Use distinct colors for demographic categories (different from other figures)
colors = ['#d62728', '#9467bd', '#8c564b']  # Red, Purple, Brown

bars = ax.bar(range(len(categories)), counts, color=colors, width=0.6)

# Customize the plot
ax.set_xticks(range(len(categories)))
ax.set_xticklabels(categories, rotation=0, ha='center')
ax.set_ylabel('Number of Colleges Founded', fontsize=12)
ax.set_xlabel('College Type', fontsize=12)
ax.set_title('Specialized Colleges by Target Demographic, 1900-1940', fontsize=14)

# Add value labels on top of bars
for i, (bar, value) in enumerate(zip(bars, counts)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{int(value)}',
            ha='center', va='bottom', fontsize=11)

# Add light grid
ax.grid(True, alpha=0.3, axis='y')
ax.set_axisbelow(True)

# Set y-axis limits
ax.set_ylim(0, max(counts) * 1.15)

# Tight layout
plt.tight_layout()

# Save the figure
output_path = f'{output_dir}/demographic_specific_colleges_1900_1940.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n✓ Figure saved to: {output_path}")

plt.close()
