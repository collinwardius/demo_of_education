import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Read the college data
df = pd.read_csv("/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/combined_college_blue_book_data.csv")

# Initialize geocoder
geolocator = Nominatim(user_agent="college_geocoder")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Function to geocode city-state pairs
def get_coordinates(city, state):
    try:
        location = geocode(f"{city}, {state}, USA")
        if location:
            return pd.Series({
                'latitude': location.latitude,
                'longitude': location.longitude,
                'geocode_address': location.address
            })
        else:
            return pd.Series({
                'latitude': None,
                'longitude': None,
                'geocode_address': None
            })
    except Exception as e:
        print(f"Error geocoding {city}, {state}: {e}")
        return pd.Series({
            'latitude': None,
            'longitude': None,
            'geocode_address': None
        })

# Get unique city-state pairs
unique_locations = df[['State', 'City']].drop_duplicates()

# Test with first 10 locations only
unique_locations = unique_locations.head(10)

print(f"Geocoding {len(unique_locations)} unique city-state pairs (TEST RUN)...")

# Geocode each unique location
geocoded = unique_locations.apply(
    lambda row: get_coordinates(row['City'], row['State']),
    axis=1
)

# Combine with original data
unique_locations = pd.concat([unique_locations, geocoded], axis=1)

# Merge back to original dataset
df_geocoded = df.merge(unique_locations, on=['State', 'City'], how='left')

# Save output
output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/colleges_with_coordinates.csv"
df_geocoded.to_csv(output_path, index=False)

# Save just the unique locations for reference
unique_output_path = "/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/data/college_data/unique_locations_geocoded.csv"
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
