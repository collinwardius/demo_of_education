import pandas as pd

# Read the data
df = pd.read_csv('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/combined_college_blue_book_data.csv')

# Drop observations missing city
df_cleaned = df.dropna(subset=['City']).copy()

# Dictionary of city name corrections (abbreviations to full names)
city_corrections = {
    'Berrien Spgs.': 'Berrien Springs',
    'Boiling Spgs.': 'Boiling Springs',
    'Brcliff Manor': 'Briarcliff Manor',
    'Cambridge Sp': 'Cambridge Springs',
    "Campbellsv'le": 'Campbellsville',
    'Cannon City': 'Canon City',
    'Chambersb\'g': 'Chambersburg',
    'Clemson Coll.': 'Clemson',
    'Colorado Spg.': 'Colorado Springs',
    'Corpus Christ.': 'Corpus Christi',
    'Crawfordsvl\'e': 'Crawfordsville',
    'E. Lansing': 'East Lansing',
    'E.Stroudsburg': 'East Stroudsburg',
    'Edinborго': 'Edinboro',
    'Elon Coll.': 'Elon',
    'Emory Univ.': 'Emory',
    'Forth Worth': 'Fort Worth',
    'Fredericksbg.': 'Fredericksburg',
    'Grand Junc.': 'Grand Junction',
    'Guilford Coll.': 'Guilford',
    'Hampden-Sdy.': 'Hampden-Sydney',
    'Holly Sprgs.': 'Holly Springs',
    'Lincoln Univ.': 'Lincoln University',
    'Lyndon Cent.': 'Lyndon Center',
    'Madison Coll.': 'Madison',
    'Milligan Coll.': 'Milligan',
    'Mission S.Jose': 'Mission San Jose',
    'Mt. Angel': 'Mount Angel',
    'Mt. Berry': 'Mount Berry',
    'Mt. Calvary': 'Mount Calvary',
    'Mt. Carroll': 'Mount Carroll',
    'Mt. Pleasant': 'Mount Pleasant',
    'Mt. Vernon': 'Mount Vernon',
    'Mt. Wash\'gt\'n': 'Mount Washington',
    'Mt.Vernon': 'Mount Vernon',
    'N. Little Rock': 'North Little Rock',
    'N. Manchester': 'North Manchester',
    'N. Sacramento': 'North Sacramento',
    'New Wilm\'gtn': 'New Wilmington',
    'North\'pton': 'Northampton',
    'Okla. City': 'Oklahoma City',
    'S. Bonaventure': 'Saint Bonaventure',
    'S. Euclid': 'South Euclid',
    'S. Lancaster': 'South Lancaster',
    'S. Luis Obispo': 'San Luis Obispo',
    'S.Bernardino': 'San Bernardino',
    'Saratoga Sprs.': 'Saratoga Springs',
    'Siloam Sprgs.': 'Siloam Springs',
    'Sioux Col.': 'Sioux Center',
    'St. Angelo': 'San Angelo',
    'St. Augustine': 'Saint Augustine',
    'St. Bernard': 'Saint Bernard',
    'St. Catherine': 'Saint Catherine',
    'St. Charles': 'Saint Charles',
    'St. Cloud': 'Saint Cloud',
    'St. George': 'Saint George',
    'St. Helena': 'Saint Helena',
    'St. Joseph': 'Saint Joseph',
    'St. Louis': 'Saint Louis',
    'St. Mary\'s': 'Saint Marys',
    'St. Mary\'s C.': 'Saint Marys',
    'St. Mary\'s Wds': 'Saint Marys Woods',
    'St. Nazianz': 'Saint Nazianz',
    'St. Paul': 'Saint Paul',
    'St. Peter': 'Saint Peter',
    'St. Petersburg': 'Saint Petersburg',
    'Stanford Univ.': 'Stanford',
    'W. Liberty': 'West Liberty',
    'W. Palm Beach': 'West Palm Beach',
    'W.Hartford': 'West Hartford',
    'W.Long Br\'ch': 'West Long Branch',
    'Webster Gr.': 'Webster Groves',
    'Wmsbg.': 'Williamsburg',
    'Yellow Spgs.': 'Yellow Springs'
}

# Apply corrections
df_cleaned['City'] = df_cleaned['City'].replace(city_corrections)

# Save cleaned data
df_cleaned.to_csv('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/combined_college_blue_book_data_cleaned.csv', index=False)

print(f"Original data: {len(df)} observations")
print(f"Cleaned data: {len(df_cleaned)} observations")
print(f"Dropped: {len(df) - len(df_cleaned)} observations")
print(f"\nCorrected {len(city_corrections)} abbreviated city names")
