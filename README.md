# Threat_Maps
World map visualizations based on data from EDR sensors and targeted host or user locations

## EDR_Sensors
Dedicated section to plot the EDR sensors data to a world map. Currently set for Crowdstrike and Defender.

### Usage:
```bash
python EDR_Plot_Script.py <sensors_csv_path> <coordinates_csv_path>
```

Examples:

### For Defender (Full country names):
```bash
python EDR_Plot_Script.py Defender_Sensors_Demo.csv Country_Coordinates.csv
```

### For CrowdStrike (Alpha-2 codes):
```bash
python EDR_Plot_Script.py Crowdstrike_Sensors_Demo.csv Country_Coordinates.csv
```
