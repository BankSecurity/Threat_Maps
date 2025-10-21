import folium
import pandas as pd
import os
import sys
from folium.plugins import HeatMap
from datetime import datetime
import re

def main():
    # --- 1. Parse command line arguments ---
    if len(sys.argv) != 3:
        print("Usage: python EDR_Plot_Script.py <sensors_csv_path> <coordinates_csv_path>")
        print("Example: python EDR_Plot_Script.py Sensors_Demo.csv Country_Coordinates.csv")
        print("\nNote: The script automatically detects whether your sensors CSV uses:")
        print("  - Country full names (e.g., 'United States')")
        print("  - Country Alpha-2 codes (e.g., 'US')")
        sys.exit(1)
    
    sensors_csv_path = sys.argv[1]
    coords_csv_path = sys.argv[2]
    
    # --- 2. Read the Sensors data ---
    print(f"Reading Sensors data from: {sensors_csv_path}")
    try:
        sensors_df = pd.read_csv(sensors_csv_path)
    except Exception as e:
        print(f"Error reading sensors data: {e}")
        return
    
    print(f"Sensors data loaded: {len(sensors_df)} records")
    
    # --- 3. Read the Country Coordinates data ---
    print(f"\nReading Country Coordinates data from: {coords_csv_path}")
    
    # Read with pipe separator and handle inconsistent fields
    try:
        coords_df = pd.read_csv(coords_csv_path, sep='|', on_bad_lines='skip', engine='python')
    except Exception as e:
        print(f"Error reading coordinates: {e}")
        return
    
    print(f"Coordinates data loaded: {len(coords_df)} countries")
    
    # --- 4. Clean column names (remove extra spaces and quotes) ---
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
    
    # --- 5. Detect and normalize column names ---
    # Handle various count column names
    count_columns = ['"_count"', '_count', 'count_', 'count', 'Total']
    for col in count_columns:
        if col in sensors_df.columns:
            sensors_df = sensors_df.rename(columns={col: 'Total'})
            break
    
    # Handle country code column names (CrowdStrike format)
    if 'Agent IP.country' in sensors_df.columns:
        sensors_df = sensors_df.rename(columns={'Agent IP.country': 'country_identifier'})
    elif 'country' in sensors_df.columns:
        sensors_df = sensors_df.rename(columns={'country': 'country_identifier'})
    elif 'country_code' in sensors_df.columns:
        sensors_df = sensors_df.rename(columns={'country_code': 'country_identifier'})
    
    # Convert Total to numeric
    if 'Total' in sensors_df.columns:
        sensors_df['Total'] = pd.to_numeric(sensors_df['Total'], errors='coerce')
    else:
        print("Error: Could not find a count column in sensors data")
        return
    
    # --- 6. Detect if using country names or Alpha-2 codes ---
    print("\nDetecting country identifier type...")
    
    # Check if country_identifier exists
    if 'country_identifier' not in sensors_df.columns:
        print("Error: Could not find country column in sensors data")
        return
    
    # Sample a few values to determine the type
    sample_values = sensors_df['country_identifier'].dropna().head(10)
    
    # Check if values are 2-character codes (Alpha-2)
    is_alpha2 = all(len(str(val)) == 2 for val in sample_values if pd.notna(val))
    
    if is_alpha2:
        print("Detected: Alpha-2 country codes (e.g., 'US', 'GB')")
        merge_left = 'country_identifier'
        merge_right = 'Alpha-2 code'
    else:
        print("Detected: Full country names (e.g., 'United States', 'United Kingdom')")
        merge_left = 'country_identifier'
        merge_right = 'Country'
    
    # --- 7. Merge the two dataframes ---
    print("\nMerging datasets...")
    
    merged_df = pd.merge(
        sensors_df, 
        coords_df, 
        left_on=merge_left, 
        right_on=merge_right, 
        how='inner'
    )
    
    print(f"Merged data: {len(merged_df)} countries matched")
    
    # Find unmatched countries
    matched_countries = set(merged_df[merge_left].unique())
    all_sensor_countries = set(sensors_df['country_identifier'].unique())
    unmatched_countries = all_sensor_countries - matched_countries
    
    if unmatched_countries:
        print(f"\nCountries that didn't match ({len(unmatched_countries)}):")
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
    
    # --- 8. Create the map and add circles and markers ---
    print("\nCreating map...")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles='CartoDB positron')
    
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
    
    # --- 9. Save the Map to an HTML file ---
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_html_name = f"EDR_Sensors_Map_{timestamp}.html"
    
    # Save in the current directory
    output_dir = os.getcwd()
    output_path = os.path.join(output_dir, output_html_name)
    
    m.save(output_path)
    print(f"\n✓ Map successfully generated and saved to: {output_path}")
    print(f"✓ Total countries plotted: {len(merged_df)}")
    print(f"✓ Total count: {merged_df['Total'].sum()}")

if __name__ == "__main__":
    main()
