import requests
import json
import geopandas as gpd
from shapely.geometry import shape
import folium
from tqdm import tqdm

# Bounding box for Lyon, France
bbox = (45.55706959, 4.6917603, 45.93918271, 5.06029048)

# Overpass API query for Lyon, France
overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = f"""
[out:json];
(
  way["building"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
);
out body;
>;
out skel qt;
"""

# Fetch data from Overpass API
response = requests.get(overpass_url, params={'data': overpass_query})
data = response.json()


# Create a Folium map centered on Lyon
map_center = [45.75, 4.85]  # Coordinates for Lyon

mymap = folium.Map(location=map_center, zoom_start=12)

# Parse the data to extract building geometries
elements = data['elements']
node_dict = {element['id']: (element['lat'], element['lon']) for element in data['elements'] if element['type'] == 'node'}

done = 0
tot = len(elements)

for element in data['elements']:
    
    done += 1
    
    if done % 1000 == 0:
        print(f"{round(done/tot, 3) * 100}% done..")
    
    if element['type'] == 'way' and 'nodes' in element:
        coords = [node_dict[node_id] for node_id in element['nodes']]
        center = folium.Polygon(locations=coords).get_bounds()
        building_center = [(center[0][0] + center[1][0]) / 2, (center[0][1] + center[1][1]) / 2]
        
        color = 'red'
        
        folium.Polygon(locations=coords, color=color, fill=True, fill_opacity=0.5).add_to(mymap)


# Save map to HTML file
mymap.save('out/lyon_buildings.html')

print("Map saved to lyon_buildings.html")
