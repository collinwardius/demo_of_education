import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import warnings
import logging
import os
import argparse

# Suppress geopy warnings and errors
warnings.filterwarnings('ignore')
logging.getLogger('geopy').setLevel(logging.CRITICAL)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Geocode college locations')
parser.add_argument('--overwrite', action='store_true',
                    help='Overwrite existing geocoded results (default: False, will only geocode new locations)')
args = parser.parse_args()

# Read the college data
df = pd.read_csv("/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/combined_college_blue_book_data_cleaned.csv")

# Initialize geocoder
geolocator = Nominatim(user_agent="college_geocoder")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, return_value_on_exception=None)

# Common abbreviation expansions
ABBREVIATIONS = {
    'Spgs.': 'Springs',
    'Sprgs.': 'Springs',
    'Spg.': 'Spring',
    'Mt.': 'Mount',
    'St.': 'Saint',
    'Ft.': 'Fort',
    'Junc.': 'Junction',
    'Coll.': 'College',
    'C.': 'City',
    'Br\'ch': 'Branch',
    'S.Jose': 'San Jose',
    'W.': 'West',
    'So.': 'South',
    'No.': 'North',
    'E.': 'East',
    '\'pton': 'hampton',
    'Twn': 'Town',
    '\'ville': 'ville',
    '\'gtn': 'ington',
    '\'sbg': 'sburg',
    '\'le': 'le',
    'Cent.': 'Center',
    '-Sdy.': '-Sydney',
    'Wds': 'Woods',
}

def expand_abbreviations(city):
    """Expand common abbreviations in city names"""
    if pd.isna(city):
        return None

    expanded = str(city)
    for abbr, full in ABBREVIATIONS.items():
        expanded = expanded.replace(abbr, full)
    return expanded

# Function to geocode city-state pairs
def get_coordinates(city, state, try_expansion=True):
    if pd.isna(city):
        return pd.Series({
            'latitude': None,
            'longitude': None,
            'geocode_address': None
        })

    try:
        # First try the original city name
        location = geocode(f"{city}, {state}, USA")
        if location:
            print(f"✓ {city}, {state}")
            return pd.Series({
                'latitude': location.latitude,
                'longitude': location.longitude,
                'geocode_address': location.address
            })

        # If failed and expansion enabled, try expanded version
        if try_expansion:
            expanded_city = expand_abbreviations(city)
            if expanded_city != city:
                print(f"  Trying expanded name: {expanded_city}")
                location = geocode(f"{expanded_city}, {state}, USA")
                if location:
                    print(f"✓ {expanded_city}, {state} (expanded from {city})")
                    return pd.Series({
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'geocode_address': location.address
                    })

        print(f"✗ {city}, {state} - Not found")
        return pd.Series({
            'latitude': None,
            'longitude': None,
            'geocode_address': None
        })
    except Exception as e:
        print(f"✗ {city}, {state} - Error")
        return pd.Series({
            'latitude': None,
            'longitude': None,
            'geocode_address': None
        })

# Get unique city-state pairs
unique_locations = df[['State', 'City']].drop_duplicates()

# Check if geocoded file already exists
unique_output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/unique_locations_geocoded.csv"
if os.path.exists(unique_output_path) and not args.overwrite:
    print("Loading existing geocoded data...")
    existing_geocoded = pd.read_csv(unique_output_path)

    # Merge existing data
    unique_locations = unique_locations.merge(
        existing_geocoded[['State', 'City', 'latitude', 'longitude', 'geocode_address']],
        on=['State', 'City'],
        how='left'
    )

    # Identify locations that need geocoding
    needs_geocoding = unique_locations[unique_locations['latitude'].isna()].copy()
    already_geocoded = unique_locations[unique_locations['latitude'].notna()].copy()

    print(f"Already geocoded: {len(already_geocoded)}")
    print(f"Need geocoding: {len(needs_geocoding)}")
else:
    if args.overwrite:
        print("Overwrite mode: Will geocode all locations (ignoring existing results)...")
    else:
        print("No existing geocoded data found, will geocode all locations...")
    needs_geocoding = unique_locations.copy()
    already_geocoded = pd.DataFrame()

# Geocode only the locations that need it
if len(needs_geocoding) > 0:
    print(f"\nGeocoding {len(needs_geocoding)} locations...")

    geocoded = needs_geocoding.apply(
        lambda row: get_coordinates(row['City'], row['State']),
        axis=1
    )

    # Combine with the state and city info
    needs_geocoding = pd.concat([needs_geocoding[['State', 'City']], geocoded], axis=1)

    # Combine with already geocoded locations
    unique_locations = pd.concat([already_geocoded, needs_geocoding], ignore_index=True)
else:
    print("\nAll locations already geocoded!")

# Merge back to original dataset
df_geocoded = df.merge(unique_locations, on=['State', 'City'], how='left')

# Save output
output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_coordinates.csv"
df_geocoded.to_csv(output_path, index=False)

# Save just the unique locations for reference
unique_locations.to_csv(unique_output_path, index=False)

print(f"\nGeocoding complete!")
print(f"Full dataset saved to: {output_path}")
print(f"Unique locations saved to: {unique_output_path}")
print(f"\nSuccessfully geocoded: {unique_locations['latitude'].notna().sum()} / {len(unique_locations)}")
print(f"Failed to geocode: {unique_locations['latitude'].isna().sum()}")

# Show failed geocodes
if unique_locations['latitude'].isna().any():
    print("\nFailed locations:")
    print(unique_locations[unique_locations['latitude'].isna()][['State', 'City']])
