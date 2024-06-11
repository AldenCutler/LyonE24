import requests
import folium
from geopy.distance import geodesic
from folium.plugins import MarkerCluster

# Step 1: Query Overpass API to get the buildings within the specified bounding box
overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = """
[out:json];
(
  way["building"](45.7442,4.8511,45.7641,4.8374);
);
out body;
>;
out skel qt;
"""
response = requests.get(overpass_url, params={'data': overpass_query})
data = response.json()

# Step 2: Query Overpass API to get the train stations within the specified bounding box
train_station_query = """
[out:json];
node["railway"="station"](45.7155,4.7951,45.8092,4.92);
out body;
"""
response_stations = requests.get(overpass_url, params={'data': train_station_query})
stations_data = response_stations.json()

# Step 3: Extract train station coordinates
train_stations = [(element['lat'], element['lon']) for element in stations_data['elements'] if element['type'] == 'node']

# Step 4: Create a Folium map centered on Lyon
map_center = [45.75, 4.85]  # Coordinates for Lyon
mymap = folium.Map(location=map_center, zoom_start=12)

# Step 5: Prepare a dictionary for quick node lookup
node_dict = {element['id']: (element['lat'], element['lon']) for element in data['elements'] if element['type'] == 'node'}

# Step 6: Function to find the closest distance to a train station
def closest_station_distance(coords):
    return min(geodesic(coords, station).meters for station in train_stations)

totbuildings = len(data['elements'])
donebuildings = 0
# Step 7: Extract building coordinates, compute distances, and overlay them on the map
for element in data['elements']:
    donebuildings += 1
    
    if donebuildings % 100 == 0:
        perc = round(donebuildings/totbuildings*100, 2)
        print(f"{perc}% of buildings computed..")
    if element['type'] == 'way' and 'nodes' in element:
        coords = [node_dict[node_id] for node_id in element['nodes']]
        center = folium.Polygon(locations=coords).get_bounds()
        building_center = [(center[0][0] + center[1][0]) / 2, (center[0][1] + center[1][1]) / 2]
        distance = closest_station_distance(building_center)
        
        if distance < 500:
            color = 'green'
        elif distance < 1000:
            color = 'orange'
        else:
            color = 'red'
        
        folium.Polygon(locations=coords, color=color, fill=True, fill_opacity=0.5).add_to(mymap)

# Step 8: Add train stations to the map
marker_cluster = MarkerCluster().add_to(mymap)
for station in train_stations:
    folium.Marker(location=station, icon=folium.Icon(color='blue', icon='train')).add_to(marker_cluster)

# Step 9: Save the map to an HTML file and display it
mymap.save("lyon_buildings_map.html")
mymap
