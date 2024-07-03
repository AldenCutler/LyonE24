import matplotlib.pyplot as plt
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np

# Load the JSON data
with open('./data/stops.json') as f:
    data = json.load(f)[0]['rows']


# Extract coordinates and names
stops = [
    {"name": stop[1], "lon": float(json.loads(stop[2])['lon']), "lat": float(json.loads(stop[2])['lat'])}
    for stop in data if len(json.loads(stop[3])) != 0
]

stops = {stop['name']: stop for stop in stops}.values()

# Create a DataFrame
df = pd.DataFrame(stops)

# Create a GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat))

# Plot the stops
fig, ax = plt.subplots(1, 1, figsize=(10, 10))
gdf.plot(ax=ax, color='black', alpha=1, markersize=30)

# Customizing the map
ax.set_axis_off()
fig.patch.set_facecolor('#e4dec0')  # Setting background color to match the poster

# Center of Lyon, France
lyon_center = Point(4.8357, 45.7640)  # Longitude, Latitude

# Radii in miles
radii = [1, 3, 5, 7, 9]

# Conversion from miles to degrees approximately (since 1 degree latitude ~ 69 miles)
miles_to_degrees = 1 / 69.0

for radius in radii:
    circle = plt.Circle(
        (lyon_center.x, lyon_center.y), 
        radius * miles_to_degrees, 
        color='grey', 
        fill=True, 
        linewidth=3,
        alpha=0.5
    )
    #ax.add_patch(circle)

# Save the map
output_path = './out/lyon_tcl_map_with_circles.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.1)
