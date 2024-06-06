import requests
import folium

# Step 1: Query Overpass API to get the district boundaries and roads
overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = """
[out:json];
area["name"="Lyon Métropole"]->.searchArea;
(
  way["highway"](area.searchArea);
);
out body;
>;
out skel qt;
"""
response = requests.get(overpass_url, params={'data': overpass_query})
data = response.json()

# Step 2: Parse the GeoJSON data
# Extracting nodes and ways from the response
elements = data['elements']

nodes = {element['id']: (element['lat'], element['lon']) for element in elements if element['type'] == 'node'}
ways = [element for element in elements if element['type'] == 'way']

# Create a map centered around Lyon
m = folium.Map(location=[45.75, 4.85], zoom_start=12)

# Step 3: Add roads as polylines to the folium map
for way in ways:
    if 'tags' in way and 'highway' in way['tags']:
        coordinates = [(nodes[node_id][0], nodes[node_id][1]) for node_id in way['nodes']]
        folium.PolyLine(coordinates, color='blue', weight=2.5, opacity=0.8).add_to(m)

# Display the map
m.save('lyon_roads.html')
print("Map saved as 'lyon_roads.html'. Open this file in your browser to view the map.")
