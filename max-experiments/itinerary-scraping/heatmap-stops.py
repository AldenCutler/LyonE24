import osmnx as ox
import folium
from folium.plugins import HeatMap
import numpy as np
import pandas as pd
from shapely.geometry import Point, LineString
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('journeys.db')

# Load the 'stops' table
stops_df = pd.read_sql_query("SELECT * FROM stops", conn)

# Extract coordinates from the 'coord' column and convert to numeric values
stops_df['lon'] = stops_df['coord'].apply(lambda x: float(eval(x)['lon']))
stops_df['lat'] = stops_df['coord'].apply(lambda x: float(eval(x)['lat']))

# Keep only relevant columns
stops_df = stops_df[['id', 'name', 'lat', 'lon']]

# Define the location (Lyon, France)
place_name = "Lyon, France"

# Retrieve all the streets in Lyon
G = ox.graph_from_place(place_name, network_type='all')

# Convert the graph to a GeoDataFrame of edges
edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

# Calculate the distance from each street segment to the nearest stop
def distance_to_nearest_stop(geometry, stops):
    line = LineString(geometry)
    min_distance = np.inf
    for _, stop in stops.iterrows():
        point = Point(stop['lon'], stop['lat'])
        distance = line.distance(point)
        if distance < min_distance:
            min_distance = distance
    return min_distance

edges['distance_to_nearest_stop'] = edges['geometry'].apply(distance_to_nearest_stop, stops=stops_df)

# Normalize the distance for heatmap color coding
edges['distance_normalized'] = (edges['distance_to_nearest_stop'] - edges['distance_to_nearest_stop'].min()) / (
            edges['distance_to_nearest_stop'].max() - edges['distance_to_nearest_stop'].min())

# Create a Folium map
m = folium.Map(location=[45.75, 4.85], zoom_start=13)

# Define color scale
def get_color(distance):
    return f"#{int(255 * (1 - distance)):02x}{int(255 * distance):02x}00"

# Add streets to the map with color coding
for _, row in edges.iterrows():
    color = get_color(row['distance_normalized'])
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x, color=color: {'color': color, 'weight': 2}
    ).add_to(m)

# Save map to an HTML file
m.save('lyon_streets_heatmap.html')
