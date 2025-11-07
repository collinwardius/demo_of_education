import pandas as pd
import matplotlib.pyplot as plt

# Load the Stata data file
data_path = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/data_from_cluster/treated_colleges_counties.dta'
df = pd.read_stata(data_path)

# Output directory for figures
output_dir = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures'

print("=" * 80)
print("DATASET OVERVIEW")
print("=" * 80)
print(f"\nDataset shape: {df.shape[0]} rows × {df.shape[1]} columns")

print("\n" + "=" * 80)
print("COLLEGE TYPE DISTRIBUTION")
print("=" * 80)
type_counts = df['college_type'].value_counts()
print(type_counts)

# Create bar graph by college type
fig, ax = plt.subplots(figsize=(10, 7))

# Combine Historically Black colleges with Regular colleges
df_grouped = df.copy()
df_grouped['college_type'] = df_grouped['college_type'].replace(
    'Colleges Especially for Negroes', 'Regular'
)

# Get counts and sort them
type_counts = df_grouped['college_type'].value_counts().sort_values(ascending=False)

# Rename labels for display
label_mapping = {
    'Regular': 'Conventional'
}
type_counts.index = type_counts.index.map(lambda x: label_mapping.get(x, x))

# Create bar plot with simple colors
colors = ['#1f77b4', '#ff7f0e']
bars = ax.bar(range(len(type_counts)), type_counts.values, color=colors, width=0.6)

# Customize the plot
ax.set_xticks(range(len(type_counts)))
ax.set_xticklabels(type_counts.index, rotation=0, ha='center')
ax.set_ylabel('Number of Colleges', fontsize=12)
ax.set_xlabel('College Type', fontsize=12)
ax.set_title('Distribution of Colleges by Type', fontsize=14)

# Add value labels on top of bars
for i, (bar, value) in enumerate(zip(bars, type_counts.values)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 3,
            f'{int(value)}',
            ha='center', va='bottom', fontsize=11)

# Add light grid
ax.grid(True, alpha=0.3)
ax.set_axisbelow(True)

# Set y-axis limits
ax.set_ylim(0, max(type_counts.values) * 1.15)

# Tight layout
plt.tight_layout()

# Save the figure
output_path = f'{output_dir}/colleges_by_type.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n✓ Figure saved to: {output_path}")

plt.close()

# Create CDF of college foundings
print("\n" + "=" * 80)
print("COLLEGE FOUNDING YEARS")
print("=" * 80)
print(f"Earliest founding: {df['year_founding'].min()}")
print(f"Latest founding: {df['year_founding'].max()}")
print(f"Median founding year: {df['year_founding'].median()}")

fig, ax = plt.subplots(figsize=(10, 7))

# Sort founding years and calculate cumulative distribution
founding_years_sorted = df['year_founding'].sort_values()
cumulative_count = range(1, len(founding_years_sorted) + 1)

# Plot CDF
ax.plot(founding_years_sorted, cumulative_count, linewidth=2, color='#1f77b4')

# Customize the plot
ax.set_xlabel('Year of Founding', fontsize=12)
ax.set_ylabel('Cumulative Number of Colleges', fontsize=12)
ax.set_title('Cumulative Distribution of College Foundings', fontsize=14)
ax.grid(True, alpha=0.3)
ax.set_axisbelow(True)

plt.tight_layout()

# Save the figure
output_path = f'{output_dir}/colleges_founding_cdf.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n✓ Figure saved to: {output_path}")

plt.close()
