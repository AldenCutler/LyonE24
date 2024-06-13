import geopandas as gpd
import folium
from folium.plugins import HeatMap

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

# Add the heatmap to the map
HeatMap(heatmap_data).add_to(m)

# Save the map
m.save('out/lyon_stops_heatmap_with_arrondissements.html')
