import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
data = pd.read_csv("/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/data_from_cluster/birthyr_state_trends_college.csv")

# Define US regions
regions = {
    'Northeast': ['Connecticut', 'Maine', 'Massachusetts', 'New Hampshire', 'Rhode Island',
                  'Vermont', 'New Jersey', 'New York', 'Pennsylvania'],
    'Midwest': ['Illinois', 'Indiana', 'Michigan', 'Ohio', 'Wisconsin', 'Iowa', 'Kansas',
                'Minnesota', 'Missouri', 'Nebraska', 'North Dakota', 'South Dakota'],
    'South': ['Delaware', 'Florida', 'Georgia', 'Maryland', 'North Carolina', 'South Carolina',
              'Virginia', 'West Virginia', 'District of Columbia', 'Alabama', 'Kentucky',
              'Mississippi', 'Tennessee', 'Arkansas', 'Louisiana', 'Oklahoma', 'Texas'],
    'West': ['Arizona', 'Colorado', 'Idaho', 'Montana', 'Nevada', 'New Mexico', 'Utah',
             'Wyoming', 'California', 'Oregon', 'Washington']
}

# Create reverse mapping
state_to_region = {}
for region, states in regions.items():
    for state in states:
        state_to_region[state] = region

# Add region column
data['region'] = data['statefip'].map(state_to_region)

# Calculate college share by region and birth year
# Weighted by total_people
regional_data = data.groupby(['birthyr', 'region'], group_keys=False).apply(
    lambda x: pd.Series({'college_share': np.average(x['college'], weights=x['total_people'])})
).reset_index()

# Create figure
fig, ax = plt.subplots(figsize=(12, 7))

# Define consistent colors for regions
region_colors = {
    'Northeast': '#1f77b4',
    'Midwest': '#ff7f0e',
    'South': '#2ca02c',
    'West': '#d62728'
}

# Plot each region
for region in ['Northeast', 'Midwest', 'South', 'West']:
    region_subset = regional_data[regional_data['region'] == region]
    ax.plot(region_subset['birthyr'], region_subset['college_share'],
            label=region, color=region_colors[region], linewidth=2)

ax.set_xlabel('Birth Year', fontsize=12)
ax.set_ylabel('Share with College Degree', fontsize=12)
ax.set_title('College Attainment by US Region and Birth Year', fontsize=14)
ax.set_xlim(1870, None)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()

# Save figure
output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures/college_share_by_region.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Figure saved to: {output_path}")

plt.close()
