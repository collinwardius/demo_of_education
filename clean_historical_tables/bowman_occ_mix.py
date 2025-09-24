import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Read the data
data_path = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/occupational_groups_data_bowman_1962.csv'
df = pd.read_csv(data_path)

# Extract male enrollment data for state and private universities
occupations = df['Occupational Groups']
state_men = df['State Universities Men']
private_men = df['Private Coeducational Colleges Men']

# Set up the bar chart
x = np.arange(len(occupations))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 8))

# Create bars
bars1 = ax.bar(x - width/2, state_men, width, label='State Universities', color='steelblue')
bars2 = ax.bar(x + width/2, private_men, width, label='Private Universities', color='orange')

# Customize the chart
ax.set_xlabel('', fontsize=12)
ax.set_ylabel('Male Enrollment Share (%)', fontsize=12)
ax.set_title('Male Enrollment Share by Parent Occupation\nState vs Private Universities (1923-1924)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(occupations, rotation=45, ha='right')
ax.legend()

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

# Adjust layout and save
plt.tight_layout()

# Create output directory if it doesn't exist
output_dir = '/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/output/figures'
os.makedirs(output_dir, exist_ok=True)

# Save the figure
output_path = os.path.join(output_dir, 'parent_occ_bowman_1962.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.show()

print(f"Chart saved to: {output_path}")