# Threat_Maps
World map visualizations based on data from EDR sensors or targeted hosts/users.

Reference: https://t3l3m3try.medium.com/geopolitical-intelligence-from-edr-sensor-location-data-33b29313d118 

## EDR_Sensors
Dedicated section to plot the EDR sensors data to a world map. Currently set for Crowdstrike and Defender.

### Usage:
```bash
python EDR_Plot_Script.py <sensors_csv_path> <coordinates_csv_path>
```

### Examples:

For Defender (Full country names):
```bash
python EDR_Plot_Script.py Defender_Sensors_Demo.csv Country_Coordinates.csv
```

For CrowdStrike (Alpha-2 codes):
```bash
python EDR_Plot_Script.py Crowdstrike_Sensors_Demo.csv Country_Coordinates.csv
```

### Country Codes
The country names, alpha-2 codes and relative coordinates can be downloaded here:
https://github.com/t3l3m3try/Threat_Maps/blob/main/EDR_Sensors/Country_Coordinates.csv 

Following you can find the ThreatMap output example:
<img width="1879" height="1072" alt="image" src="https://github.com/user-attachments/assets/02cfdf07-e61d-4f8a-931d-e0ddaf7b75a5" />
