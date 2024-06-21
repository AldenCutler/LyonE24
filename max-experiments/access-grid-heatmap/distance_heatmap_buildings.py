import geopandas as gpd
import folium
from folium.plugins import HeatMap
import os
import requests
import json
import numpy as np
import pandas as pd
import math
from scipy.spatial import KDTree

# Load GeoJSON data
arrondissements = gpd.read_file('data/arrondissements-lyon.geojson')
stops = gpd.read_file('data/stops.geojson')

# Ensure both GeoDataFrames have the same CRS
arrondissements = arrondissements.to_crs(stops.crs)

# Perform a spatial join to filter stops within arrondissements
stops_within_arrondissements = gpd.sjoin(stops, arrondissements, how='inner', op='within')

# Extract coordinates for the heatmap
heatmap_data = [[point.y, point.x] for point in stops_within_arrondissements.geometry]

# Define the bounding box for the Lyon Metropolis
minx, miny, maxx, maxy = arrondissements.total_bounds

# Overpass API query for Lyon, France
overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = f"""
[out:json];
(
  way["building"="residential"]({miny},{minx},{maxy},{maxx});
  way["building"="apartments"]({miny},{minx},{maxy},{maxx});
  way["building"="house"]({miny},{minx},{maxy},{maxx});
  way["building"="detached"]({miny},{minx},{maxy},{maxx});
  way["building"="terrace"]({miny},{minx},{maxy},{maxx});
  way["building"="semidetached_house"]({miny},{minx},{maxy},{maxx});
  way["building"="bungalow"]({miny},{minx},{maxy},{maxx});
  way["building"="static_caravan"]({miny},{minx},{maxy},{maxx});
);
out body;
>;
out skel qt;
"""

# Fetch data from Overpass API
response = requests.get(overpass_url, params={'data': overpass_query})
data = response.json()


buildings_coords = []

for element in data['elements']:
    if element['type'] == "node":
        buildings_coords.append([element['lat'], element['lon'], -1, ''])

# Convert buildings_coords to a GeoDataFrame
buildings_gdf = gpd.GeoDataFrame(
    buildings_coords,
    columns=['lat', 'lon', 'distance', 'nearest_station'],
    geometry=gpd.points_from_xy([coord[1] for coord in buildings_coords], [coord[0] for coord in buildings_coords]),
    crs=arrondissements.crs
)

# Perform a spatial join to filter buildings within arrondissements
buildings_within_arrondissements = gpd.sjoin(buildings_gdf, arrondissements, how='inner', op='within')

# Get list of station coords and names
station_coords = []
station_names = []
stops_json = json.loads(open('data/stops.geojson', 'r').read())

for stop in stops_json['features']:
    station_coords.append(stop['geometry']['coordinates'])
    station_names.append(stop['properties']['name'])

print(f"Got {len(buildings_coords)} buildings and {len(station_coords)} stops")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    meters = R * c  # output distance in meters
    return meters

def compute_closest_stations(buildings_coords, station_coords, station_names):
    # Convert station coordinates to a numpy array for KDTree
    station_coords_np = np.array(station_coords)
    
    # Create KDTree for station coordinates
    station_tree = KDTree(station_coords_np)
    i = 0
    for building in buildings_coords:
        i+=1
        if i % 50000 == 0:
            print(f"{round(i/len(buildings_coords)*100)}% of distances computed..")
        building_lat, building_lon = building[:2]
        distance, index = station_tree.query([building_lon, building_lat])
        closest_station = station_coords_np[index]
        distance = haversine(building_lat, building_lon, closest_station[1], closest_station[0])
        building[2] = distance
        building[3] = station_names[index]
    
    return buildings_coords

buildings_within_arrondissements = compute_closest_stations(
    buildings_within_arrondissements[['lat', 'lon', 'distance', 'nearest_station']].values.tolist(),
    station_coords,
    station_names
)

# Filter out the lowest 60% of distance points
distances = [building[2] for building in buildings_within_arrondissements]
threshold = np.percentile(distances, 80)
filtered_buildings_coords = [building for building in buildings_within_arrondissements if building[2] > threshold]

# Create the base map centered on Lyon
m = folium.Map(location=[(miny + maxy) / 2, (minx + maxx) / 2], zoom_start=13)

# Add the regions to the map with the style column
arrondissements['style'] = [{
    "fillColor": 'black',  # color for the region
    "color": "black",
    "weight": 2,
    "fillOpacity": 0  # opacity for the region
} for _ in range(len(arrondissements))]

folium.GeoJson(
    arrondissements,
    name='geojson',
    style_function=lambda x: x['properties']['style'],
    tooltip=folium.GeoJsonTooltip(fields=[], aliases=[])
).add_to(m)

# Add the filtered heatmap to the map
HeatMap([[building[0], building[1], building[2]] for building in filtered_buildings_coords]).add_to(m)

# stops_within_arrondissements = gpd.sjoin(stops, arrondissements, how='inner', op='within')
# folium.GeoJson(
#     stops_within_arrondissements,
#     name='geojson',
# ).add_to(m)

# Save the map
m.save('out/lyon_stops_distance_heatmap_no_markers.html')





do_csv = False

if do_csv:
    # Create the CSV file
    building_data = []
    i = 0
    for building in buildings_within_arrondissements:
        i+=1
        if i % 5000 == 0:
            print(f"{round(i/len(buildings_within_arrondissements)*100)}% of building infos written for CSV..")
        lat, lon, distance, nearest_station = building
        point = gpd.points_from_xy([lon], [lat], crs=arrondissements.crs)[0]
        arrondissement = arrondissements[arrondissements.contains(point)].iloc[0]['nom']
        building_data.append([lat, lon, distance, nearest_station, arrondissement])

    # Convert to DataFrame
    df = pd.DataFrame(building_data, columns=['lat', 'lon', 'distance', 'nearest_station', 'arrondissement'])

    # Save to CSV
    df.to_csv('out/building_distances.csv', index=False)
