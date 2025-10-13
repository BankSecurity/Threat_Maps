import folium
import pandas as pd
import os
from folium.plugins import HeatMap
from datetime import datetime
import re
import urllib.request

def download_csv(url):
    """Download CSV file from URL and return as pandas DataFrame"""
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
        from io import StringIO
        return pd.read_csv(StringIO(data))
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def main():
    # --- 1. Download and read the CrowdStrike Sensors data ---
    print("Downloading CrowdStrike Sensors data...")
    sensors_url = "https://raw.githubusercontent.com/BankSecurity/Threat_Maps/refs/heads/main/EDR_Sensors/Crowdstrike_Sensors_Demo.csv"
    sensors_df = download_csv(sensors_url)
    
    if sensors_df is None:
        print("Failed to download sensors data. Exiting.")
        return
    
    print(f"Sensors data loaded: {len(sensors_df)} countries")
    
    # --- 2. Download and read the Country Coordinates data ---
    print("\nDownloading Country Coordinates data...")
    coords_url = "https://raw.githubusercontent.com/BankSecurity/Threat_Maps/refs/heads/main/EDR_Sensors/Country_Coordinates.csv"
    
    # Read with pipe separator and handle inconsistent fields
    try:
        with urllib.request.urlopen(coords_url) as response:
            data = response.read().decode('utf-8')
        from io import StringIO
        coords_df = pd.read_csv(StringIO(data), sep='|', on_bad_lines='skip', engine='python')
    except Exception as e:
        print(f"Error downloading coordinates: {e}")
        return
    
    if coords_df is None:
        print("Failed to download coordinates data. Exiting.")
        return
    
    print(f"Coordinates data loaded: {len(coords_df)} countries")
    
    # --- 3. Clean column names (remove extra spaces and quotes) ---
    sensors_df.columns = sensors_df.columns.str.strip()
    coords_df.columns = coords_df.columns.str.strip().str.replace('"', '')
    
    # Clean data in coords_df (remove quotes from values)
    for col in coords_df.columns:
        if coords_df[col].dtype == 'object':
            coords_df[col] = coords_df[col].str.strip().str.replace('"', '')
    
    # Clean data in sensors_df (remove quotes from values)
    for col in sensors_df.columns:
        if sensors_df[col].dtype == 'object':
            sensors_df[col] = sensors_df[col].str.strip().str.replace('"', '')
    
    # Rename columns to match for merging
    if '"_count"' in sensors_df.columns:
        sensors_df = sensors_df.rename(columns={'"_count"': 'Total'})
    elif '_count' in sensors_df.columns:
        sensors_df = sensors_df.rename(columns={'_count': 'Total'})
    
    if 'Agent IP.country' in sensors_df.columns:
        sensors_df = sensors_df.rename(columns={'Agent IP.country': 'country_code'})
    
    # Convert Total to numeric
    sensors_df['Total'] = pd.to_numeric(sensors_df['Total'], errors='coerce')
    
    # --- 4. Merge the two dataframes on country code (Alpha-2 code) ---
    print("\nMerging datasets...")
    
    merged_df = pd.merge(
        sensors_df, 
        coords_df, 
        left_on='country_code', 
        right_on='Alpha-2 code', 
        how='inner'
    )
    
    print(f"Merged data: {len(merged_df)} countries matched")
    
    # Find unmatched countries
    matched_countries = set(merged_df['country_code'].unique())
    all_sensor_countries = set(sensors_df['country_code'].unique())
    unmatched_countries = all_sensor_countries - matched_countries
    
    if unmatched_countries:
        print(f"\nCountry codes that didn't match ({len(unmatched_countries)}):")
        for country in sorted(unmatched_countries):
            print(f"  - {country}")
    
    if len(merged_df) == 0:
        print("Warning: No countries matched between the two datasets!")
        return
    
    # Convert latitude and longitude to numeric
    merged_df['Latitude (average)'] = pd.to_numeric(merged_df['Latitude (average)'], errors='coerce')
    merged_df['Longitude (average)'] = pd.to_numeric(merged_df['Longitude (average)'], errors='coerce')
    
    # Remove rows with missing coordinates
    merged_df = merged_df.dropna(subset=['Latitude (average)', 'Longitude (average)'])
    
    print(f"Final dataset: {len(merged_df)} countries with valid coordinates")
    
    # --- 5. Create the map and add circles and markers ---
    print("\nCreating map...")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles='CartoDB dark_matter')
    
    # Get the maximum total value to scale the circle sizes
    max_total = merged_df['Total'].max()
    
    # Iterate through the merged data to add circles and conditional markers
    for _, row in merged_df.iterrows():
        # Calculate the radius of the circle based on the 'Total' value
        # A small multiplier is used to make the circles visible but not too large
        radius = (row['Total'] / max_total) * 30 if max_total > 0 else 5
        
        # Add a CircleMarker for each country
        folium.CircleMarker(
            location=[row['Latitude (average)'], row['Longitude (average)']],
            radius=radius,
            popup=f"Country: {row['Country']}<br>Count: {row['Total']}",
            color='orange',
            fill=True,
            fill_color='orange',
            fill_opacity=0.6
        ).add_to(m)
    
    # --- 6. Save the Map to an HTML file ---
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_html_name = f"Crowdstrike_EDR_Sensors_map_{timestamp}.html"
    
    # Save in the current directory
    output_dir = os.getcwd()
    output_path = os.path.join(output_dir, output_html_name)
    
    m.save(output_path)
    print(f"\n✓ Map successfully generated and saved to: {output_path}")
    print(f"✓ Total countries plotted: {len(merged_df)}")
    print(f"✓ Total count: {merged_df['Total'].sum()}")

if __name__ == "__main__":
    main()
